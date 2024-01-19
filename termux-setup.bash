#!/bin/bash

# Variable declaration
ver="1.0.1"
pwd=${pwd}

# Start up
echo -e "\n# Termux Setup Script v$ver\n\n"

apt update
yes | pkg upgrade

# Install Package 
yes | pkg install fish starship proot-distro wget curl

cd ~

### Configuration 

#Fish
echo -e "\nConfiguring FISH ...\n"

chsh -s fish
fish -c 'echo "starship init fish | source" >> ./.config/fish/config.fish'

fish -c "set -U fish_greeting "

echo -e "\nConfigured FISH.\n"

#User Bin Folder 
mkdir ./usr-bin
fish -c "fish_add_path ./usr-bin"

#Proot Debian
echo -e "\nSetting up Debian Distro ...\n"

proot-distro install debian
ln -s /storage/emulated/0 ./android
touch ./usr-bin/debian
echo 'proot-distro login --bind ~/android:/root/android debian -- "$@" '>> ./usr-bin/debian
chmod +x ./usr-bin/debian

debian sed -i 's/^/#/' /etc/apt/sources.list
debian echo 'deb [signed-by="/usr/share/keyrings/debian-archive-keyring.gpg"] http://deb.debian.org/debian testing main contrib non-free' >> /etc/apt/sources.list
debian apt update
debian apt clean
debian apt upgrade -y
debian apt install -y fish npm pip python
debian apt autoremove -y
debian chsh -s /usr/bin/fish
debian fish -c "set -U fish_greeting -e '\nWelcome to Debian (testing)\n'"

echo -e "\nFinished Setting up Debian Distro. \n"

#Misc
rm ../usr/etc/motd



cd $pwd
echo -e "\n# Finished Setup. \n\n"