import requests
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from config import TG_BOT_TOKEN, API_ID, API_HASH, OWNER_ID, ANIME_QUEST, ONGOING_ANIME_QUEST

from bot import Bot

# AniList API URL
ANILIST_API_URL = "https://graphql.anilist.co"

# Helper Function: Fetch Anime Details from AniList
def fetch_anime_details(anime_name):
    query = """
    query ($search: String) {
        Media(search: $search, type: ANIME) {
            title {
                english
                romaji
            }
            coverImage {
                extraLarge
            }
            nextAiringEpisode {
                episode
                timeUntilAiring
            }
            season
            seasonYear
        }
    }
    """
    variables = {"search": anime_name}
    response = requests.post(ANILIST_API_URL, json={"query": query, "variables": variables})
    
    if response.status_code == 200:
        data = response.json().get("data", {}).get("Media", None)
        return data
    return None

# Command: Fetch Anime Details
@Bot.on_message(filters.command("anime") & filters.user(OWNER_ID))
async def get_anime(client, message):
    anime_name = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else None
    if not anime_name:
        await message.reply("Please provide an anime name. Usage: `/anime <anime_name>`")
        return

    # Fetch anime details
    details = fetch_anime_details(anime_name)
    if not details:
        await message.reply("Could not find details for the anime. Please check the name.")
        return

    # Extract data
    title = details["title"]["english"] or details["title"]["romaji"]
    cover_image = details["coverImage"]["extraLarge"]
    next_ep = details["nextAiringEpisode"]["episode"] if details["nextAiringEpisode"] else "Unknown"
    season = details["season"] or "Unknown"
    season_year = details["seasonYear"] or "Unknown"
    season_text = f"{season.capitalize()} {season_year}"

    # Ask admin for the season if not found
    if season == "Unknown" or season_year == "Unknown":
        await message.reply("I couldn't fetch the season. Please provide the season manually (e.g., `Fall 2024`).")
        return

    # Construct caption
    caption = f"""✨ {title} ✨
──────────────────────
☀︎︎ Season - {season_text}
☀︎︎ Episode - {next_ep}
☀︎︎ Language - English Sub
──────────────────────"""

    # Send the thumbnail and caption, and ask for the URL
    msg = await message.reply_photo(
        photo=cover_image,
        caption=caption,
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("Set URL", callback_data=f"set_url_{anime_name}")]]
        )
    )
    # Save the message ID for further actions
    msg_id = msg.message_id
    await Bot.set_chat_data(chat_id=message.chat.id, key="last_post", value={"caption": caption, "cover_image": cover_image, "anime_name": anime_name, "msg_id": msg_id})

# Callback: Set URL
@Bot.on_callback_query(filters.regex(r"set_url_(.+)") & filters.user(OWNER_ID))
async def set_url(client, callback_query):
    anime_name = callback_query.data.split("_", 1)[1]
    await callback_query.message.reply("Please send the URL for the post (e.g., `https://example.com/download`).")
    await Bot.set_chat_data(chat_id=callback_query.message.chat.id, key="url_request", value=anime_name)

# Handle URL input
@Bot.on_message(filters.text & filters.user(OWNER_ID))
async def handle_url(client, message):
    url_request = await Bot.get_chat_data(chat_id=message.chat.id, key="url_request")
    if not url_request:
        return  # No pending URL request

    anime_name = url_request
    last_post = await Bot.get_chat_data(chat_id=message.chat.id, key="last_post")
    if not last_post:
        await message.reply("Could not find the previous post details. Please try again.")
        return

    # Add URL to the caption
    final_caption = f"{last_post['caption']}\n\n[🏖️ Watch / Download]({message.text})"

    # Send the finalized post to channels
    await Bot.send_photo(
        chat_id=ANIME_QUEST,
        photo=last_post["cover_image"],
        caption=final_caption,
        parse_mode="markdown",
    )
    await Bot.send_photo(
        chat_id=ONGOING_ANIME_QUEST,
        photo=last_post["cover_image"],
        caption=final_caption,
        parse_mode="markdown",
    )

    await message.reply("Post successfully sent to both channels!")
    # Clear data
    await Bot.set_chat_data(chat_id=message.chat.id, key="url_request", value=None)
    await Bot.set_chat_data(chat_id=message.chat.id, key="last_post", value=None)

Bot.run()
