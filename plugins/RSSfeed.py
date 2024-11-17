import os
import feedparser
import subprocess
import time
from pyrogram import Client, filters
import asyncio

from bot import Bot  # Import Bot from bot.py

# Load Config
from config import BOT_TOKEN, API_ID, API_HASH, OWNER_ID, RSS_FEED_URL, DOWNLOAD_PATH, CHECK_INTERVAL

# Task queue
task_queue = []

# Helper Function: Read Anime List from File
def read_anime_list():
    if os.path.exists("anime_list.txt"):
        with open("anime_list.txt", "r") as f:
            anime_list = f.read().splitlines()
    else:
        anime_list = []
    return anime_list

# Helper Function: Write Anime List to File
def write_anime_list(anime_list):
    with open("anime_list.txt", "w") as f:
        for anime in anime_list:
            f.write(anime + "\n")

# Helper Function: Parse RSS and Filter Entries
def fetch_rss_feed():
    feed = feedparser.parse(RSS_FEED_URL)
    anime_list = read_anime_list()
    filtered_entries = []
    for entry in feed.entries:
        if any(anime.lower() in entry.title.lower() for anime in anime_list) or \
           any(anime.lower() in entry.category.lower() for anime in anime_list):
            filtered_entries.append(entry)
    return filtered_entries

# Helper Function: Download Torrent with Progress
def download_torrent(link, output_path):
    command = [
        "aria2c",
        "--dir", output_path,
        "--console-log-level=error",
        "--show-console-readout=false",
        "--download-result=hide",
        "--progress=dot",
        link
    ]
    
    # Start the download process
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    # Monitor the progress of the download
    while True:
        output = process.stdout.readline()
        if output == b"" and process.poll() is not None:
            break
        if output:
            # Parse the download progress from the output
            output_str = output.decode('utf-8').strip()
            if "download" in output_str:  # Filter relevant output
                # Send download progress to Telegram
                Bot.send_message(OWNER_ID, f"Download Progress: {output_str}")

# Command: Add Anime to List
@Bot.on_message(filters.command("add_anime"))
async def add_anime(client, message):
    anime_name = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else None
    if anime_name:
        anime_list = read_anime_list()
        if anime_name.lower() not in [anime.lower() for anime in anime_list]:
            anime_list.append(anime_name)
            write_anime_list(anime_list)
            await message.reply(f"Added {anime_name} to the anime list.")
        else:
            await message.reply(f"{anime_name} is already in the list.")
    else:
        await message.reply("Please provide an anime name after the command. Example: /add_anime Fairy Tail")

# Command: Remove Anime from List
@Bot.on_message(filters.command("remove_anime"))
async def remove_anime(client, message):
    anime_name = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else None
    if anime_name:
        anime_list = read_anime_list()
        if anime_name.lower() in [anime.lower() for anime in anime_list]:
            anime_list = [anime for anime in anime_list if anime.lower() != anime_name.lower()]
            write_anime_list(anime_list)
            await message.reply(f"Removed {anime_name} from the anime list.")
        else:
            await message.reply(f"{anime_name} is not in the list.")
    else:
        await message.reply("Please provide an anime name after the command. Example: /remove_anime Fairy Tail")

# Command: View Anime List
@Bot.on_message(filters.command("anime_list"))
async def anime_list(client, message):
    anime_list = read_anime_list()
    if anime_list:
        await message.reply("Current Anime List:\n" + "\n".join(anime_list))
    else:
        await message.reply("The anime list is empty. Use /add_anime <anime_name> to add anime.")

# Command: Check RSS and Download Matches
@Bot.on_message(filters.command("check_rss"))
async def check_rss(client, message):
    await message.reply("Fetching RSS feed...")
    entries = fetch_rss_feed()
    if not entries:
        await message.reply("No matching anime found.")
        return

    # Add tasks to the queue
    for entry in entries:
        task_queue.append(entry)
        await message.reply(f"Added to queue: {entry.title}\nLink: {entry.link}")

# Function to process tasks from the queue
async def process_tasks():
    while True:
        if task_queue:
            task = task_queue.pop(0)  # Get the first task (most recent)
            try:
                # Download the task
                await Bot.send_message(OWNER_ID, f"Starting download for: {task.title}\n{task.link}")
                download_torrent(task.link, DOWNLOAD_PATH)

                # Wait for the download to complete before uploading
                await Bot.send_message(OWNER_ID, f"Download complete: {task.title}. Now uploading...")

                # Upload the downloaded file with progress
                for filename in os.listdir(DOWNLOAD_PATH):
                    file_path = os.path.join(DOWNLOAD_PATH, filename)
                    if os.path.isfile(file_path):
                        await Bot.send_document(OWNER_ID, file_path, caption=f"Uploaded: {filename}", progress=progress_callback)
                        os.remove(file_path)  # Delete file after upload

                await Bot.send_message(OWNER_ID, f"Finished uploading: {task.title}")
            except Exception as e:
                await Bot.send_message(OWNER_ID, f"Error processing task {task.title}: {e}")
        else:
            await Bot.send_message(OWNER_ID, "No tasks in the queue. Waiting for new tasks.")

        # Sleep for a while before checking for the next task
        await asyncio.sleep(5)  # Adjust sleep time as necessary

# Progress callback for upload
async def progress_callback(current, total, upload_file, message):
    progress = current / total * 100
    progress_message = f"Uploading {upload_file}: {progress:.2f}%"
    await message.edit(progress_message)

# Start the periodic check loop
async def periodic_check():
    while True:
        try:
            print("Checking RSS feed...")
            entries = fetch_rss_feed()
            if entries:
                for entry in entries:
                    # Add matching tasks to the queue
                    task_queue.append(entry)
                    print(f"Added to queue: {entry.title}")
            else:
                print("No new episodes found.")
        except Exception as e:
            print(f"Error while checking RSS: {e}")

        # Sleep for a set interval before checking again
        await asyncio.sleep(CHECK_INTERVAL)


# Run the bot and periodic check
async def start_bot():
    # Start the periodic check
    asyncio.create_task(periodic_check())
    
    # Process tasks from the queue
    await process_tasks()

# Start the bot
Bot.run(start_bot())
