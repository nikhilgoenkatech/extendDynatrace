#!/usr/bin/env python
# encoding: utf-8
#
# python-netsnmpagent module
# Copyright (c) 2013-2019 Pieter Hollants <pieter@hollants.com>
# Licensed under the GNU Lesser Public License (LGPL) version 3
#
# Integration tests for the netsnmptestenv helper module
#

import sys, os, time, subprocess, re
from nose.tools import *
sys.path.insert(1, "..")
from netsnmptestenv import netsnmpTestEnv

@timed(3)
@raises(netsnmpTestEnv.SNMPTimeoutError)
def test_FirstGetFails():
	""" No test environment yet, snmpget fails """

	netsnmpTestEnv.snmpget("SNMPv2-MIB::snmpSetSerialNo.0")

@timed(1)
def test_Instantiation():
	""" Instantiation without exceptions and within reasonable time """

	global testenv, pid, tmpdir

	# Try creating the instance without raising exceptions
	testenv = netsnmpTestEnv()

	# Wait for snmpd to have started
	while not os.path.exists(testenv.pidfile):
		time.sleep(.1)

	# Remember the PID file and the tmpdir the instance uses
	with open(testenv.pidfile, "r") as f:
		pid = int(f.read())
	tmpdir = testenv.tmpdir

@timed(1)
def test_SecondGetWorks():
	""" test environment set up, snmpget succeeds """

	global testenv

	(data, datatype) = testenv.snmpget("SNMPv2-MIB::snmpSetSerialNo.0")
	eq_(datatype, "INTEGER")

@timed(1)
@raises(netsnmpTestEnv.UnknownOIDError)
def test_GetUnknownMIBThrowsException():
	""" snmpget of unknown MIB raises exception """

	global testenv

	testenv.snmpget("FOO-MIB::fooBarBaz.0")

@timed(1)
@raises(netsnmpTestEnv.UnknownOIDError)
def test_GetUnknownOIDThrowsException():
	""" snmpget of unknown OID raises exception """

	global testenv

	testenv.snmpget("SNMPv2-MIB::fooBarBaz.0")

@timed(1)
@raises(netsnmpTestEnv.MIBUnavailableError)
def test_GetAbsentMIBThrowsException():
	""" snmpget of absent MIB raises exception """

	global testenv

	testenv.snmpget("TEST-MIB::testUnsigned32NoInitval.0")

@timed(1)
def test_Shutdown():
	""" Shutdown without exceptions and within reasonable time """

	global testenv

	testenv.shutdown()

@timed(3)
@raises(netsnmpTestEnv.SNMPTimeoutError)
def test_ThirdGetFailsAgain():
	""" No more test environment, snmpget fails """

	netsnmpTestEnv.snmpget("SNMPv2-MIB::snmpSetSerialNo.0")

@raises(OSError)
def test_SnmpdNotRunning():
	""" snmpd not running anymore """

	global pid

	os.kill(pid, 0)

def test_TmpdirRemoved():
	""" tmpdir was removed """

	global tmpdir

	# List the tempdir's name and its contents if the assert fails
	print(tmpdir)
	try:
		print(os.listdir(tmpdir))
	except OSError:
		pass
	ok_(os.path.exists(tmpdir) == False)
