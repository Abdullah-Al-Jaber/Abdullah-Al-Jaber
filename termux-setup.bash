#!/bin/bash

# Variable declaration
ver="1.0.0"
pwd=${pwd}

# Start up
echo -e "\n# Termux Setup Script v$ver\n\n"

apt update
yes | pkg upgrade

# Install Package 
yes | pkg install fish starship proot-distro 

cd ~

### Configuration 

#Fish

chsh -s fish
echo "starship init fish | source" >> ./.config/fish/config.fish

fish -c "fish_greeting -U "

#User Bin Folder 
mkdir ./usr-bin
fish -c "fish_add_path ./usr-bin"


#Misc
rm ../usr/etc/motd



cd $pwd
echo -e "\n# Finished Setup. \n\n"
