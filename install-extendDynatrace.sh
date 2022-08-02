#!/bin/bash
# =========================================================
# Script for installing workshop in an Ubuntu Server LTS  #
# (20 or 18). You can install the following packages with #
# script - Docker, Docker Registry, Docker-compose
#                                                         #
# 'install-prerequisites.sh' is where the functions are   #
# defined and will be loaded into this shell.             #
# You can keep adding functionalities depending on your   #
# and contol with feature-flags(boolean variables).       #
#                                                         #
# An installationBundle contains a set of multiple ins-   #
# tallation functions.                                    #
# =========================================================
                        
LOGFILE='/tmp/install.log'      
touch $LOGFILE                  
chmod 775 $LOGFILE                      
pipe_log=true                           
                                
# - The installation will look for this file locally, if not found it will pull it form github.
BACKEND_FILE='install-extendDynatrace-prerequisites.sh'
                
USER="ubuntu"           
# ---- Workshop User  ----      
# The flag 'create_workshop_user'=true is per default set to false. If it's set to to it'll clone the home directory from USER and allow SSH login with the given text password )
NEWUSER="dynatrace"                     
NEWPWD="dynatrace"
        
FUNCTIONS_FILE_REPO="https://raw.githubusercontent.com/nikhilgoenkatech/extendDynatrace/master/install-extendDynatrace-prerequisites.sh"
                
if [ "$pipe_log" = true ] ; then
  echo "Piping all output to logfile $LOGFILE"  
  echo "Type 'less +F $LOGFILE' for viewing the output of installation on realtime"
  echo ""               
  # Saves file descriptors so they can be restored to whatever they were before redirection or used
  # themselves to output to whatever they were before the following redirect.
  exec 3>&1 4>&2        
  # Restore file descriptors for particular signals. Not generally necessary since they should be restored when the sub-shell exits.
  trap 'exec 2>&4 1>&3' 0 1 2 3
  # Redirect stdout to file log.out then redirect stderr to stdout. Note that the order is important when you
  # want them going to the same file. stdout must be redirected before stderr is redirected to stdout.
  exec 1>$LOGFILE 2>&1          
else                                    
  echo "Not piping stdout stderr to the logfile, writing the installation to the console"
fi                              
                        
# Load functions after defining the variables & versions
if [ -f "$BACKEND_FILE" ]; then
    echo "The functions file $BACKEND_FILE exists locally, loading functions from it. (dev)"
else
    echo "The functions file $BACKEND_FILE does not exist, getting it from github."
    curl -o install-extendDynatrace-prerequisites.sh $FUNCTIONS_FILE_REPO
fi

# Comfortable function for setting the sudo user.
if [ -n "${SUDO_USER}" ] ; then
  USER=$SUDO_USER
fi
echo "running sudo commands as $USER"

# Wrapper for runnig commands for the real owner and not as root
alias bashas="sudo -H -u ${USER} bash -c"
# Expand aliases for non-interactive shell
shopt -s expand_aliases

# --- Loading the functions in the current shell
source $BACKEND_FILE

# ==================================================
#    ----- Select your installation Bundle -----   #
# ==================================================
# Uncomment for installing Bank-Workshop
installExtendDynatrace
# ==================================================
#  ----- Call the Installation Function -----      #
# ==================================================
installSetup
