#!/bin/bash

echo -e "Termux Setup Script v2.0'

echo -e "Updating packages ..."
echo -e "\n[ Apt Update ]\n" > ./log.txt
yes | apt update > ./log.txt

echo -e "Upgrading packages ..."
echo -e "\n[ Package Upgrade ]\n" > ./log.txt
yes | pkg upgrade > ./log.txt
