#!/data/data/com.termux/files/usr/bin/bash
yes | pkg update
yes | pkg upgrade

pkg install python curl

curl -s -H "Cache-Control: no-cache" https://raw.githubusercontent.com/abdullah-al-jaber/abdullah-al-jaber/vanilla/SCRIPTS/python/termux-setup.py > termux-setup.py
python termux-setup.py
