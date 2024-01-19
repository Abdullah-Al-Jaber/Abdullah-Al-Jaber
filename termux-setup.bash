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
touch ./usr-bin/debian
echo "proot-distro login --bind /storage/emulated/0/:/root/android debian" >> ./usr-bin/debian
chmod +x ./usr-bin/debian

echo -e "\nFinished Setting up Debian Distro. \n"

#Misc
rm ../usr/etc/motd



cd $pwd
echo -e "\n# Finished Setup. \n\n"