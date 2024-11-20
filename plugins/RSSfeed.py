import os
import feedparser
import asyncio
from pyrogram import Client, filters
from config import TG_BOT_TOKEN, API_ID, API_HASH, OWNER_ID, RSS_FEED_URL, CHECK_INTERVAL, GROUP_ID


# Helper Function: Read Anime List from File
def read_anime_list():
    if os.path.exists("anime_list.txt"):
        with open("anime_list.txt", "r") as f:
            anime_list = f.read().splitlines()
    else:
        anime_list = []
    return anime_list

# Helper Function: Read Sent Files from File
def read_sent_files():
    if os.path.exists("sendedfilesname.txt"):
        with open("sendedfilesname.txt", "r") as f:
            sent_files = f.read().splitlines()
    else:
        sent_files = []
    return sent_files

# Helper Function: Save Sent Files to File
def save_sent_file(filename):
    with open("sendedfilesname.txt", "a") as f:
        f.write(filename + "\n")

# Helper Function: Parse RSS and Filter Entries
def fetch_rss_feed():
    feed = feedparser.parse(RSS_FEED_URL)
    anime_list = read_anime_list()
    sent_files = read_sent_files()
    filtered_entries = []

    for entry in feed.entries:
        # Check if the entry matches an anime in the list and hasn't been sent yet
        if any(anime.lower() in entry.title.lower() for anime in anime_list) and entry.title not in sent_files:
            filtered_entries.append(entry)
    return filtered_entries

# Periodic Task: Check RSS Feed and Notify Group
async def periodic_check():
    while True:
        try:
            print("Checking RSS feed...")
            entries = fetch_rss_feed()
            for entry in entries:
                message = f"/lecch {entry.link}"
                await Bot.send_message(GROUP_ID, message)
                print(f"Sent to group: {message}")
                save_sent_file(entry.title)  # Save the title to avoid duplicates
            print("RSS check complete. Waiting for next interval.")
        except Exception as e:
            print(f"Error while checking RSS: {e}")
        await asyncio.sleep(CHECK_INTERVAL)

# Command: Add Anime to List
@Bot.on_message(filters.command("add_anime"))
async def add_anime(client, message):
    anime_name = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else None
    if anime_name:
        anime_list = read_anime_list()
        if anime_name.lower() not in [anime.lower() for anime in anime_list]:
            anime_list.append(anime_name)
            with open("anime_list.txt", "w") as f:
                for anime in anime_list:
                    f.write(anime + "\n")
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
            with open("anime_list.txt", "w") as f:
                for anime in anime_list:
                    f.write(anime + "\n")
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
