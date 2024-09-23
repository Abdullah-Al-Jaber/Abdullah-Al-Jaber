# built-in modules
import re
import os
import sys
import time
import shutil
import signal
import asyncio
import importlib


# custom module importer
def import_module(module_names: str, require: bool = True):
    modules = module_names.split(" ")

    found_modules = []
    not_found_modules = []
    for module_name in modules:
        try:
            module = importlib.import_module(module_name)
            found_modules.append(module)
        except ImportError:
            not_found_modules.append(module_name)

    if require and not_found_modules:
        not_found_text = " ".join(not_found_modules)
        print(f"[ERROR] Failed to import: {not_found_text}")
        sys.exit(1)
    else:
        return found_modules


# third party modules
import_module("rich requests bs4 edge_tts pydub")
import requests
import bs4
import edge_tts
import pydub

from rich.console import Console
from rich.prompt import Prompt
from rich.progress import Progress
from rich.panel import Panel
from rich.live import Live
from rich.traceback import install

install()
console = Console()

# info
novel_title = "THE FEMALE ZOMBIE REINCARNATED AS THE VILLAINS STEPMOTHER"
chapter_selector = ""

# config
url_pattern = "https://novelbjn.phieuvu.com/book/[novel-id]/[chapter-id]"
output_folder = "output"

folders = {
    "text": os.path.join(output_folder, "text"),
    "audio": os.path.join(output_folder, "audio"),
    "lyric": os.path.join(output_folder, "lyric"),
    "temporary": os.path.join(output_folder, ".temp")
}

download_config = {"worker_count": 5, "worker_interval": 5}

tts_config = {
    "parallel": {
        "worker_count": 3,
        "worker_interval": 1
    },
    "serial": {
        "worker_count": 5,
        "worker_interval": 1
    }
}

thread_count = 5

# console logging tags
error_tag = "[red bold][ERROR][/]"
success_tag = "[green bold][SUCCESS][/]"
info_tag = "[blue bold][INFO][/]"


# signal handler
def signal_handler(signal, frame):
    console.print(error_tag, "User interrupt !")
    sys.exit(1)


signal.signal(signal.SIGINT, signal_handler)


## functions
def parse_novel_id(novel_title: str):
    if not novel_title:
        console.print(error_tag, "Novel Title can't be empty !")
        sys.exit(1)
    novel_title_words = novel_title.split(" ")
    separator = "-"
    novel_id = separator.join(novel_title_words)
    return novel_id.lower()


def parse_chapter_id(chapter_number: int):
    chapter_id = f"chapter-{chapter_number}"
    return chapter_id


def parse_chapter_numbers(chapter_selector: str):
    if not chapter_selector:
        console.print(error_tag, "Chapter Selector can't be empty !")
        sys.exit(1)

    invalid_characters = re.search(r"[^\d|\-|\,]", chapter_selector)

    if invalid_characters:
        invalid_characters = invalid_characters.group()
        console.print(error_tag, f"Invalid characters: {invalid_characters}")
        sys.exit(1)

    selectors = chapter_selector.split(",")

    chapter_numbers = []
    for selector in selectors:
        if re.fullmatch(r"(\d+)-(\d+)", selector):
            start, end = selector.split("-")
            start = int(start)
            end = int(end)

            if start > end:
                console.print(error_tag, f"Invalid range: {selector}")
                sys.exit(1)

            for i in range(start, end + 1):
                chapter_numbers.append(i)
        elif re.fullmatch(r"\d+", selector):
            chapter_numbers.append(int(selector))
        else:
            console.print(error_tag, f"Invalid selector: {selector}")
            sys.exit(1)

    chapter_numbers = list(set(chapter_numbers))
    chapter_numbers = sorted(chapter_numbers)
    return chapter_numbers


def parse_download_url(novel_id: str, chapter_id: str):
    url = url_pattern
    url = url.replace("[novel-id]", novel_id)
    url = url.replace("[chapter-id]", chapter_id)
    return url


novel_title_prompt = "[red bold]Novel Title[/]"
if not novel_title:
    novel_title = Prompt.ask(novel_title_prompt)
else:
    console.print(f"{novel_title_prompt}: {novel_title}")

chapter_selector_prompt = "[yellow bold]Chapter Selector[/]"
if not chapter_selector:
    chapter_selector = Prompt.ask(chapter_selector_prompt)
else:
    console.print(f"{chapter_selector_prompt}: {chapter_selector}")

novel_id = parse_novel_id(novel_title)
chapter_numbers = parse_chapter_numbers(chapter_selector)

## let's make folders
if os.path.exists(folders["temporary"]):
    shutil.rmtree(folders["temporary"])

for folder in folders:
    os.makedirs(folders[folder], exist_ok=True)

