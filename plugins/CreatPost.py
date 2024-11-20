import requests
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from config import TG_BOT_TOKEN, API_ID, API_HASH, OWNER_ID, ANIME_QUEST, ONGOING_ANIME_QUEST

from bot import Bot

# AniList API URL
ANILIST_API_URL = "https://graphql.anilist.co"

# Temporary storage
chat_data = {}

# Helper: Set chat data
async def set_chat_data(chat_id, key, value):
    if chat_id not in chat_data:
        chat_data[chat_id] = {}
    chat_data[chat_id][key] = value

# Helper: Get chat data
async def get_chat_data(chat_id, key):
    return chat_data.get(chat_id, {}).get(key)

# Fetch Anime Details
def fetch_anime_details(anime_name):
    query = """
    query ($search: String) {
        Media(search: $search, type: ANIME) {
            id
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
        return response.json()["data"]["Media"]
    return None

# Command: /anime [anime_name]
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
    cover_image = f"https://img.anili.st/media/{details['id']}"
    next_ep = details["nextAiringEpisode"]["episode"] if details["nextAiringEpisode"] else "Unknown"
    current_ep = next_ep - 1 if next_ep != "Unknown" else "Unknown"

    # Ask admin for season number
    await message.reply("Please provide the season number (e.g., `1`, `2`, `3`, etc.).")
    await set_chat_data(message.chat.id, "last_post", {
        "caption": {
            "title": title,
            "current_ep": current_ep,
        },
        "cover_image": cover_image,
        "anime_name": anime_name,
    })

# Handle Season Input
@Bot.on_message(filters.text & filters.user(OWNER_ID))
async def handle_season(client, message):
    last_post = await get_chat_data(message.chat.id, "last_post")
    if not last_post:
        return  # No pending season request

    # Try to parse season number
    try:
        season_number = int(message.text)
    except ValueError:
        await message.reply("Invalid input. Please provide a valid season number (e.g., `1`, `2`, `3`).")
        return

    # Update caption
    caption = f"""✨ {last_post['caption']['title']} ✨
──────────────────────
☀︎︎ Season - {season_number}
☀︎︎ Episode - {last_post['caption']['current_ep']}
☀︎︎ Language - English Sub
──────────────────────
Send the URL for the post (e.g., `https://example.com/download`)."""

    # Send the updated caption and thumbnail
    await message.reply_photo(
        photo=last_post["cover_image"],
        caption=caption
    )
    await set_chat_data(message.chat.id, "last_post", {**last_post, "caption": caption, "season": season_number})
    await set_chat_data(message.chat.id, "url_request", True)

# Handle URL Input
@Bot.on_message(filters.text & filters.user(OWNER_ID))
async def handle_url(client, message):
    url_request = await get_chat_data(message.chat.id, "url_request")
    if not url_request:
        return  # No pending URL request

    last_post = await get_chat_data(message.chat.id, "last_post")
    if not last_post:
        await message.reply("Could not find the previous post details. Please try again.")
        return

    # Add URL to the caption
    final_caption = f"{last_post['caption']}\n\n[🏖️ Watch / Download]({message.text})"
    button = InlineKeyboardMarkup([[InlineKeyboardButton("🏖️ Watch / Download", url=message.text)]])

    # Save the final post details
    await set_chat_data(message.chat.id, "final_post", {
        "caption": final_caption,
        "cover_image": last_post["cover_image"],
        "button": button,
    })

    # Show confirmation with "Send Post" button
    await message.reply_photo(
        photo=last_post["cover_image"],
        caption=final_caption,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✅ Send Post", callback_data="send_post")]])
    )
    await set_chat_data(message.chat.id, "url_request", None)

# Callback: Send Post
@Bot.on_callback_query(filters.regex(r"send_post") & filters.user(OWNER_ID))
async def send_post(client, callback_query):
    final_post = await get_chat_data(callback_query.message.chat.id, "final_post")
    if not final_post:
        await callback_query.answer("No post found to send.", show_alert=True)
        return

    # Send post to channels
    for channel_id in [ANIME_QUEST, ONGOING_ANIME_QUEST]:
        await client.send_photo(
            chat_id=channel_id,
            photo=final_post["cover_image"],
            caption=final_post["caption"],
            reply_markup=final_post["button"],
            parse_mode="markdown",
        )

    await callback_query.message.reply("Post successfully sent to both channels!")
    await callback_query.answer("Post sent!")

    # Clear data
    await set_chat_data(callback_query.message.chat.id, "final_post", None)
    await callback_query.message.delete()


