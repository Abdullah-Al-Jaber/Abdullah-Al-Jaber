#!/bin/bash

### Variable ###
PWD=$(pwd)
URL_PREFIX="https://raw.githubusercontent.com/abdullah-al-jaber/abdullah-al-jaber/vanilla/Scripts"
RED="\e[31m"
YELLOW="\e[33m"
GREEN="\e[32m"
BLUE="\e[34m"
RESET="\e[0m"

BUFFER=""

download_file() {
  filename="$1"
  url="${URL_PREFIX}/${filename}"
  path="${PWD}/${filename}"

  if [ -f "${path}" ]; then
    echo -e "${YELLOW}File ${filename} already exists.${RESET}"
    echo -e "${RED}Removing it !${RESET}"
    rm "${path}"
  fi

  # check if input given 
  if [ -z "$1" ]; then
    echo
    echo -ne "${BLUE}Please input the file name to download${RESET} : "
    read -i $BUFFER -r filename
    #BUFFER='$filename'
    download_file "${filename}"
    return
  fi

  echo -e "${YELLOW}Downloading ($BLUE${url}$RESET$YELLOW)${RESET}"
  code=$(curl -sL -w "%{http_code}\n"  -o "${path}" "${url}")

  if [[ $code -ne 200 ]]; then 
    echo -e "${RED}Failed to download (${filename}) ! ${RESET}"
    rm "${path}"
    download_file
    return
  fi 

  echo -e "${GREEN}Download complete !${RESET}"
}

download_file
chmod +x "$path"
