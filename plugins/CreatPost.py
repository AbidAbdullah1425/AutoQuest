from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
import requests
from config import TG_BOT_TOKEN, API_ID, API_HASH, OWNER_ID, ANIME_QUEST, ONGOING_ANIME_QUEST
from bot import Bot

CHANNELS = ["@AnimeQuestX", "@OngoingAnimeQuest"]

@Bot.on_message(filters.text & filters.private & filters.user(OWNER_ID))
async def season_episode_url_handler(client, message: Message):
    user_id = message.from_user.id
    user_input = message.text.strip()

    # Ensure user_data is initialized for the user
    if user_id not in user_data:
        await message.reply("Please start with `/anime [anime name]` to initialize.")
        return

    # Check for season input
    if "season" not in user_data[user_id]:
        # Validate Season Number
        if not user_input.isdigit() or not (1 <= int(user_input) <= 100):
            await message.reply("Invalid season number. Please provide a number between 1 and 100.")
            return
        user_data[user_id]["season"] = int(user_input)
        await message.reply(f"Season {user_input} selected. Now, send the episode number (1 - 5000).")
        return

    # Check for episode input
    if "episode" not in user_data[user_id]:
        # Validate Episode Number
        if not user_input.isdigit() or not (1 <= int(user_input) <= 5000):
            await message.reply("Invalid episode number. Please provide a number between 1 and 5000.")
            return
        user_data[user_id]["episode"] = int(user_input)
        await message.reply("Episode number selected. Now, send the URL for the button.")
        return

    # Check for URL input
    if "url" not in user_data[user_id]:
        # Validate URL
        if not (user_input.startswith("http://") or user_input.startswith("https://")):
            await message.reply("Invalid URL. Please provide a valid URL (starting with http:// or https://).")
            return
        user_data[user_id]["url"] = user_input

        # Prepare and send the final post
        anime_title = user_data[user_id]["anime_title"]
        anime_cover_url = user_data[user_id]["anime_cover_url"]
        season_number = user_data[user_id]["season"]
        episode_number = user_data[user_id]["episode"]
        button_url = user_data[user_id]["url"]

        post_text = (
            f"🇯🇵 {anime_title}\n"
            f"──────────────────────\n"
            f"☀︎︎ Season - {season_number:02d}\n"
            f"☀︎︎ Episode - {episode_number:02d}\n"
            f"☀︎︎ Language - [English Sub]\n"
            f"──────────────────────"
        )

        # Create inline button
        button = InlineKeyboardMarkup(
            [[InlineKeyboardButton("🏖️ Wᴀᴛᴄʜ / Dᴏᴡɴʟᴏᴀᴅ", url=button_url)]]
        )

        # Send post to channels
        for channel in CHANNELS:
            await client.send_photo(
                chat_id=channel,
                photo=anime_cover_url,
                caption=post_text,
                reply_markup=button
            )

        await message.reply("Post created and sent to channels!")

        # Clean up user data and turn off the process
        user_data.pop(user_id)
        return
