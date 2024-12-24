""" AUDIOBOOK GENERATOR """
# built-in modules
import re
import os
import sys
import time
import json
import shutil
import signal
import asyncio
import subprocess
import urllib.parse as url_parser

# third-party modules
from rich.console import Console, Group
from rich.panel import Panel
from rich.progress import Progress
from rich.live import Live
from rich.traceback import install

import requests
import py7zr
import ffmpeg
from bs4 import BeautifulSoup
from edge_tts import Communicate, VoicesManager

## pip install rich requests py7zr ffmpeg-python bs4 edge-tts eyed3

install()
console = Console()

auto_mode = True
trim_text = "1-10"

#### CONFIGURATION [START] ####
fresh_mode = True  # delete beforehand
mini_mode = True  # delete afterward
suppress_logs = False  # no useless logs
log_error = False  # log error to screen (if not, log to error file)

# console
success_tag = "[green][+][/]"
error_tag = "[red][-][/]"
info_tag = "[blue][•][/]"

# chapter urls
novel_id = "i-was-hoping-she-would-notice-but-again-now-when-she-did-im-tired"
chapter_list_url = f"https://novelbin.me/ajax/chapter-archive?novelId={novel_id}"

url_info = url_parser.urlparse(chapter_list_url)
base_url = f"{url_info.scheme}://{url_info.netloc}"

chapter_name_template = "chapter_[number]"
chapter_url_prefixes = (f"{base_url}/novel-book", f"{base_url}/book",
                        f"{base_url}/b")

chapter_urls_file = "chapter_urls.json"

# download html
download_directory = "html"
download_coroutine_count = 10
download_coroutine_interval = 1
download_max_retry_count = 3

# extract text
extract_directory = "text"

title_selector = "span.chr-text"
content_selector = "div#chr-content > p"
extract_coroutine_count = 5

# check and replace text
replace_terms = {}
replace_keywords = {}

_invalid_lines = False
invalid_lines = {}
invalid_lines_file = "invalid_lines.json"

# generate audiobook and subtitles
VOICE = "en-US-EmmaNeurall"
RATE = "+0%"
VOLUME = "+0%"
PITCH = "+0Hz"

generate_coroutine_count = 50
generate_max_retry_count = 3

audiobook_directory = "audiobook"
subtitle_directory = "subtitle"

# generate playlist
playlist_directory = "playlists"
tag_updater_count = 5
tags = {
    "artist": "'Audiobook Generator'",
    "album":
    "'I was hoping she would notice but again now when she did I am tired'",
    "comment": '"Hope is Okey"'
}
images = {"FRONT_COVER": "image.png"}

### CONFIGURATION [END] ###
_progress = Progress()
_task = _progress.add_task("NULL", total=0)
_total = 0
_invalid_line_store = False
refresh_rate = 1
blank = ""
error_log_file = "error.log"

show_voice_list = False
if show_voice_list:
  VOICES = asyncio.run(VoicesManager.create())
  VOICES = VOICES.find(Gender="Female", Locale="en-US", Language="en")
  VOICES = [VOICE["ShortName"] for VOICE in VOICES]
  console.print(VOICES)

  TEXT = "Hello, world! Good Luck on your fucking exams !"
  demo_directory = "demo"

  make_demo_audio = True
  if make_demo_audio:
    os.makedirs(demo_directory, exist_ok=True)
    for voice in VOICES:
      file_name = f"{voice}.mp3"
      file_path = os.path.join(demo_directory, file_name)
      communicate = Communicate(text=TEXT, voice=voice)
      asyncio.run(communicate.save(file_path))
    console.print(f"Audio files saved to {demo_directory}")
  sys.exit()


# misc func
def string(*strings):
  string = " ".join(strings)
  return string


def sort_by_number(string_list):
  numbers = []
  for string in string_list:
    nums = re.findall(r"\d+", string)
    if nums:
      numbers.append(int(nums[0]))
    else:
      console.print(error_tag, f"Invalid item: [yellow]{string}[/]")
      sys.exit(1)

  sorted_numbers = sorted(numbers)

  sorted_string_list = []
  for number in sorted_numbers:
    index = numbers.index(number)
    sorted_string_list.append(string_list[index])
  return sorted_string_list


