from pyrogram import Client, filters
import telegramify_markdown
from bot import Bot

# Your Telegram API credentials
api_id = "26254064"  # Replace with your API ID
api_hash = "72541d6610ae7730e6135af9423b319c"  # Replace with your API Hash
bot_token = "7615598964:AAHVRKevupQ-6msvK2MPO9pvvt8C97C27hQ"  # Replace with your bot token

# Create a Pyrogram Client
app = Client("quote_sender", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

# The text message that includes a quote
message_text = """
> One Piece

Seasson 20 - Episode 1111
"""

# Convert the Markdown text to Telegram's MarkdownV2 format
converted_message = telegramify_markdown.markdownify(message_text)

# Function to send the formatted message as a quote
def send_quote(channel_username, text):
    with app:
        app.send_message(
            chat_id=channel_username,
            text=text,
            parse_mode="MarkdownV2"
        )
        print("Quote sent successfully.")

# Command handler for /send
@Bot.on_message(filters.command("send"))
def send_command_handler(client, message):
    channel_username = "@AnimeQuestFamily"
    send_quote(channel_username, converted_message)
    message.reply("Quote sent successfully to @AnimeQuestFamily!")
