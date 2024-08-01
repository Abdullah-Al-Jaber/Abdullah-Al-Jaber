import datetime
import os
import random
import signal
import string
import sys
import time
import pickle
import json

red = "\033[0;31m"
blue = "\033[0;34m"
green = "\033[0;32m"
yellow = "\033[0;33m"
bold = "\033[1m"
reset = "\033[0m"

error_sign = red + bold + "[!]" + reset
info_sign = blue + bold + "[•]" + reset

version = "1.0.0"
name = "Help me"
title = f"\n\t{bold}{name}{reset} {blue}v{version}{reset}\n"
window_title = f"{name} {version}"

save_file = "./data.pkl"
default_data = {
    "referrer": "",
    "good_request": 0,
    "bad_request": 0,
    "interval": 10
}
good_request = 0
bad_request = 0

try:
  import httpx
except ImportError:
  print(f"\n{error_sign} Python module 'httpx' not found !\n")
  print("Run following command to install it :")
  print(f"\t{bold}pip install httpx{reset}\n")
  sys.exit(1)


def set_window_title(title):
  os.system(f"echo -ne '\033]0;{title}\007'")


def clear_screen():
  os.system("clear")


def save_data():
  global data
  with open(save_file, "wb") as file:
    pickle.dump(data, file)


def gen_ran_str(length):
  return ''.join(
      random.choice(string.ascii_letters + string.digits)
      for _ in range(length))


def gen_ran_num(length):
  return ''.join(random.choice(string.digits) for _ in range(length))


def send_request():
  global data, api_url, good_request, bad_request
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
      print(f"{green}[•]{reset} Request sent successfully !")
      data["good_request"] += 1
      good_request += 1
      time.sleep(1)

    else:
      print(f"{error_sign} Failed to send request (server) !")
      print(f"{error_sign} Status code : {response.status_code}")
      print(f"\n{bold}[ Response ]{reset}\n")
      try:
        response_json = response.json()
        print(json.dumps(response_json, indent=2))
      except json.JSONDecodeError:
        print(f"{response.text}\n")
        print(f"{info_sign} Response is not valid JSON !")

      data["bad_request"] += 1
      bad_request += 1
      time.sleep(5)

  except Exception as error:
    print(f"{error_sign} Failed to send request (client) !")
    print(f"\n{error}\n")
    time.sleep(5)


def show_menu():
  clear_screen()
  print(f"\n\t{bold}{name}{reset} {blue}v{version}{reset}\n")
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
    timer(5, f"{error_sign} Invalid option !")
    show_menu()


def timer(seconds, message):
  for i in range(seconds, -1, -1):
    print(f"\r{message} {bold}[{i}s]{reset}", end="", flush=True)
    time.sleep(1)


def show_instruction():
  clear_screen()
  print(title)
  print(f"{blue}[1]{reset} Open 1.1.1.1 App.")
  print(
      f"{blue}[2]{reset} Go to {bold}Settings > Advanced > Diagnostics{reset}."
  )
  print(
      f"{blue}[3]{reset} Copy {bold}ID{reset} from {bold}Client Configuration{reset}."
  )
  print(f"{blue}[4]{reset} Run this script")
  print(f"{blue}[5]{reset} Paste the ID in {bold}Refferer ID{reset} field.")
  print(f"{blue}[6]{reset} Enjoy !!")

  print(f"\n\t{bold}[ Press Enter to go back ]{reset}\n")
  input()
  show_menu()


def run(code):
  global data
  if code == 1:
    global good_request, bad_request
    while True:
      while len(data["referrer"]) < 10:
        clear_screen()
        print(title)
        print(
            "If you don't understand how to get the ID, read the instructions !"
        )
        referrer = input(f"\n{yellow}[?]{reset} Enter Refferer ID : ")
        if len(referrer) < 10:
          timer(5, f"{error_sign} Refferer ID must be at least 10 characters !")
        else:
          data["referrer"] = referrer

      clear_screen()
      print(title)
      print(f"{info_sign} Current ID : {data['referrer']}")
      print(f"{info_sign} Good Requests : {good_request}")
      print(f"{info_sign} Bad Requests : {bad_request}")
      print(f"\n{yellow} Total : {bold}{data['good_request']} GB {reset}")
      print("\n------------\n")

      timer(data["interval"], f"{yellow}[•]{reset} Next Request in ")
      print(f"\n{info_sign} Sending Request to Server ...")

      send_request()
      save_data()

  elif code == 2:
    referrer = input(f"\n{yellow}[•]{reset} Enter Refferer ID : ")
    if len(referrer) > 10:
      data["referrer"] = referrer
      data['good_request'] = 0
      data['bad_request'] = 0
      show_menu()
    else:
      timer(5, f"{error_sign} Invalid ID !")
      show_menu()
  elif code == 3:
    interval = input(
        f"\n{yellow}[•]{reset} Enter Request Intervals (in seconds) : ")
    if interval.isdigit():
      data["interval"] = int(interval)
    else:
      timer(5, f"{error_sign} Invalid interval (only positive integers) !")
    show_menu()
  elif code == 4:
    save_data()
    timer(5, f"{info_sign} Data saved !")
    show_menu()
  elif code == 5:
    show_instruction()


def handle_interrupt(signal_number, frame):
  print(f",\n\n{info_sign} [ User Interrupted ] [{signal_number}]")
  sys.exit(0)


set_window_title(window_title)
signal.signal(signal.SIGINT, handle_interrupt)

api_url = f'https://api.cloudflareclient.com/v0a{gen_ran_num(3)}/reg'

if os.path.exists(save_file):
  with open(save_file, "rb") as file:
    data = pickle.load(file)
else:
  data = default_data

show_menu()
