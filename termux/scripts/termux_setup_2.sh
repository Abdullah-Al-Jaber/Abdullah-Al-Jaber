#!/data/data/com.termux/files/usr/bin/bash

### VARIABLE ###
PWD=$(pwd)
COUNTDOWN=5
LOG_PATH=./log
PACKAGES_1="fish starship proot-distro wget curl"
PACKAGES_2=""

# Styles 
BOLD="\e[1m"
UNDERLINE="\e[4m"

RED="\e[31m"
GREEN="\e[32m"
YELLOW="\e[33m"
BLUE="\e[34m"

SPECIAL_COLOR="\e[34m\e[47m"

TITLE="$SPECIAL_COLOR$BOLD"
RESET="\e[0m"

echo -e "$TITLE\n# Termux Setup Script #\n$RESET"

if [ -d "$LOG_PATH" ]; then rm -rf $LOG_PATH; fi
mkdir $LOG_PATH

## FUNCTIONS
function silent_log() {
  eval "yes | $1" &>> "$LOG_PATH/$2.log"
}

function update_pkg() {
  silent_log "apt update" "apt"
  silent_log "pkg upgrade" "apt"
}

function wait_before_execute () {
  count=$COUNTDOWN
  
  echo 
  while [ $count -gt -1 ]; do
    # read -t 1 -p "[ $YELLOW$BOLD$count$RESET ] $2"
    echo -ne "[ $YELLOW$BOLD$count$RESET ] $2"
    read -r -t 1
    
    if [ $? -eq 0 ]; then
      echo -ne "${YELLOW}[ Skipped execution ]${RESET}"
      echo 
      return
    fi
    count=$((count-1))
    echo -ne "\r"
  done
  echo
  
  eval "$1"
}

function setup_fish() {
  chsh -s fish
fish -c 'echo "starship init fish | source" >> ./.config/fish/config.fish'

fish -c "set -U fish_greeting "
}

function setup_bin() {
if [ -d "./usr-bin" ]; then rm -rf ./usr-bin; fi

mkdir ./usr-bin
fish -c "fish_add_path ./usr-bin"
export PATH=$PATH:~/usr-bin
}


function setup_other() {
proot-distro remove debian
proot-distro install debian
rm ./usr-bin/debian
ln -s /storage/emulated/0 ./android
touch ./usr-bin/debian
echo 'proot-distro login --bind ~/android:/root/android debian -- "$@" ' >> ./usr-bin/debian
chmod +x ./usr-bin/debian
rm ../usr/etc/motd
}

function setup_debian() {

debian sed -i 's/^/#/' /etc/apt/sources.list
debian bash -c 'echo deb [signed-by="/usr/share/keyrings/debian-archive-keyring.gpg"] http://deb.debian.org/debian testing main contrib non-free >> /etc/apt/sources.list'
debian apt clean
debian apt update
debian bash -c "yes | apt upgrade"
debian bash -c "yes | apt install fish"
debian bash -c "yes | apt autoremove"
debian fish -c 'set -U fish_greeting -e "\nWelcome to Debian (testing)\n"'
debian chsh -s /usr/bin/fish
debian bash -c "yes | apt install $PACKAGES_2"
}

## MAIN CODE
cd ~ || exit
wait_before_execute 'update_pkg' 'Update &  Upgrade Packages'
wait_before_execute 'silent_log "pkg install $PACKAGES_1" "apt"' 'Installing Packages'

wait_before_execute 'silent_log "setup_fish" "misc"' 'Setting Fish Shell'
wait_before_execute 'silent_log "setup_bin" "misc"' 'Setting Up User Bin Folder'

wait_before_execute 'silent_log "setup_other" "misc"' 'Setting Up New Debian'
wait_before_execute 'silent_log "setup_debian" "debian"' 'Setting Up Debian Tweeks'
cd $PWD || exit

echo -e "\n# $GREEN Finished Setup $RESET #\n"
