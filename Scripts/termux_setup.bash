#!/data/data/com.termux/files/usr/bin/bash

### VARIABLE ###
PWD=$(pwd)
COUNTDOWN=5
PACKAGES_1="fish starship proot-distro wget curl"
PACKAGES_2="python3 python3-pip"

# Styles 
BOLD="\e[1m"

GREEN="\e[32m"
YELLOW="\e[33m"
BLUE="\e[34m"

SPECIAL_COLOR="\e[37m"

TITLE="$SPECIAL_COLOR$BOLD"
RESET="\e[0m"

echo -e "$TITLE\n# Termux Setup Script #\n$RESET"

## FUNCTIONS
# function silent_log() {
#   eval "yes | $1" &>> "$LOG_PATH/$2.log"
# }

function update_pkg() {
  yes | apt update
  yes | pkg upgrade
}

function wait_before_execute () {
  count=$COUNTDOWN
  
  echo 
  while [ $count -gt -1 ]; do
    # read -t 1 -p "[ $YELLOW$BOLD$count$RESET ] $2"
    echo -ne "[ $YELLOW$BOLD$count$RESET ] $BLUE$2$RESET"
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
  ln -s /storage/emulated/0 ./android
  fish -c "set -U fish_greeting "
}

function setup_bin() {
  if [ -d "./usr-bin" ]; then rm -rf ./usr-bin; fi
  mkdir ./usr-bin
  rm ../usr/etc/motd
  fish -c "fish_add_path ./usr-bin"
  export PATH=$PATH:~/usr-bin
}


function setup_other() {
  proot-distro remove debian
  proot-distro install debian
  rm ./usr-bin/debian
  touch ./usr-bin/debian
  echo 'proot-distro login --bind ~/android:/root/android debian -- "$@" ' >> ./usr-bin/debian
  chmod +x ./usr-bin/debian
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
echo -e "$YELLOW( Press enter to skip any step )$RESET"
wait_before_execute "update_pkg" "Update &  Upgrade Packages"
wait_before_execute "yes | pkg install $PACKAGES_1" "Installing Additional Packages"

wait_before_execute "setup_fish" "Setting up Fish Shell"
wait_before_execute "setup_bin" "Setting up User Bin Folder"

wait_before_execute "setup_other" "Install New Debian System "
wait_before_execute "setup_debian" "Setting Up New Debian System"
cd "${PWD}" || exit

echo -e "\n# $GREEN $BOLD Finished Setup $RESET #\n"