# storage func
def write_file(file_path, content, mode="w"):
  tokens = file_path.split("/")
  directory = "/".join(tokens[:-1])
  if directory:
    os.makedirs(directory, exist_ok=True)
  with open(file_path, mode) as file:
    file.write(content)


def read_file(file_path, mode="r"):
  try:
    with open(file_path, "r") as file:
      content = file.read()
      return content
  except Exception as error:
    console.print(error_tag, f"Failed reading file: [yellow]{file_path}[/]")
    console.print(error)
    sys.exit(1)


def create_directory(directory):
  if fresh_mode and os.path.exists(directory):
    shutil.rmtree(directory)
  os.makedirs(directory, exist_ok=True)


def delete_directory(directory):
  if mini_mode and os.path.exists(directory):
    shutil.rmtree(directory)


def delete_file(file_path):
  if os.path.exists(file_path):
    os.remove(file_path)


def remove_empty_directory(directory):
  if mini_mode and os.path.exists(directory):
    if not os.listdir(directory):
      shutil.rmtree(directory)
    else:
      console.print(error_tag,
                    f"Directory is not empty: [yellow]{directory}[/]")
      sys.exit(1)


def remove_empty_file(file_path):
  if os.path.exists(file_path):
    content = read_file(file_path)
    if not content:
      os.remove(file_path)
    else:
      console.print(error_tag, f"File is not empty: [yellow]{file_path}[/]")
      sys.exit(1)


def count_files_in_directory(directory):
  file_count = 0
  for _, _, files in os.walk(directory):
    file_count += len(files)
  return file_count


def get_directory_size(directory):
  total_size = 0
  for dirpath, dirnames, filenames in os.walk(directory):
    for file in filenames:
      file_path = os.path.join(dirpath, file)
      total_size += os.path.getsize(file_path)
  return total_size / (1024 * 1024)


def get_file_size(file_path):
  return os.path.getsize(file_path) / (1024 * 1024)


# preprocess
def pre_process(line):
  return line


# tts fallback func
spell_map = {
    ".": "dot",
    "+": "plus",
    "-": "minus",
    "~": "tilde",
    "!": "exclamation",
    "@": "at",
    "#": "hash",
    "$": "dollar",
    "%": "percent",
    "^": "caret",
    "&": "ampersand",
    "*": "asterisk",
    "(": "left parenthesis",
    ")": "right parenthesis",
    "_": "underscore",
    "=": "equal",
    "'": "single quote",
    '"': "double quote",
    "<": "less than",
    ">": "greater than",
    "?": "question mark",
    "/": "forward slash",
    "|": "vertical bar",
    "{": "left curly bracket",
    "}": "right curly bracket",
    "[": "left square bracket",
    "]": "right square bracket",
    "\\": "backslash",
    ":": "colon",
    ";": "semicolon",
    ",": "comma",
    "—": "dash",
    "…": "ellipsis",
    "•": "bullet",
    "“": "left double quote",
    "”": "right double quote",
}


def spell_sign(sign):
  if sign in spell_map:
    return f" {spell_map[sign]} "
  else:
    return sign


def get_fallback_line(line):
  signs = re.findall(r"[^\w\s]", line)
  letters = re.findall(r"[\w]", line)

  if letters:
    return line

  signs = list(set(signs))
  for sign in signs:
    spell = spell_sign(sign)
    line = line.replace(sign, spell)
  line = re.sub(r"\s+", " ", line)
  line = line.strip()
  return line


# Progress Panel
def Progress_Panel(task_text, total=1):
  global _progress, _task
  _progress = Progress(expand=True)
  _task = _progress.add_task(task_text, total=total)
  _panel = Panel(_progress)
  _live_group = Group(blank, _panel, blank)
  return Live(_live_group, console=console)


# interrupt handler
def interrupt_handler(signal, frame):
  global interrupt_count
  interrupt_count += 1

  text = string(error_tag,
                f"Keyboard Interrupt Detected ! [{interrupt_count}]")
  panel = Panel(text, style="red")

  console.line()
  console.print(panel)
  sys.exit(1)


