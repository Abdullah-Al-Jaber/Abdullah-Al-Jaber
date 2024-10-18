
# built-in modules
import re
import os
import sys
import time
import importlib
import contextlib


## custom module import function
def import_module(module_name):
    try:
        module = importlib.import_module(module_name)
        return module
    except ImportError:
        run_termux_command(f"pip install {module_name}", False)
        import_module(module_name)


## custom run functions
def run_termux_command(command, show_output=True):
    if not show_output:
        command = f"{command} > /dev/null"
    os.system(command)


def run_debian_command(command, show_output=True):
    command = f"debian bash -c '{command}'"
    if not show_output:
        command = f"{command} > /dev/null"
    os.system(command)


# third-party modules
import_module("rich")
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
from rich.traceback import install

install()
console = Console()

os.system("clear")
title = "TERMINAL SETUP SCRIPT"
title_panel = Panel(title, style="bold cyan")
console.print(title_panel, justify="center")

termux_packages = ""
debian_packages = "python3-full"

console.print("\n", "Select what to do:", "\n", style="bold")


def ter_up_pkg():
    run_termux_command("pkg update")
    run_termux_command("yes | pkg upgrade")


def ter_inst_pkg():
    run_termux_command(f"yes | pkg install {termux_packages}")


def set_fish_sh_ter():
    run_termux_command("yes | pkg install fish")
    run_termux_command("chsh -s fish")
    run_termux_command("fish -c 'set -U fish_greeting'")
    run_termux_command("mkdir ~/usr-bin")
    run_termux_command("fish -c 'fish_add_path ~/usr-bin'")
    run_termux_command("export PATH=$PATH:~/usr-bin")


def set_up_stsh_ter():
    run_termux_command("yes | apt install starship")
    run_termux_command(
        "echo 'starship init fish | source' >> ~/.config/fish/config.fish")


def link_ter():
    run_termux_command("ln -s /storage/emulated/0/ ~/android")
    run_termux_command("mv ~/../usr/etc/motd ~/.motd")


def debian_install():
    run_termux_command("yes | apt install proot-distro")
    run_termux_command("proot-distro remove debian")
    run_termux_command("proot-distro install debian")
    code = 'proot-distro login --bind ~/android:/root/android debian -- "$@"'
    run_termux_command(f"echo '{code}' > ~/usr-bin/debian")
    run_termux_command("chmod +x ~/usr-bin/debian")


def debian_up_pkg():
    run_debian_command("apt update")
    run_debian_command("yes | apt upgrade")


def debian_inst_pkg():
    run_debian_command(f"yes | apt install {debian_packages}")


def set_fish_sh_deb():
    run_debian_command("yes | apt install fish")
    run_debian_command("chsh -s /usr/bin/fish")
    run_debian_command("fish -c 'set -U fish_greeting'")
    run_debian_command("mkdir ~/usr-bin")
    run_debian_command("fish -c 'fish_add_path ~/usr-bin'")


def set_up_stsh_deb():
    run_debian_command("curl -sS https://starship.rs/install.sh > tmp.sh")
    run_debian_command("yes | bash tmp.sh")
    run_debian_command("rm tmp.sh")
    text = 'starship init fish | source'
    run_debian_command(f"echo '{text}' >> ~/.config/fish/config.fish")
    run_debian_command(
        "starship preset bracketed-segments -o ~/.config/starship.toml")


def set_up_python3_deb():
    run_debian_command("python3 -m venv ~/venv")
    run_debian_command(
        "echo 'source ~/venv/bin/activate.fish' >> ~/.config/fish/config.fish")


map = {
    1: {
        "msg": "update & upgrade packages (termux)",
        "func": ter_up_pkg
    },
    2: {
        "msg": "install packages (termux)",
        "func": ter_inst_pkg
    },
    3: {
        "msg": "set fish shell (termux)",
        "func": set_fish_sh_ter
    },
    4: {
        "msg": "set up starship (termux-fish)",
        "func": set_up_stsh_ter
    },
    5: {
        "msg": "link android (termux)",
        "func": link_ter
    },
    6: {
        "msg": "install debian",
        "func": debian_install
    },
    7: {
        "msg": "update & upgrade packages (debian)",
        "func": debian_up_pkg
    },
    8: {
        "msg": "install packages (debian)",
        "func": debian_inst_pkg
    },
    9: {
        "msg": "set fish shell (debian)",
        "func": set_fish_sh_deb
    },
    10: {
        "msg": "set up starship (debian-fish)",
        "func": set_up_stsh_deb
    },
    11: {
        "msg": "set up python3 (debian)",
        "func": set_up_python3_deb
    }
}

for i, v in map.items():
    console.print(f"[bold blue][{i}][/] {v['msg']}")

console.print("\n")
selection = Prompt.ask("[bold yellow][ANSWER IN ORDER][/]", default="yes")

runs = list(map.keys())

if selection != "yes":
    for code in selection.split():
        with contextlib.suppress(ValueError):
            runs.remove(int(code))

for code in runs:
    console.print(f"\n[bold blue]#{code}[/] {map[code]['msg']} [running]")
    map[code]["func"]()
