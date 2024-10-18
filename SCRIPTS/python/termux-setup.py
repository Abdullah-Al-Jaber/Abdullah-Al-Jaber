# built-in modules
import os
import sys
import time
import types
import subprocess


def install_modules(module_names: str):
  return_code = os.system(f"pip install {module_names}")

  if return_code != 0:
    print("[ERROR] Failed to install modules !")
    sys.exit(return_code)


install_modules("rich")
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
from rich.traceback import install

console = Console()
install(console=console)

os.system("clear")
title = "TERMINAL SETUP SCRIPT"
title_panel = Panel(title, style="bold yellow")
console.print(title_panel, justify="center")

success_tag = "[bold green][SUCCESS][/]"
error_tag = "[bold red][ERROR][/]"
debian_shell = None


def termux_command(command: str, show_output=False, show_error=False):
  result = subprocess.run(command, shell=True, capture_output=True)
  output = result.stdout.decode('utf-8').strip()
  error = result.stderr.decode('utf-8').strip()
  return_code = result.returncode

  if show_output and output:
    console.print(output)

  if show_error and error:
    console.print(error)

  if return_code != 0 and show_error:
    console.print(error_tag, "Failed to execute command !")
    console.print(f"[bold yellow]Command:[/] {command}")
    console.print("[CONTINUE] ? => [bold][ENTER][/]")
    input()


def debian_command(command: str, show_output=False, show_error=False):
  global debian_shell
  if not debian_shell:
    return

  #if not isinstance(debian_shell, subprocess.Popen):
  debian_shell = subprocess.Popen("debian",
                                  shell=True,
                                  stdin=subprocess.PIPE,
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE)

  result = debian_shell.communicate(input=command.encode())
  output = result[0].decode('utf-8').strip()
  error = result[1].decode('utf-8').strip()

  if show_output and output:
    console.print(output)

  if show_error and error:
    console.print(error)

  return_code = debian_shell.returncode

  if return_code != 0 and show_error:
    console.print(error_tag, "Failed to execute command !")
    console.print(f"[bold yellow]Command (debian):[/] {command}")
    console.print("[CONTINUE] ? => [bold][ENTER][/]")
    input()


def termux_install_packages(packages: str, show_output=False):
  termux_command(f"yes | pkg install {packages}", show_output)


def debian_install_packages(packages: str, show_output=False):
  debian_command(f"yes | apt install {packages}", show_output)


## list all functions in this script
old_functions = [
    name for name, func in globals().items()
    if isinstance(func, types.FunctionType)
]
## main functions


def termux_package_update_and_upgrade():
  """Update & Upgrade termux packages"""
  termux_command("yes | pkg update")
  termux_command("yes | pkg upgrade")


def termux_package_install():
  """Install termux packages"""
  termux_install_packages("")


def termux_setup_fish_and_starship():
  """Setup Fish & Starship (termux)"""
  termux_install_packages("fish starship")
  termux_command("chsh -s fish")
  termux_command("fish -c 'set -U fish_greeting'")
  termux_command("mkdir ~/usr-bin")
  termux_command("fish -c 'fish_add_path ~/usr-bin'")
  termux_command("export PATH=$PATH:~/usr-bin")
  termux_command(
      "echo 'starship init fish | source' >> ~/.config/fish/config.fish")
  termux_command("mv ~/../usr/etc/motd ~/.motd")


def termux_link_android_folder():
  """Link Android Folder (termux)"""
  termux_command("ln -s /storage/emulated/0/ ~/android")


def termux_install_debian():
  """Install Debian (termux)"""
  global debian_shell
  termux_install_packages("proot-distro")
  termux_command("proot-distro remove debian", show_error=False)
  termux_command("proot-distro install debian")
  login_code = 'proot-distro login --bind ~/android:/root/android debian -- "$@"'
  termux_command(f"echo '{login_code}' > ~/usr-bin/debian")
  termux_command("chmod +x ~/usr-bin/debian")
  debian_shell = True


def debian_package_update_and_upgrade():
  """Update & Upgrade debian packages"""
  debian_command("yes | apt update")
  debian_command("yes | apt upgrade")


def debian_package_install():
  """Install debian packages"""
  debian_install_packages("")


def debian_setup_fish_and_starship():
  """Setup Fish & Starship (debian)"""
  debian_install_packages("fish")
  debian_command("curl -sS https://starship.rs/install.sh > tmp.sh")
  debian_command("yes | bash tmp.sh")
  debian_command("rm tmp.sh")
  debian_command("chsh -s /usr/bin/fish")
  debian_command("fish -c 'set -U fish_greeting'")
  debian_command("mkdir ~/usr-bin")
  debian_command("fish -c 'fish_add_path ~/usr-bin'")
  debian_command(
      "echo 'starship init fish | source' >> ~/.config/fish/config.fish")
  debian_command(
      "starship preset bracketed-segments -o ~/.config/starship.toml")


def debian_setup_python3_venv():
  """Setup Python3 (debian)"""
  debian_install_packages("python3-full")
  debian_command("python3 -m venv ~/venv")
  debian_command(
      "echo 'source ~/venv/bin/activate.fish' >> ~/.config/fish/config.fish")


## last but must
new_functions = [
    name for name, func in globals().items()
    if isinstance(func, types.FunctionType)
]

main_functions = [name for name in new_functions if name not in old_functions]

map = [{
    "title": globals().get(function).__doc__,
    "function": globals().get(function)
} for function in main_functions]

for index, function in enumerate(map):
  tag = f"[bold blue][{index + 1}][/]"
  console.print(tag, function['title'].strip())

console.line()
skip_code = Prompt.ask("[bold]SKIP EXECUTION[/]", default="NONE")

run_list = [function["function"] for function in map]

if skip_code != "NONE":
  skip_codes = skip_code.split(" ")
  skip_codes = [skip_code.strip() for skip_code in skip_codes if skip_code]

  for code in skip_codes:
    if not code.isdigit():
      console.print(error_tag, f"Invalid number: {code}")
      sys.exit(1)
    else:
      code = int(code)

    if 1 <= code <= len(map):
      run_list.remove(map[code - 1]['function'])
    else:
      console.print(error_tag, f"Invalid code: {code}")
      sys.exit(1)

start_time = time.time()
for function in run_list:
  function()
end_time = time.time()

duration = end_time - start_time
duration = time.strftime("%H:%M:%S", time.gmtime(duration))

console.print(success_tag, "All done !", f"[bold yellow][{duration}][/]")