interrupt_count = 0
signal.signal(signal.SIGINT, interrupt_handler)


# download func
def get_relative_path(url):
  url_info = url_parser.urlparse(url)
  path = url_info.path
  relative_path = "/".join(path.split("/")[:-1])
  return relative_path


def get_absolute_url(input_url, document_url):
  url_info = url_parser.urlparse(document_url)
  base_url = f"{url_info.scheme}://{url_info.netloc}"
  relative_path = get_relative_path(input_url)

  if input_url.startswith(("http", "https")):
    return input_url
  elif input_url.startswith("/"):
    return base_url + input_url
  else:
    relative_path += f"/{input_url}"
    return base_url + relative_path


def download(url, file_path, show_log=True, retry_count=0):
  try:
    response = requests.get(url, stream=True)
    response.raise_for_status()
    write_file(file_path, response.content, "wb")

    if show_log and not suppress_logs:
      url_info = url_parser.urlparse(response.url)
      console.print(success_tag, f"Successful Download: {url_info.path}")

  except Exception as error:
    if retry_count <= download_max_retry_count:
      retry_count += 1
      time.sleep(download_coroutine_interval)
      download(url, file_path, show_log, retry_count)
    else:
      console.print(error_tag, f"Failed to download: {url}")
      console.print(error)
      sys.exit()


async def download_coroutine(url, file_path, download_semaphore):
  async with download_semaphore:
    task = asyncio.to_thread(download, url, file_path)
    await asyncio.sleep(download_coroutine_interval)
    await task
    _progress.update(_task, advance=1)


# extact texts
def extract(html_file):
  text_file = html_file.replace(".html", ".txt")
  html_file_path = os.path.join(download_directory, html_file)
  text_file_path = os.path.join(extract_directory, text_file)

  if not fresh_mode and os.path.exists(text_file_path):
    if not suppress_logs:
      console.print(success_tag,
                    f"CACHE(text file): [cyan]{text_file_path}[cyan]")
    _progress.update(_task, advance=1)
    if mini_mode:
      os.remove(html_file_path)
    return 'Horray !'

  try:
    html = read_file(html_file_path)
    soup = BeautifulSoup(html, "html.parser")
    title_elements = soup.select_one(title_selector)
    content_elements = soup.select(content_selector)

    if title_elements is None:
      console.print(error_tag, f"Failed to extract title: {html_file} ")
      raise Exception("title not found !")

    if content_elements is None:
      console.print(error_tag, f"Failed to extract content: {html_file} ")
      raise Exception("content not found !")

    title = title_elements.text.strip()
    contents = [content.text.strip() for content in content_elements]
    contents = [content for content in contents if content.strip()]
    content = "\n".join(contents)

    text = "\n".join([title, content])
    for regex, substitute in replace_keywords.items():
      text = re.sub(regex, substitute, text)

    lines = text.split("\n")
    for index, line in enumerate(lines):
      if line in replace_terms:
        lines[index] = replace_terms[line]

    for index, line in enumerate(lines):
      lines[index] = pre_process(line)

    global invalid_lines
    for index, line in enumerate(lines):
      if not re.search(r"[\w]", line):
        line_num = index + 1
        chapter_name = html_file.replace(".html", "")
        if html_file in invalid_lines:
          invalid_lines[chapter_name][line_num] = line
        else:
          invalid_lines[chapter_name] = {line_num: line}

    text = "\n".join(lines)
    write_file(text_file_path, text)
    _progress.update(_task, advance=1)
    if not suppress_logs:
      console.print(success_tag, f"Extracted: [magenta]{text_file_path}[/]")
    if mini_mode:
      os.remove(html_file_path)
  except Exception as error:
    console.print(error_tag, f"Failed to extract: {html_file}")
    console.print(error)
    sys.exit()


async def extract_coroutine(html_file, extract_semaphore):
  async with extract_semaphore:
    task = asyncio.to_thread(extract, html_file)
    await task


# audiobook and subtitles funcs
def append_subtitle(subtitle_file_path, subtitle_text):
  with open(subtitle_file_path, "a") as file:
    file.write(subtitle_text)