## let's make chapters frame
chapters = []
for chapter_number in chapter_numbers:
    base_name = f"chapter-{chapter_number}"
    chapter_id = parse_chapter_id(chapter_number)
    html_url = parse_download_url(novel_id, chapter_id)

    text_path = os.path.join(folders["text"], f"{base_name}.txt")
    audio_path = os.path.join(folders["audio"], f"{base_name}.mp3")
    lyric_path = os.path.join(folders["lyric"], f"{base_name}.lrc")

    temporary_folder = os.path.join(folders["temporary"], base_name)

    chapter = {
        "number": chapter_number,
        "base_name": base_name,
        "id": chapter_id,
        "text_path": text_path,
        "audio_path": audio_path,
        "lyric_path": lyric_path,
        "temporary_folder": temporary_folder,
    }

    chapters.append(chapter)
chapter_count = len(chapters)


## download html of chapters
async def download_chapters(chapters: list):
    tasks = []
    for chapter in chapters:
        task = download_chapter(chapter)
        tasks.append(task)
    chapters = await asyncio.gather(*tasks)
    return chapters


async def download_chapter(chapter: dict):
    url = parse_download_url(novel_id, chapter["id"])
    response = await asyncio.to_thread(requests.get, url)
    response.raise_for_status()
    text = extract_html(response.text)
    with open(chapter["text_path"], "w") as text_file:
        text_file.write(text)
    progress.advance(download_task, advance=1)
    chapter["character_count"] = len(text)
    return chapter


def extract_html(html: str):
    soup = bs4.BeautifulSoup(html, "html.parser")
    title = soup.select_one("h1")
    paragraphs = soup.select("p")

    if not (title and paragraphs):
        html_error_file_path = os.path.join(folders["temporary"], "error.html")
        with open(html_error_file_path, "w") as html_error_file:
            html_error_file.write(html)

    if not title:
        raise Exception("No title found !")

    if not paragraphs:
        raise Exception("No paragraphs found !")

    title = title.text.strip()
    paragraphs = [paragraph.text for paragraph in paragraphs]
    paragraphs = "\n".join(paragraphs).split("\n")
    paragraphs = [paragraph for paragraph in paragraphs if paragraph.strip()]
    content = "\n".join(paragraphs)

    pattern = re.compile(r'[^a-zA-Z0-9\s\."!&]')
    text = title + "\n" + content
    text = re.sub(pattern, "", text)

    return text


async def tts_chapters(chapters: list):
    tasks = []
    for chapter in chapters:
        task = tts_chapter(chapter)
        tasks.append(task)
    await asyncio.gather(*tasks)


async def tts_chapter(chapter: dict):
    text = ""
    with open(chapter["text_path"], "r") as text_file:
        text = text_file.read()

    lines = text.split("\n")
    del text

    chunks = []
    for i in range(0, len(lines), tts_config["serial"]["worker_count"]):
        start = i
        end = i + tts_config['serial']["worker_count"]
        chunk = lines[start:end]
        chunks.append(chunk)

    os.makedirs(chapter["temporary_folder"], exist_ok=True)
    advance = 1 / len(lines)
    i = 0
    for index, chunk in enumerate(chunks):
        chuck_path = chapter['temporary_folder']
        chunks[index] = await tts_chunk(chunk, chuck_path, i, advance)
        i += len(chunk)
        await asyncio.sleep(tts_config["serial"]["worker_interval"])

    lines = []
    for chunk in chunks:
        lines.extend(chunk)
    lines = [line for line in lines if line.strip()]
    text = "\n".join(lines)

    backup_folder = os.path.join(folders["text"], ".original")
    os.makedirs(backup_folder, exist_ok=True)
    os.rename(chapter["text_path"], f"{backup_folder}/{chapter['base_name']}.txt")
    with open(chapter["text_path"], "w") as text_file:
        text_file.write(text)

    rename_files_in_dir(chapter["temporary_folder"])


async def tts_chunk(chunk, chunk_path, index, advance):
    tasks = []

    for i, text in enumerate(chunk):
        tag = f"{index + i}"
        output_file = os.path.join(chunk_path, f"{tag}.mp3")
        task = tts_text(text, output_file, advance)
        tasks.append(task)

    chunk = await asyncio.gather(*tasks)
    return chunk


async def tts_text(text: str, output_file: str, advance):
    try:
        tts = edge_tts.Communicate(text)
        progress.update(tts_task, advance=advance)
        await tts.save(output_file)
    except Exception as error:
        console.print(error_tag, f"Failed to convert text: {text}")
        console.print(error)
        if os.path.exists(output_file):
            os.remove(output_file)
        return ""

    ## check if audio ok
    if not os.path.exists(output_file):
        return ""

    try:
        pydub.AudioSegment.from_file(output_file)
        return text
    except Exception:
        console.print(error_tag, f"Failed to convert text: {text}")
        console.print(f"Invalid audio file: {output_file}")
        os.remove(output_file)
        return ""


