import feedparser
from time import sleep
from pyrogram import filters
from config import TG_BOT_TOKEN, RSS_FEED_URL, GROUP_ID, OWNER_ID

from bot import Bot

# Lists for storing anime titles and sent titles
anime_list = []  # List of anime names to track
sent_anime_titles = []  # List of already sent anime titles to prevent duplicates

# Add an anime to the list
def add_anime_to_list(anime_name):
    if anime_name not in anime_list:
        anime_list.append(anime_name)
        return f"Added **{anime_name}** to your anime list."
    else:
        return f"**{anime_name}** is already in your list."

# Parse the RSS feed and send matching magnet links
def fetch_rss_and_send_mirrors():
    feed = feedparser.parse(RSS_FEED_URL)
    for entry in feed.entries:
        anime_name = entry.title.split(" - ")[0]  # Extract anime name from title
        
        # Check if the anime is in the tracked list and not sent before
        if anime_name in anime_list and anime_name not in sent_anime_titles:
            magnet_link = entry.link  # Extract magnet link from RSS entry
            # Send to the group
            Bot.send_message(GROUP_ID, f"/lecch {magnet_link}")
            # Add the anime name to sent list to avoid duplicate sending
            sent_anime_titles.append(anime_name)

# Command to add anime to the list (Only for owner)
@Bot.on_message(filters.command("addshow") & filters.user(OWNER_ID))
async def add_anime(client, message):
    anime_name = " ".join(message.command[1:])
    if anime_name:
        response = add_anime_to_list(anime_name)
        await message.reply(response)
    else:
        await message.reply("Please provide an anime name. Usage: `/addshow [anime name]`")

# Command to view the list of added anime (Only for owner)
@Bot.on_message(filters.command("showlist") & filters.user(OWNER_ID))
async def show_list(client, message):
    if anime_list:
        anime_list_text = "\n".join([f"- {anime}" for anime in anime_list])
        await message.reply(f"Here is the list of tracked anime:\n\n{anime_list_text}")
    else:
        await message.reply("The anime list is empty. Add anime using `/addshow`.")

# Command to start fetching and processing the RSS feed (Only for owner)
@Bot.on_message(filters.command("stasks") & filters.user(OWNER_ID))
async def start_tasks(client, message):
    await message.reply("Started monitoring the RSS feed. Updates will be sent to the group.")
    while True:
        fetch_rss_and_send_mirrors()  # Fetch and send mirrors
        sleep(150)  # Wait for 2 min before fetching again