def get_audio_duration(file_path):
  try:
    probe = ffmpeg.probe(file_path)
    duration = float(probe['format']['duration'])
    return duration
  except Exception as error:
    console.print(error_tag, f"Failed to get audio duration: {file_path}")
    console.print(error)
    sys.exit()


async def generator(line,
                    line_number,
                    audiobook_file_path,
                    subtitle_file_path,
                    progress_percentage,
                    fallback_line=None,
                    retry_count=0):
  if fallback_line is not None:
    LINE = fallback_line
  else:
    LINE = line

  try:
    if os.path.exists(audiobook_file_path):
      current_time = get_audio_duration(audiobook_file_path)
    else:
      current_time = 0

    with open(audiobook_file_path, "ab") as audio_file:
      communicate = Communicate(LINE,
                                VOICE,
                                rate=RATE,
                                volume=VOLUME,
                                pitch=PITCH)

      async for chunk in communicate.stream():
        if chunk["type"] == "audio":
          audio_file.write(chunk["data"])
      time_tag = time.strftime("%H:%M:%S", time.gmtime(current_time))
      lyrics = f"[{time_tag}] {line}"
      append_subtitle(subtitle_file_path, lyrics + "\n")
      _progress.update(_task, advance=progress_percentage)

  except Exception as error:
    if retry_count <= generate_max_retry_count:
      retry_count += 1
      fallback_line = get_fallback_line(line)
      await generator(line, line_number, audiobook_file_path,
                      subtitle_file_path, progress_percentage, fallback_line,
                      retry_count)
    else:
      console.print(error_tag, f"Failed to generate audio: [yellow]{line}[/]")
      console.print(info_tag, f"Fallback line: [yellow]{LINE}[/]")
      console.print(info_tag,
                    f"AUD: [red]{audiobook_file_path}[/] LINE NUM: {index}")
      console.print(error)


async def generate_audiobook_subtitle(chapter_name):
  text_file_path = os.path.join(extract_directory, f"{chapter_name}.txt")
  audiobook_file_path = os.path.join(audiobook_directory,
                                     f"{chapter_name}.mp3")
  subtitle_file_path = os.path.join(subtitle_directory, f"{chapter_name}.lrc")

  text = read_file(text_file_path)
  lines = text.split("\n")
  progress_percentage = 1 / len(lines)

  delete_file(audiobook_file_path)
  delete_file(subtitle_file_path)

  for index, line in enumerate(lines):
    line = line.strip()
    line_number = index + 1

    if not line:
      continue

    await generator(line, line_number, audiobook_file_path, subtitle_file_path,
                    progress_percentage)

  subtitle = read_file(subtitle_file_path)
  subtitle_lines = subtitle.split("\n")
  subtitle_lines = [line for line in subtitle_lines if line.strip()]
  subtitle = "\n".join(subtitle_lines)
  write_file(subtitle_file_path, subtitle)


async def generate_audiobook_subtitle_coroutine(chapter_name,
                                                generate_semaphore):
  async with generate_semaphore:
    dot_file_path = os.path.join(audiobook_directory, f".{chapter_name}")
    audiobook_file_path = os.path.join(audiobook_directory,
                                       f"{chapter_name}.mp3")
    subtitle_file_path = os.path.join(subtitle_directory,
                                      f"{chapter_name}.lrc")

    dot_exists = os.path.exists(dot_file_path)
    audiobook_exists = os.path.exists(audiobook_file_path)
    subtitle_exists = os.path.exists(subtitle_file_path)

    files_exists = audiobook_exists and subtitle_exists

    if not dot_exists and files_exists:
      if not suppress_logs:
        console.print(success_tag,
                      f"CACHE(audiobook): [cyan]{chapter_name}.mp3[cyan]")
      _progress.update(_task, advance=1)
      return 'Horray !'

    write_file(dot_file_path, "Please chottomatte !")

    task = generate_audiobook_subtitle(chapter_name)
    await task

    if not suppress_logs:
      console.print(success_tag, f"Generated: {chapter_name}")
    os.remove(dot_file_path)


