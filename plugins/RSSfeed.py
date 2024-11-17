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
    if os.path.exists(ANIME_LIST_FILE):
        with open(ANIME_LIST_FILE, "r") as f:
            anime_list = f.read().splitlines()
    else:
        anime_list = []
    return anime_list

# Helper Function: Write Anime List to File
def write_anime_list(anime_list):
    with open(ANIME_LIST_FILE, "w") as f:
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

# Helper Function: Download Torrent
def download_torrent(link, output_path):
    # Use aria2c or another method to download the torrent
    subprocess.run(["aria2c", "-d", output_path, link])

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
                await Bot.send_message("me", f"Starting download for: {task.title}\n{task.link}")
                download_torrent(task.link, DOWNLOAD_PATH)
                
                # Wait for the download to complete before uploading
                await Bot.send_message("me", f"Download complete: {task.title}. Now uploading...")
                
                # Upload the downloaded file
                for filename in os.listdir(DOWNLOAD_PATH):
                    file_path = os.path.join(DOWNLOAD_PATH, filename)
                    if os.path.isfile(file_path):
                        await Bot.send_document("me", file_path, caption=f"Uploaded: {filename}")
                        os.remove(file_path)  # Delete file after upload
                
                await Bot.send_message("me", f"Finished uploading: {task.title}")
            except Exception as e:
                await Bot.send_message("me", f"Error processing task {task.title}: {e}")
        else:
            await Bot.send_message("me", "No tasks in the queue. Waiting for new tasks.")
        
        # Sleep for a while before checking for the next task
        await asyncio.sleep(5)  # Adjust sleep time as necessary

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

