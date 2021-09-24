EXTENDDYNATRACE_REPO="https://github.com/nikhilgoenkatech/extendDynatrace.git"
EXTENDDYNATRACE_DIR="~/extendDynatrace"
    
install_telegraf() {
  if [ "$telegraf" = true ]; then
    printInfoSection "Installing Telegraf pre-requisites"
    printInfo "Download telegraf ..."
    bashas "wget https://dl.influxdata.com/telegraf/releases/telegraf_1.18.3-1_amd64.deb"
    bashas "dpkg -i telegraf_1.18.3-1_amd64.deb"
    printInfo "Install snmp deamon ..."
    bashas "apt install snmpd -y"
    printInfo "Install snmp agent ..."
    bashas "apt install snmp -y"
    printfInfo "Install MIBS Downloader ..."
    bashas "apt install snmp-mibs-downloader"
    printInfo "Installing SNMP Agent ..."
    bashas "python /home/ubuntu/extendDynatrace/telegraf/setup.py.in install"
    printInfo "Copy the MIB files ..."
    bashas "cp /home/ubuntu/extendDynatrace/examples/SIMPLE-MIB.txt /usr/share/snmp/mibs/"
    printInfo "Restart the SNMP Deamon ..."
    bashas "service snmpd restart"
  fi
}

setBashas() {
  # Wrapper for runnig commands for the real owner and not as root
  alias bashas="sudo -H -u ${USER} bash -c"
  # Expand aliases for non-interactive shell
  shopt -s expand_aliases
} 
timestamp() {
  date +"[%Y-%m-%d %H:%M:%S]"
} 
printInfo() {
  echo "[install-prerequisites|INFO] $(timestamp) |>->-> $1 <-<-<|"
}

printInfoSection() {
  echo "[install-prerequisites|INFO] $(timestamp) |$thickline"
  echo "[install-prerequisites|INFO] $(timestamp) |$halfline $1 $halfline"
  echo "[install-prerequisites|INFO] $(timestamp) |$thinline"
}

printError() {
  echo "[install-prerequisites|ERROR] $(timestamp) |x-x-> $1 <-x-x|"
}

# ======================================================================
#          ----- Installation Functions -------                        #
# The functions for installing the different modules and capabilities. #
# Some functions depend on each other, for understanding the order of  #
# execution see the function doInstallation() defined at the bottom    #
# ======================================================================
updateUbuntu() {
  if [ "$update_ubuntu" = true ]; then
    printInfoSection "Updating Ubuntu apt registry"
    apt update
  fi
}

setupProAliases() {
  if [ "$setup_proaliases" = true ]; then
    printInfoSection "Adding Bash and Kubectl Pro CLI aliases to .bash_aliases for user ubuntu and root "
    echo "
      # Alias for ease of use of the CLI
      alias las='ls -las'
      alias hg='history | grep'
      alias h='history'
      alias vaml='vi -c \"set syntax:yaml\" -'
      alias vson='vi -c \"set syntax:json\" -'
      alias pg='ps -aux | grep' " >/root/.bash_aliases
    homedir=$(eval echo ~$USER)
    cp /root/.bash_aliases $homedir/.bash_aliases
  fi
}

resources_clone(){
  if [ "$clone_the_repo" = true ]; then
    printInfoSection "Clone RUMD1Workshop Resources in $EXTENDDYNATRACE_DIR"
    bashas "sudo git clone $EXTENDDYNATRACE_REPO $EXTENDDYNATRACE_DIR"

  fi
}
createWorkshopUser() {
  if [ "$create_workshop_user" = true ]; then
    printInfoSection "Creating Workshop User from user($USER) into($NEWUSER)"
    homedirectory=$(eval echo ~$USER)
    printInfo "copy home directories and configurations"
    cp -R $homedirectory /home/$NEWUSER
    printInfo "Create user"
    useradd -s /bin/bash -d /home/$NEWUSER -m -G sudo -p $(openssl passwd -1 $NEWPWD) $NEWUSER
    printInfo "Change diretores rights -r"
    chown -R $NEWUSER:$NEWUSER /home/$NEWUSER
    usermod -a -G docker $NEWUSER
    usermod -a -G microk8s $NEWUSER
    printInfo "Warning: allowing SSH passwordAuthentication into the sshd_config"
    sed -i 's/PasswordAuthentication no/PasswordAuthentication yes/g' /etc/ssh/sshd_config
    service sshd restart
  fi
}
# ======================================================================
#       -------- Function boolean flags ----------                     #
#  Each function flag representas a function and will be evaluated     #
#  before execution.                                                   #
# ======================================================================
# If you add varibles here, dont forget the function definition and the priting in printFlags function.
verbose_mode=false
update_ubuntu=false
clone_the_repo=false
setup_proaliases=false
create_workshop_user=false
telegraf=false

extendDynatrace() {
  update_ubuntu=true
  setup_proaliases=true
  clone_the_repo=true

  create_workshop_user=true
  telegraf=true
}


# ======================================================================
#            ---- The Installation function -----                      #
#  The order of the subfunctions are defined in a sequencial order     #
#  since ones depend on another.                                       #
# ======================================================================
installSetup() {
  echo ""
  printInfoSection "Installing ... "
  echo ""

  echo ""
  setBashas

  updateUbuntu
  setupProAliases
  createWorkshopUser

  resources_clone
  install_telegraf