# playlist
def tag_updater(chapter_name):
  text_file_path = os.path.join(extract_directory, f"{chapter_name}.txt")
  audiobook_file_path = os.path.join(audiobook_directory,
                                     f"{chapter_name}.mp3")
  subtitle_file_path = os.path.join(subtitle_directory, f"{chapter_name}.lrc")
  playlist_file_path = os.path.join(playlist_directory, f"{chapter_name}.mp3")

  if os.path.exists(playlist_file_path):
    os.remove(playlist_file_path)
  shutil.copy(audiobook_file_path, playlist_file_path)

  command = ["eyeD3"]
  track_number = re.findall(r"\d+", chapter_name)[0]
  track_total = _total

  title = read_file(text_file_path).split("\n")[0]

  for image_type, image_path in images.items():
    if os.path.exists(image_path):
      command.append(f"--add-image {image_path}:{image_type}")

  for option, value in tags.items():
    command.append(f"--{option} {value}")

  title = title.replace("\"", "'")
  command.append(f'--title "{title}"')
  command.append(f"--add-lyrics {subtitle_file_path}")
  command.append(f"--track {track_number}")
  command.append(f"--track-total {track_total}")
  command.append(playlist_file_path)
  command = " ".join(command)

  process = subprocess.Popen(command,
                             shell=True,
                             stdout=subprocess.PIPE,
                             text=True)
  stdout, stderr = process.communicate()

  if process.returncode == 0:
    _progress.update(_task, advance=1)
    if not suppress_logs:
      console.print(success_tag, f"Generated: {playlist_file_path}")
    if mini_mode:
      os.remove(audiobook_file_path)
      os.remove(subtitle_file_path)
  else:
    console.print(error_tag, f"Failed to generate playlist: {stderr}")
    console.print(info_tag, f"Command: [yellow]{command}[/]")
    console.print("[blue] STDOUT: [/]", stdout)
    console.print("[red] STDERR: [/]", stderr)
    os.remove(playlist_file_path)
    sys.exit()


async def tag_updater_coroutine(chapter_name, tag_semaphore):
  async with tag_semaphore:
    task = asyncio.to_thread(tag_updater, chapter_name)
    await task


# compress
def compress_to_7z(input_directory, output_archive):
  if not os.path.isdir(input_directory):
    console.print(error_tag, f"Invalid input folder: {input_directory}")
    sys.exit()

  directory_size = get_directory_size(input_directory)
  with Progress_Panel("COMPRESS", total=directory_size):
    with py7zr.SevenZipFile(output_archive, 'w') as archive:
      for root, _, files in os.walk(input_directory):
        for file in files:
          file_path = os.path.join(root, file)
          archive.write(file_path,
                        arcname=os.path.relpath(file_path, input_directory))
          _progress.advance(_task, get_file_size(file_path))
          if mini_mode:
            os.remove(file_path)


# MAIN FUNCTION
def chapter_urls():
  try:
    if fresh_mode and os.path.exists(chapter_urls_file):
      os.remove(chapter_urls_file)

    if os.path.exists(chapter_urls_file):
      console.print(success_tag, "CACHE MODE: Chapter URL file found")
      with open(chapter_urls_file, "r") as list_file:
        chapter_urls = json.load(list_file)
      console.print(info_tag,
                    f"Chapter url list: [cyan]{chapter_urls_file}[/]")
      console.print(info_tag, f"Chapter count: {len(chapter_urls)}")
      console.line()
    else:
      console.print(info_tag, "Downloading chapter url list...")
      response = requests.get(chapter_list_url)
      response.raise_for_status()
      chapter_list_html = response.text

      console.print(success_tag, "Downloaded chapter url list !")

      soup = BeautifulSoup(chapter_list_html, "html.parser")
      urls = [link.get("href") for link in soup.find_all("a", href=True)]

      urls = [get_absolute_url(url, chapter_list_url) for url in urls]

      _urls = []
      for url in urls:
        if url in _urls:
          continue
        _urls.append(url)
      urls = urls

      _chapter_urls = [
          url for url in urls if url.startswith(chapter_url_prefixes)
      ]

      chapter_urls = {}
      for index, chapter_url in enumerate(_chapter_urls):
        chapter_name = chapter_name_template
        chapter_number = index + 1
        chapter_name = chapter_name.replace("[number]", str(chapter_number))
        chapter_urls[chapter_name] = chapter_url

      with open(chapter_urls_file, "w") as list_file:
        json.dump(chapter_urls, list_file, indent=2)

      global _total
      _total = len(chapter_urls)

      console.line()
      console.print(info_tag,
                    f"Chapter url list: [magenta]{chapter_urls_file}[/]")
      console.print(info_tag, f"Chapter count: {len(chapter_urls)}")
      console.line()
  except Exception as error:
    console.print(error_tag, f"Failed to download chapter url list: {error}")
    sys.exit(1)


