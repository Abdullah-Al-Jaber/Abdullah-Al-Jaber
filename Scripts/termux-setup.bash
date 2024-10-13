# bash script for termux setup

yes | pkg update
yes | pkg upgrade

pkg install python curl

curl "https://guthub.vom/termux-setup.py" >> termux-setup.py
python termux-setup.py