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
            }
        }
    }
    """
    variables = {"search": anime_name}
    response = requests.post(ANILIST_API_URL, json={"query": query, "variables": variables})

    if response.status_code == 200:
        return response.json().get("data", {}).get("Media", None)
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

    # Ask for the season number
    await message.reply(
        "Please provide the season number (e.g., `1`, `2`, `3`, etc.).",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("Cancel", callback_data="cancel_post")]]
        ),
    )
    await app.set_chat_data(chat_id=message.chat.id, key="anime_data", value={"title": title, "cover_image": cover_image, "next_ep": next_ep, "anime_name": anime_name})

# Handle Season Input
@Bot.on_message(filters.text & filters.user(OWNER_ID))
async def handle_season(client, message):
    anime_data = await app.get_chat_data(chat_id=message.chat.id, key="anime_data")
    if not anime_data:
        return  # No pending anime post

    # Save season input
    if not message.text.isdigit():
        await message.reply("Invalid season number. Please send a number (e.g., `1`, `2`, `3`).")
        return
    season = message.text
    anime_data["season"] = season

    # Construct caption
    caption = f"""✨ {anime_data['title']} ✨
──────────────────────
☀︎︎ Season - {season}
☀︎︎ Episode - {anime_data['next_ep']}
☀︎︎ Language - English Sub
──────────────────────
"""

    # Send preview with button to set URL
    msg = await message.reply_photo(
        photo=anime_data["cover_image"],
        caption=caption,
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("🏖️ Wᴀᴛᴄʜ / Dᴏᴡɴʟᴏᴀᴅ", callback_data=f"set_url_{anime_data['anime_name']}")]]
        ),
    )
    anime_data["msg_id"] = msg.message_id
    anime_data["caption"] = caption
    await app.set_chat_data(chat_id=message.chat.id, key="anime_data", value=anime_data)

# Callback: Set URL
@Bot.on_callback_query(filters.regex(r"set_url_(.+)") & filters.user(OWNER_ID))
async def set_url(client, callback_query):
    anime_data = await app.get_chat_data(chat_id=callback_query.message.chat.id, key="anime_data")
    if not anime_data:
        await callback_query.answer("No anime data found. Please try again.", show_alert=True)
        return

    await callback_query.message.reply("Please send the URL for the button.")
    await app.set_chat_data(chat_id=callback_query.message.chat.id, key="url_request", value=anime_data)

# Handle URL Input
@Bot.on_message(filters.text & filters.user(OWNER_ID))
async def handle_url(client, message):
    url_request = await app.get_chat_data(chat_id=message.chat.id, key="url_request")
    if not url_request:
        return  # No pending URL request

    # Update anime data with the provided URL
    url = message.text
    anime_data = url_request
    anime_data["url"] = url

    # Send confirmation message with button
    await message.reply_photo(
        photo=anime_data["cover_image"],
        caption=anime_data["caption"],
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("🏖️ Wᴀᴛᴄʜ / Dᴏᴡɴʟᴏᴀᴅ", url=url)],
                [InlineKeyboardButton("✅ Send Post", callback_data="send_post")],
                [InlineKeyboardButton("❌ Cancel", callback_data="cancel_post")],
            ]
        ),
    )
    await app.set_chat_data(chat_id=message.chat.id, key="anime_data", value=anime_data)

# Callback: Send Post
@Bot.on_callback_query(filters.regex(r"send_post") & filters.user(OWNER_ID))
async def send_post(client, callback_query):
    anime_data = await app.get_chat_data(chat_id=callback_query.message.chat.id, key="anime_data")
    if not anime_data:
        await callback_query.answer("No anime data found. Please try again.", show_alert=True)
        return

    # Send the post to both channels
    for channel_id in [ANIME_QUEST, ONGOING_ANIME_QUEST]:
        await app.send_photo(
            chat_id=channel_id,
            photo=anime_data["cover_image"],
            caption=anime_data["caption"],
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("🏖️ Wᴀᴛᴄʜ / Dᴏᴡɴʟᴏᴀᴅ", url=anime_data["url"])]]
            ),
        )

    await callback_query.message.reply("Post successfully sent to both channels!")
    await app.set_chat_data(chat_id=callback_query.message.chat.id, key="anime_data", value=None)

# Callback: Cancel Post
@Bot.on_callback_query(filters.regex(r"cancel_post") & filters.user(OWNER_ID))
async def cancel_post(client, callback_query):
    await callback_query.message.reply("Post creation cancelled.")
    await app.set_chat_data(chat_id=callback_query.message.chat.id, key="anime_data", value=None)