def _trim_urls(range_text):
  with open(chapter_urls_file, "r") as list_file:
    chapter_urls = json.load(list_file)

  if not re.search(r"\d+-\d+", range_text):
    console.print(error_tag, "Invalid range: [red]RANGE[/]")
    sys.exit()

  range_text = range_text.strip()
  range_text = range_text.split("-")
  start, end = int(range_text[0]), int(range_text[1])
  if start > end:
    start, end = end, start
  console.print(info_tag, f"Trimmed range: [cyan]{start}-{end}[/]")
  console.print(info_tag, f"Trimmed boundary: {end - start + 1}")

  new_chapter_urls = {}
  for chapter_name, chapter_url in chapter_urls.items():
    chapter_number = re.findall(r"\d+", chapter_name)[0]
    if int(chapter_number) >= start and int(chapter_number) <= end:
      new_chapter_urls[chapter_name] = chapter_url

  console.print(success_tag, f"New chapter count: {len(new_chapter_urls)}")

  with open(chapter_urls_file, "w") as list_file:
    json.dump(new_chapter_urls, list_file, indent=2)
  console.line()


async def _download():
  with open(chapter_urls_file, "r") as list_file:
    chapter_urls = json.load(list_file)

  create_directory(download_directory)
  html_files = os.listdir(download_directory)

  _chapter_urls = {}
  for chapter_name, url in chapter_urls.items():
    html_file = f"{chapter_name}.html"
    if html_file in html_files:
      html_file_path = os.path.join(download_directory, html_file)
      if not suppress_logs:
        console.print(success_tag,
                      f"CACHE(html file): [cyan]{html_file_path}[/]")
    else:
      _chapter_urls[chapter_name] = url
  chapter_urls = _chapter_urls

  with Progress_Panel("DOWNLOAD", total=len(chapter_urls)):
    tasks = []
    html_semaphore = asyncio.Semaphore(download_coroutine_count)
    for chapter_name, chapter_url in chapter_urls.items():
      html_file = f"{chapter_name}.html"
      html_file_path = os.path.join(download_directory, html_file)
      task = download_coroutine(chapter_url, html_file_path, html_semaphore)
      tasks.append(task)
    await asyncio.gather(*tasks)

  html_file_count = count_files_in_directory(download_directory)

  console.line()
  console.print(info_tag, f"Download Directory: {download_directory}")
  console.print(info_tag, f"Chapter count: {html_file_count}")


async def _extract():
  create_directory(extract_directory)

  html_files = os.listdir(download_directory)

  with Progress_Panel("EXTRACT", total=len(html_files)):
    extract_semaphore = asyncio.Semaphore(extract_coroutine_count)
    tasks = []
    for html_file in html_files:
      task = extract_coroutine(html_file, extract_semaphore)
      tasks.append(task)
    await asyncio.gather(*tasks)

  if _invalid_lines:
    invalid_lines_set = set()
    for file_name, lines in invalid_lines.items():
      invalid_lines_set.update(lines.values())

    invalid_lines["_set"] = list(invalid_lines_set)
    with open(invalid_lines_file, "w") as json_file:
      json.dump(invalid_lines, json_file, indent=2)

  file_count = count_files_in_directory(extract_directory)

  if mini_mode:
    remove_empty_directory(download_directory)

  console.line()
  console.print(info_tag, f"Extract directory: {extract_directory}")
  console.print(info_tag, f"File count: {file_count}")


