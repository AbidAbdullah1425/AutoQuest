import feedparser
from time import sleep
from pyrogram import filters
from config import TG_BOT_TOKEN, RSS_FEED_URL, GROUP_ID, OWNER_ID

from bot import Bot

# Lists for storing anime names to track and sent episode titles
anime_list = []  # List of anime names to track (e.g., "MF Ghost")
sent_anime_titles = []  # List of already sent episode titles to prevent duplicates

# Add an anime to the tracking list
def add_anime_to_list(anime_name):
    if anime_name not in anime_list:
        anime_list.append(anime_name)
        return f"Added **{anime_name}** to your tracking list."
    else:
        return f"**{anime_name}** is already being tracked."

# Parse the RSS feed and send new matches
def fetch_rss_and_send_mirrors():
    feed = feedparser.parse(RSS_FEED_URL)
    for entry in feed.entries:
        # Extract relevant fields from the RSS item
        title = entry.title  # Full title, e.g., "[SubsPlease] MF Ghost - 20 (480p) [511B71F6].mkv"
        link = entry.link  # Magnet link
        anime_name, episode_number = parse_title(title)  # Extract anime name and episode number

        # Match against tracked anime and ensure it's not already sent
        if anime_name in anime_list and title not in sent_anime_titles:
            # Send the magnet link to the group in the desired format
            formatted_message = f"/leech {link} -n [EP{episode_number}] - [{anime_name}][Eng Sub][1080p][@AnimeQuestX].mkv"
            Bot.send_message(GROUP_ID, formatted_message)
            
            # Add the title to the sent list to avoid duplicates
            sent_anime_titles.append(title)

# Extract anime name and episode number from the title
def parse_title(title):
    try:
        # Example title: "[SubsPlease] MF Ghost - 20 (480p) [511B71F6].mkv"
        anime_part = title.split("] ")[1]  # Extract "MF Ghost - 20 (480p)"
        anime_name, episode_and_quality = anime_part.split(" - ")  # Split "MF Ghost" and "20 (480p)"
        episode_number = episode_and_quality.split(" ")[0]  # Extract "20"
        return anime_name.strip(), episode_number.strip()
    except (IndexError, ValueError):
        return "Unknown Anime", "00"  # Default if parsing fails

# Command to add anime to the tracking list (Owner-only)
@Bot.on_message(filters.private & filters.user(OWNER_ID) & filters.command('addshow'))
async def add_anime(client, message):
    anime_name = " ".join(message.command[1:])
    if anime_name:
        response = add_anime_to_list(anime_name)
        await message.reply(response)
    else:
        await message.reply("Please provide an anime name. Usage: `/addshow [anime name]`")

# Command to view the list of tracked anime (Owner-only)
@Bot.on_message(filters.private & filters.user(OWNER_ID) & filters.command('showlist'))
async def show_list(client, message):
    # Check if anime_list is empty and respond only if it's empty
    if anime_list:
        anime_list_text = "\n".join([f"- {anime}" for anime in anime_list])
        await message.reply(f"Here is the list of tracked anime:\n\n{anime_list_text}")
    else:
        await message.reply("The tracking list is empty. Add anime using `/addshow`.")

# Command to start monitoring the RSS feed (Owner-only)
@Bot.on_message(filters.private & filters.user(OWNER_ID) & filters.command('starttasks'))
async def start_tasks(client, message):
    await message.reply("Started monitoring the RSS feed. Updates will be sent to the group.")
    while True:
        fetch_rss_and_send_mirrors()  # Fetch and send updates
        sleep(300)  # Wait 5 minutes before checking again

# Prevent the bot from responding to random text messages
@Bot.on_message(filters.private & filters.user(OWNER_ID) & ~filters.command())
async def ignore_text_messages(client, message):
    # Just return so it ignores any text that's not a command
    pass

# Main function
if __name__ == "__main__":
    Bot.run()
