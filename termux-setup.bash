#!/data/data/com.termux/files/usr/bin/bash

# Variable declaration
ver="1.0.0"
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

chsh -s fish
fish -c 'echo "starship init fish | source" >> ./.config/fish/config.fish'

fish -c "set -U fish_greeting "

#User Bin Folder 
mkdir ./usr-bin
fish -c "fish_add_path ./usr-bin"
export PATH=$PATH:~/usr-bin

#Proot Debian

proot-distro install debian
rm ./usr-bin/debian
ln -s /storage/emulated/0 ./android
touch ./usr-bin/debian
echo 'proot-distro login --bind ~/android:/root/android debian -- "$@" ' >> ./usr-bin/debian
chmod +x ./usr-bin/debian

debian sed -i 's/^/#/' /etc/apt/sources.list
debian bash -c 'echo deb [signed-by="/usr/share/keyrings/debian-archive-keyring.gpg"] http://deb.debian.org/debian testing main contrib non-free >> /etc/apt/sources.list'
debian apt clean
debian apt update
debian bash -c "yes | apt upgrade"
debian bash -c "yes | apt install fish"
debian bash -c "yes | apt autoremove"
debian fish -c 'set -U fish_greeting -e "\nWelcome to Debian (testing)\n"'
debian chsh -s /usr/bin/fish
debian bash -c "yes | apt install npm python3-pip ranger"
#Misc
rm ../usr/etc/motd



cd $pwd
echo -e "\n# Finished Setup. \n\n"