async def audio_chapters(chapters: list):
    tasks = []
    for chapter in chapters:
        task = asyncio.to_thread(audio_chapter, chapter)
        tasks.append(task)
    chapters = await asyncio.gather(*tasks)
    return chapters


def audio_chapter(chapter: dict):
    output_file = chapter["audio_path"]

    text = ""
    with open(chapter["text_path"], "r") as text_file:
        text = text_file.read()
    lines = text.split("\n")

    advance = 1 / len(lines)
    lyrics = []
    main_audio = pydub.AudioSegment.empty()
    for i, line in enumerate(lines):
        input_file = os.path.join(chapter["temporary_folder"], f"{i}.mp3")
        audio = pydub.AudioSegment.from_file(input_file)

        time_stamp = time.strftime("%H:%M:%S",
                                   time.gmtime(main_audio.duration_seconds))
        lyrics.append(f"[{time_stamp}] {line}")

        main_audio += audio

        progress.update(audio_task, advance=advance)

    main_audio.export(output_file)

    lyric = "\n".join(lyrics)
    with open(chapter["lyric_path"], "w") as lyric_file:
        lyric_file.write(lyric)

    chapter["listen_time"] = main_audio.duration_seconds
    return chapter


def rename_files_in_dir(dir_path: str):
    list = os.listdir(dir_path)
    for i, file in enumerate(list):
        old_name = os.path.join(dir_path, file)
        new_name = os.path.join(dir_path, f"{i}.mp3")
        os.rename(old_name, new_name)


def get_directory_size(directory: str):
    total_size = 0
    for root, dirs, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            file_size = os.path.getsize(file_path)
            total_size += file_size

        for dir in dirs:
            dir_path = os.path.join(root, dir)
            dir_size = get_directory_size(dir_path)
            total_size += dir_size
    return total_size


progress = Progress(expand=True)
progress_panel = Panel(progress, title="Progress")
with Live(progress_panel, console=console, transient=True) as live:
    total_character_count = 0
    total_listen_time = 0
    download_task_text = "[cyan bold] DOWNLOAD [/]"
    tts_task_text = "[yellow bold] TTS [/]"
    audio_task_text = "[red bold] AUDIO [/]"
    download_task = progress.add_task(download_task_text, total=chapter_count)
    tts_task = progress.add_task(tts_task_text, total=chapter_count)
    audio_task = progress.add_task(audio_task_text, total=chapter_count)

    for i in range(0, chapter_count, download_config["worker_count"]):
        start = i
        end = i + download_config["worker_count"]

        try:
            chunk = chapters[start:end]
            chapters[start:end] = asyncio.run(download_chapters(chunk))
        except Exception as error:
            console.print(error_tag, "Failed to download chapter !")
            console.print(error)
            sys.exit(1)

        if not progress.tasks[download_task].finished:
            time.sleep(download_config["worker_interval"])

    for chapter in chapters:
        total_character_count += chapter["character_count"]

    total_character_count = f"{total_character_count:,d}"
    console.print(success_tag, "All chapters are downloaded successfully !")
    console.print(info_tag, f"Total character count: {total_character_count}")

    ## tts
    for i in range(0, chapter_count, tts_config["parallel"]["worker_count"]):
        start = i
        end = i + tts_config["parallel"]["worker_count"]

        chunk = chapters[start:end]

        try:
            asyncio.run(tts_chapters(chunk))
            if not progress.tasks[tts_task].finished:
                time.sleep(tts_config["parallel"]["worker_interval"])
        except Exception as error:
            console.print(error)
            sys.exit(1)

    total_used_size = get_directory_size(folders["temporary"])
    total_used_size = f"{total_used_size // 1024:,d} KB"
    console.print(success_tag,
                  "All chapters are converted to audio successfully !")
    console.print(info_tag, f"Total used size: {total_used_size}")

    ## audio
    for i in range(0, chapter_count, thread_count):
        start = i
        end = i + thread_count
        chunk = chapters[start:end]

        try:
            chapters[start:end] = asyncio.run(audio_chapters(chunk))
        except Exception as error:
            console.print(error_tag, "Failed to make audio !")
            console.print(error)
            sys.exit(1)

    for chapter in chapters:
        total_listen_time += chapter["listen_time"]

    total_listen_time = time.strftime("%H:%M:%S",
                                      time.gmtime(total_listen_time))
    console.print(success_tag, "All audios are joined successfully !")
    console.print(info_tag, f"Total listen time: {total_listen_time}")

shutil.rmtree(folders["temporary"])
console.print(error_tag, "You made me proud !")
