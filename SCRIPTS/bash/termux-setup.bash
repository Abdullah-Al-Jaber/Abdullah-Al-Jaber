#!/data/data/com.termux/files/usr/bin/bash
yes | pkg update
yes | pkg upgrade

yes | pkg install python python-pip

curl -s https://raw.githubusercontent.com/abdullah-al-jaber/abdullah-al-jaber/vanilla/SCRIPTS/python/termux-setup.py > termux-setup.py
python termux-setup.py
