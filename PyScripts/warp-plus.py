import os
import sys
import signal
import json
import random
import string
import datetime
import httpx
import time

red = "\033[0;31m"
blue = "\033[0;34m"
yellow = "\033[0;33m"
bold = "\033[1m"
reset = "\033[0m"

error_sign = red + bold + "[!]" + reset
info_sign = blue + bold + "[•]" + reset

version = "1.0.0"
window_title = name = "Help me"

save_file = "./data.json"
data = {
  "referrer": "",
  "good_request": 0,
  "bad_request": 0,
  "interval": 10
}
good = 0
bad = 0


try:
  import httpx
except ImportError:
  print(f"{error_sign} Python module 'httpx' not found !")
  print("\nRun following command to install it : \n")
  print(f"\t{bold}pip install httpx{reset}\n")
  sys.exit(1)

def set_window_title(title):
  if sys.platform == "win32":
    os.system(f"title {title}")
  elif sys.platform == "linux":
    os.system(f"echo -ne '\033]0;{title}\007'")
  else:
    print(f"{error_sign} Unsupported platform !")

set_window_title(window_title)

def clear_screen():
  if sys.platform == "win32":
    os.system("cls")
  elif sys.platform == "linux":
    os.system("clear")
  else:
    print(f"{error_sign} Unsupported platform !")


def save_data():
  global data
  with open(save_file, "w") as file:
    json.dump(data, file)


def gen_ran_str(length):
  return ''.join(
      random.choice(string.ascii_letters + string.digits)
      for _ in range(length))

def gen_ran_num(length):
  return ''.join(
      random.choice(string.digits)
      for _ in range(length))

def send_request():
  global data
  global api_url
  global good
  global bad
  try:
    install_id = gen_ran_str(22)
    body = {
        "key": f"{gen_ran_str(43)}=",
        "install_id": install_id,
        "fcm_token": f"{install_id}:APA91b{gen_ran_str(134)}",
        "referrer": f"{data['referrer']}",
        "warp_enabled": False,
        "tos": f"{datetime.datetime.now().isoformat()[:-3]}+02:00",
        "type": "Android",
        "locale": "es_ES",
    }

    headers = {
        'Content-Type': 'application/json; charset=UTF-8',
        'Host': 'api.cloudflareclient.com',
        'Connection': 'Keep-Alive',
        'Accept-Encoding': 'gzip',
        'User-Agent': 'okhttp/3.12.1'
    }

    response = httpx.post(api_url, headers=headers, json=body)
    if response.status_code == 200:
      print(f"{info_sign} Request sent successfully !")
      data["good_request"] += 1
      good += 1
      time.sleep(1)

    else:
      print(f"{error_sign} Failed to send request (server) !")
      print(f"{error_sign} Status code : {response.status_code}")
      print(f"\n{bold}[ Response ]{reset}\n{response.text}\n")
      data["bad_request"] += 1
      bad += 1
      time.sleep(5)

  except Exception as error:
    print(f"{error_sign} Failed to send request (client) !")
    print(f"\n{error}\n")
    return None

def show_menu():
  clear_screen()
  print(f"\t{bold}{name} {blue}v{version}{reset}\n")
  print(f"{yellow}[1]{reset} Start the script")
  print(f"{yellow}[2]{reset} Set Refferer ID")
  print(f"{yellow}[3]{reset} Set Request Intervals")
  print(f"{yellow}[4]{reset} Save Data")
  print(f"{yellow}[5]{reset} See Instructions")

  print(f"\n\t{bold}[ Press Ctrl +C to exit ]{reset}\n")

  code = input(f"\n{yellow}[?]{reset} Select an option : ")

  if code.isdigit() and 1 <= int(code) <= 5:
    run(int(code))
  else:
    timer(5,f"{error_sign} Invalid option !")
    show_menu()

def timer(seconds,message):
  for i in range(seconds, -1, -1):
    print(f"\r{message} {bold}[{i}s]{reset}", end="", flush=True)
    time.sleep(1)

def show_instruction():
  clear_screen()
  print(f"\t{bold}{name} {blue}v{version}{reset}\n")
  print(f"{blue}[1]{reset} Open 1.1.1.1 App.")
  print(f"{blue}[2]{reset} Go to {bold}Settings > Advanced > Diagnostics{reset}.")
  print(f"{blue}[3]{reset} Copy {bold}ID{reset} from {bold}Client Configuration{reset}.")
  print(f"{blue}[4]{reset} Run this script")
  print(f"{blue}[5]{reset} Paste the ID in {bold}Refferer ID{reset} field.")
  print(f"{blue}[6]{reset} Enjoy !!")

  print(f"\n\t{bold}[ Press Enter to go back ]{reset}\n")
  input()
  show_menu()

def run(code):
  global data
  if code == 1:
    global good
    global bad
    while True:
      clear_screen()
      if data["referrer"] == "":
        print(f"\t{bold}{name} {blue}v{version}{reset}\n")
        print("If you don't understand how to get the ID, read the instructions !")
        data["referrer"] = input(f"\n{yellow}[?]{reset} Enter Refferer ID : ")
        clear_screen()
      print(f"\t{bold}{name} {blue}v{version}{reset}\n")
      print(f"{info_sign} Current ID : {data['referrer']}")
      print(f"{info_sign} Good Requests : {good}")
      print(f"{info_sign} Bad Requests : {bad}")
      print(f"\n{yellow} Total : {bold}{data['good_request']} GB {reset}")
      print("\n------------\n")
      timer(data["interval"],f"{yellow}[•]{reset} Next Request in ")
      print(f"\n{info_sign} Sending Request to Server ...")
      send_request()
      save_data()
  elif code == 2:
    data["referrer"] = input(f"\n{yellow}[•]{reset} Enter Refferer ID : ")
    data['good_request'] = 0
    data['bad_request'] = 0
    show_menu()
  elif code == 3:
    interval = input(f"\n{yellow}[•]{reset} Enter Request Intervals (in seconds) : ")
    if interval.isdigit():
      data["interval"] = int(interval)
    else:
      timer(5,f"{error_sign} Invalid interval (only positive integers) !")
    show_menu()
  elif code == 4:
    save_data()
    timer(5,f"{info_sign} Data saved !")
    show_menu()
  elif code == 5:
    show_instruction()

def handle_interrupt(signal_number, frame):
  print(f"\n{info_sign} [ Exiting as requested ]")
  sys.exit(0)

signal.signal(signal.SIGINT, handle_interrupt)

api_url = f'https://api.cloudflareclient.com/v0a{gen_ran_num(3)}/reg'
#load data if exit on global data
if os.path.exists(save_file):
  with open(save_file, "r") as file:
    data = json.load(file)

show_menu()
