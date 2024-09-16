#!/data/data/com.termux/files/usr/bin/bash

bash -c 'curl -s -H "Cache-Control: no-cache" https://raw.githubusercontent.com/abdullah-al-jaber/abdullah-al-jaber/vanilla/PyScripts/setup_script.py > setup.py'
pkg update
yes | pkg upgrade
yes | pkg install python3
python3 setup.py
