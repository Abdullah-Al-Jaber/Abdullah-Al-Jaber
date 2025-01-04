#!/usr/bin/env python

###########################
""" MIME HTML EXTRACTOR """
###########################
import re
import os
import sys
import shutil
import argparse

from rich.console import Console
from rich.traceback import install
from rich_argparse import RichHelpFormatter

console = Console()
install(console=console)

old_print = console.print


def new_print(*args, **kwargs):
  old_print(*args, **kwargs, overflow="ignore", crop=False)


console.print = new_print

error_tag = "[red bold][-][/]"
succes_tag = "[green bold][+][/]"
warn_tag = "[yellow bold][!][/]"
info_tag = "[blue bold][~][/]"

# setting up the parser
argument_parser = argparse.ArgumentParser(
    prog="mime-html-extractor",
    description="Extracts MIME HTML file",
    epilog="Copyright (c) 2021 - 2022 Mr. Spyder",
    formatter_class=RichHelpFormatter,
    exit_on_error=True)

argument_parser.add_argument(
    "-i",
    "--input",
    help="PATH to MIME HTML file",
    dest="input_file_path",
)
argument_parser.add_argument("-o",
                             "--output",
                             help="PATH to output folder",
                             dest="output_folder_path",
                             default="extracted_files",
                             required=False)
argument_parser.add_argument("-m",
                             "--mode",
                             help="Mode of extraction",
                             dest="extraction_mode",
                             default="res",
                             choices=["dom", "res"],
                             required=False)
arguments = argument_parser.parse_args()

# checking arguments
if not os.path.isfile(arguments.input_file_path):
  console.print(
      error_tag,
      f"File [cyan]{arguments.input_file_path}[/] does not exists !")
  sys.exit(1)

if os.path.isdir(arguments.output_folder_path):
  console.print(
      warn_tag,
      f"Folder [cyan]{arguments.output_folder_path}[/] already exists !")
  _override = input("Do you want to override it ? [Y/n] ").lower()
  if _override == "y":
    shutil.rmtree(arguments.output_folder_path)
  else:
    sys.exit(1)
os.mkdir(arguments.output_folder_path)

with open(arguments.input_file_path, "rb") as file:
  file_lines = file.read().split(b"\n")


# functions definition
def find_boundery_line(file_lines: list):
  prefix = b"------MultipartBoundary--"
  for line in file_lines:
    if line.startswith(prefix):
      return line
  else:
    console.print(error_tag, "No boundary line found !")
    sys.exit(1)


def flag_boundaries(file_lines: list):
  boundary = find_boundery_line(file_lines)
  flag_indexes = []
  for i, line in enumerate(file_lines):
    if line == boundary:
      flag_indexes.append(i)
  return flag_indexes


def divide_in_chunks(file_lines: list):
  flag_indexes = flag_boundaries(file_lines)
  chunks = []
  for i in range(len(flag_indexes) - 1):
    chunks.append(file_lines[flag_indexes[i]:flag_indexes[i + 1]])
  return chunks


def divide_raw_chunk(chunk: list):
  meta_data = []
  content = []
  meta_data_completed = False
  for line in chunk:
    if line == b"\r":
      meta_data_completed = True

    if not meta_data_completed:
      meta_data.append(line)
    else:
      content.append(line)
  meta_data = meta_data[1:]
  content = content[1:]
  return {"meta_data": meta_data, "content": content}


def extract_meta_data(meta_data: list) -> dict:
  meta_data_dict = {}
  for line in meta_data:
    line = line.decode("utf-8").strip()
    line = line.split(": ")
    meta_data_dict[line[0]] = line[1]
  return meta_data_dict


def chunkify(file_lines: list):
  raw_chunks = divide_in_chunks(file_lines)
  chunks = [divide_raw_chunk(raw_chunk) for raw_chunk in raw_chunks]
  for i, chunk in enumerate(chunks):
    meta_data = extract_meta_data(chunk["meta_data"])
    chunks[i] = {"meta_data": meta_data, "content": chunk["content"]}
  return chunks


def get_file_path(meta_data: dict, index, mode):
  if mode == "dom":
    if "Content-Location" in meta_data:
      file_path = meta_data["Content-Location"]
    elif "Content-ID" in meta_data:
      file_path = meta_data["Content-ID"]
    else:
      file_path = f"unknown/{index}"
      console.print(warn_tag, "No Content Location or Content ID found !")
      console.print(meta_data)
      console.print(info_tag, f"Using [cyan]{file_path}[/] as file path")
  elif mode == "res":
    if "Content-Type" in meta_data:
      file_path = f'{meta_data["Content-Type"]}/{index}'
    else:
      file_path = f"unknown/{index}"
      console.print(warn_tag, "No Content Type found !")
      console.print(meta_data)
      console.print(info_tag, f"Using [cyan]{file_path}[/] as file path")
  else:
    console.print(error_tag, "Invalid mode !")
    sys.exit(1)
  file_path = sanitize_file_path(file_path)

  if len(file_path) > 200:
    tokens = file_path.split("/")
    for i, token in enumerate(tokens):
      if len(token) > 100:
        tokens[i] = f"{token[:3]}...{token[-3:]}"
    file_path = "/".join(tokens)
    console.print(warn_tag, "File path is too long !")
    console.print(meta_data)
    console.print(info_tag, f"Using [cyan]{file_path}[/] as file path")

  return file_path


def sanitize_file_path(file_path: str):
  file_path = re.sub(r"/+", "/", file_path)
  file_path = re.sub(r"[^\w\s\-/#\+\.=]", "", file_path)
  return file_path


def ensure_folder(file_path: str):
  folder_path = os.path.dirname(file_path)
  if not os.path.exists(folder_path) and folder_path:
    os.makedirs(folder_path)


def write_file(file_path: str, content: bytes):
  with open(file_path, "wb") as file:
    file.write(content)


chunks = chunkify(file_lines)
del file_lines

for i, chunk in enumerate(chunks):
  if type(chunk["meta_data"]) is dict:
    try:
      file_path = get_file_path(chunk["meta_data"], i,
                                arguments.extraction_mode)
      file_path = os.path.join(arguments.output_folder_path, file_path)
      ensure_folder(file_path)
      write_file(file_path, b"\n".join(chunk["content"]))
      console.print(
          succes_tag,
          f"Extracted: [cyan]{file_path}[/]",
      )
    except Exception as error:
      console.print(error_tag, f"Error while extracting file : {error}")
      sys.exit(1)
  else:
    console.print(error_tag, "Invalid chunk !")
    sys.exit(1)