async def _generate_audiobook_subtitle():
  create_directory(audiobook_directory)
  create_directory(subtitle_directory)

  text_files = os.listdir(extract_directory)

  generate_semaphore = asyncio.Semaphore(generate_coroutine_count)
  with Progress_Panel("AUDIOBOOK", total=len(text_files)):
    tasks = []
    for text_file in text_files:
      chapter_name = text_file.replace(".txt", "")
      task = generate_audiobook_subtitle_coroutine(chapter_name,
                                                   generate_semaphore)
      tasks.append(task)
    await asyncio.gather(*tasks)


async def _playlist():
  create_directory(playlist_directory)
  audiobook_files = os.listdir(audiobook_directory)
  subtitle_files = os.listdir(subtitle_directory)

  audiobook_files = sort_by_number(audiobook_files)
  subtitle_files = sort_by_number(subtitle_files)

  if len(audiobook_files) != len(subtitle_files):
    console.print(error_tag, "Audiobook and subtitle files count mismatch !")
    sys.exit(1)
  else:
    length = len(audiobook_files)

  with Progress_Panel("PLAYLIST", total=length):
    playlist_semaphore = asyncio.Semaphore(tag_updater_count)
    tasks = []
    for index in range(length):
      chapter_name = audiobook_files[index].replace(".mp3", "")
      task = tag_updater_coroutine(chapter_name, playlist_semaphore)
      tasks.append(task)
    await asyncio.gather(*tasks)
  if mini_mode:
    remove_empty_directory(audiobook_directory)
    remove_empty_directory(subtitle_directory)


def compress():
  output_archive = f"{trim_text}.7z"
  if os.path.exists(output_archive):
    console.print(error_tag, f"Archive already exists: {output_archive}")
    sys.exit(1)

  input_directory = playlist_directory
  directory_size = get_directory_size(input_directory)
  console.print(info_tag,
                f"Directory size: [yellow]{directory_size:.2f}[/] MB")

  try:
    compress_to_7z(input_directory, output_archive)
  except Exception as error:
    console.print(error_tag, f"Failed to compress: {error}")
    sys.exit(1)

  archive_file_size = get_file_size(output_archive)
  console.print(info_tag,
                f"Archive size: [yellow]{archive_file_size:.2f}[/] MB")
  if mini_mode:
    remove_empty_directory(input_directory)
  console.line()


# wraper functions
def download_htmls():
  asyncio.run(_download())
  console.line()


def extract_texts():
  asyncio.run(_extract())
  console.line()


def trim_urls():
  arguments = sys.argv[1:]
  range_text = arguments[arguments.index("trim") + 1]
  _trim_urls(range_text)


def Audio_Subtitle():
  asyncio.run(_generate_audiobook_subtitle())
  console.line()


def playlist():
  asyncio.run(_playlist())
  console.line()


if not log_error:
  sys.stderr = open(os.devnull, 'w')  # maybe no error log at all !
  delete_file(error_log_file)
  sys.stderr = open(error_log_file, 'a')

try:
  map = {
      "urls": chapter_urls,
      "trim": trim_urls,
      "htmls": download_htmls,
      "texts": extract_texts,
      "main": Audio_Subtitle,
      "playlist": playlist,
      "compress": compress
  }

  if len(sys.argv) > 1:
    auto_mode = False
    arguments = sys.argv[1:]
    for index, argument in enumerate(arguments):
      if argument in map:
        map[argument]()
      else:
        parametered_arguments = ["trim"]
        previous_argument = arguments[index - 1]
        if previous_argument not in parametered_arguments:
          console.print(error_tag, f"Invalid argument: {argument}")
          sys.exit(1)

  if auto_mode:
    chapter_urls()
    _trim_urls(trim_text)
    download_htmls()
    extract_texts()
    Audio_Subtitle()
    playlist()
    compress()

    delete_directory(extract_directory)

    # random replit crap
    delete_directory(".pythonlibs")
    delete_directory(".upm")
    delete_directory(".cache")
    delete_directory(".local")
    delete_directory(".git")
    delete_file(".gitignore")

  remove_empty_file(error_log_file)
except Exception as error:
  console.print(error_tag, "Unhandled Exception occured !")
  console.print(error)
  # raise error
