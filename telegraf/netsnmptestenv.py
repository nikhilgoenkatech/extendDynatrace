#!/usr/bin/env python
# encoding: utf-8
#
# python-netsnmpagent module
# Copyright (c) 2013-2019 Pieter Hollants <pieter@hollants.com>
# Licensed under the GNU Lesser Public License (LGPL) version 3
#
# net-snmp test environment module
#

""" Sets up net-snmp test environments.

This module allows to run net-snmp instances with user privileges that do not
interfere with any system-wide running net-snmp instance. """

import sys, os, atexit, tempfile, subprocess, locale, re, inspect, signal, time, shutil

class netsnmpTestEnv(object):
	""" Implements a net-snmp test environment. """

	def __init__(self, **args):
		""" Initializes a new net-snmp test environment. """

		# Currently hardcoded. Doesn't really allow parallel runs :/
		self.agentport  = 6555
		self.informport = 6556
		self.smuxport   = 6557

		# Ensure we get a chance to clean up after ourselves
		atexit.register(self.shutdown)

		# Create a temporary directory to hold the snmpd files
		self.tmpdir = tempfile.mkdtemp("netsnmptestenv")

		# Compose paths to files inside the temp dir
		conffile          = os.path.join(self.tmpdir, "snmpd.conf")
		self.mastersocket = os.path.join(self.tmpdir, "snmpd-agentx.sock")
		self.statedir     = os.path.join(self.tmpdir, "state")
		self.pidfile      = os.path.join(self.tmpdir, "snmpd.pid")
		indexesfile       = os.path.join(self.tmpdir, "mib_indexes")

		# Create a minimal snmpd configuration file
		with open(conffile, "w") as f:
			f.write("[snmpd]\n")
			f.write("rocommunity public 127.0.0.1\n")
			f.write("rwcommunity simple 127.0.0.1\n")
			f.write("agentaddress localhost:{0}\n".format(self.agentport))
			f.write("informsink localhost:{0}\n".format(self.informport))
			f.write("smuxsocket localhost:{0}\n".format(self.smuxport))
			f.write("master agentx\n")
			f.write("agentXSocket {0}\n\n".format(self.mastersocket))
			f.write("[snmp]\n")
			f.write("persistentDir {0}\n".format(self.statedir))

		# Create an empty mib_indexes file
		open(indexesfile, "w").close()

		# Start the snmpd instance
		cmd = "/usr/sbin/snmpd -r -LE warning -C -c{0} -p{1}".format(
			conffile, self.pidfile
		)
		subprocess.check_call(cmd, shell=True)

	def shutdown(self):
		def kill_process(pid):
			def is_running(pid):
				return os.path.exists("/proc/{0}".format(pid))

			if not is_running(pid):
				return

			starttime = time.clock()
			os.kill(pid, signal.SIGTERM)
			while time.clock() == starttime:
				time.sleep(0.25)

			if not is_running(pid):
				return

			os.kill(pid, signal.SIGTERM)
			while is_running(pid):
				time.sleep(0.25)

		# Check for existance of snmpd's PID file
		if hasattr(self, "pidfile") and os.access(self.pidfile, os.R_OK):
			# Read the PID
			with open(self.pidfile, "r") as f:
				pid = int(f.read())

			# And kill it
			kill_process(pid)

		# Recursively remove the temporary directory
		if hasattr(self, "tmpdir") and os.access(self.tmpdir, os.R_OK):
			shutil.rmtree(self.tmpdir)

	class SNMPTimeoutError(Exception):
		pass

	class UnknownOIDError(Exception):
		pass

	class MIBUnavailableError(Exception):
		pass

	class NotWritableError(Exception):
		pass

	@staticmethod
	def snmpcmd(op, oid, data=None, datatype=None):
		""" Executes a SNMP client operation in the net-snmp test environment.

		    "op" is either "get", "set", "walk" or "table".
		    "oid" is the OID to run the operation against.
		    "data" is the data to set in case of a "set" operation.
			"datatype" is the type of the data (as specified to "snmpset"). """

		# Compose the SNMP client command
		if op == "set":
			cmd = "/usr/bin/snmp{0} -M+. -r0 -v 2c -c simple localhost:6555 {1} {2} {3}"
			cmd = cmd.format(op, oid, datatype, data)
		else:
			cmd = "/usr/bin/snmp{0} -M+. -r0 -v 2c -c public localhost:6555 {1}"
			cmd = cmd.format(op, oid)

		# Python 2.6 (used eg. in SLES11SP2) does not yet know about
		# subprocess.check_output(), so we wrap subprocess.Popen() instead.
		#
		# Execute the command with stderr redirected to stdout and stdout
		# redirected to a pipe that we capture below
		proc = subprocess.Popen(
			cmd, shell=True, env={ "LANG": "C" },
			stdout=subprocess.PIPE, stderr=subprocess.STDOUT
		)
		output = proc.communicate()[0].strip()

		# Python 3's "str" strings are Unicode strings, not byte strings
		if not isinstance("Test", bytes):
			output = output.decode(locale.getpreferredencoding())

		rc = proc.poll()
		if rc == 0:
			if re.search(" = No Such Object available on this agent at this OID", output):
				raise netsnmpTestEnv.MIBUnavailableError(oid)
			if re.search("= No Such Instance currently exists at this OID", output):
				raise netsnmpTestEnv.UnknownOIDError(oid)
			return output

		if re.search(": Unknown Object Identifier", output):
				raise netsnmpTestEnv.UnknownOIDError(oid)

		if re.search("Timeout: No Response from ", output):
			raise netsnmpTestEnv.SNMPTimeoutError("localhost:6555")

		if re.search("Reason: notWritable \(That object does not support modification\)", output):
			raise netsnmpTestEnv.NotWritableError(oid)

		# SLES11 SP2's Python 2.6 has a subprocess module whose
		# CalledProcessError exception does not yet know the third "output"
		# argument, so we monkey-patch support into it
		if len(inspect.getargspec(subprocess.CalledProcessError.__init__).args) == 3:
			def new_init(self, returncode, cmd, output=None):
				self.returncode = returncode
				self.cmd        = cmd
				self.output     = output
			subprocess.CalledProcessError.__init__ = new_init

		raise subprocess.CalledProcessError(rc, cmd, output)

	@classmethod
	def snmpget(self, oid):
		""" Executes a "snmpget" operation in the net-snmp test environment.

		    "oid" is the OID to run the operation against.

		    Returns a two-tuple (data, datatype). """

		data = self.snmpcmd("get", oid).split("=")[1]
		if ":" in data:
			(datatype, data) = data.rsplit(": ", 1) if ": " in data else (data.rstrip(":"),"")
			datatype = datatype.strip()
		else:
			datatype = "STRING"
		data = data.strip()
		if data.startswith('"') and data.endswith('"'):
			data = data[1:-1]
		return (data, datatype)

	@classmethod
	def snmpset(self, oid, data, datatype):
		""" Executes a "snmpset" operation in the net-snmp test environment.

		    "oid" is the OID to run the operation against.
		    "data" is the data to set.
		    "datatype" is the type of the data (as specified to "snmpset"). """

		return self.snmpcmd("set", oid, data, datatype)

	@classmethod
	def snmpwalk(self, oid):
		""" Executes a "snmpwalk" operation in the net-snmp test environment.

		    "oid" is the OID to run the operation against. """

		return self.snmpcmd("walk", oid)

	@classmethod
	def snmptable(self, oid):
		""" Executes a "snmpwalk" operation in the net-snmp test environment.

		    "oid" is the OID to run the operation against. """

		return self.snmpcmd("table", oid)
