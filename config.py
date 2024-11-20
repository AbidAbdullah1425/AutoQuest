#(©)CodeXBotz




import os
import logging
from logging.handlers import RotatingFileHandler



#Bot token @Botfather
TG_BOT_TOKEN = os.environ.get("TG_BOT_TOKEN", "7708810325:AAFTdEkc6BZ_OfsysafWqB-HgXAkWmsP6LE")

GROUP_ID = os.environ.get("GROUP_ID", "-4547144057")

#Your API ID from my.telegram.org
API_ID = int(os.environ.get("API_ID", "26254064"))

#Your API Hash from my.telegram.org
API_HASH = os.environ.get("API_HASH", "72541d6610ae7730e6135af9423b319c")

#Your db channel Id
CHANNEL_ID = int(os.environ.get("CHANNEL_ID", "-1002191732189"))

ANIME_QUEST = int(os.environ.get("ANIME_QUEST", "-1002125561929"))

ONGOING_ANIME_QUEST = int(os.environ.get("ONGOING_ANIME_QUEST", "-1002219567279"))

#OWNER ID
OWNER_ID = int(os.environ.get("OWNER_ID", "5296584067"))

RSS_FEED_URL = "https://subsplease.org/rss/?r=sd"

# File Paths
ANIME_LIST_FILE = "anime_list.txt"  # File to store the dynamic list of anime
DOWNLOAD_PATH = "./downloads/"

# Polling Interval for RSS Check
CHECK_INTERVAL = 600  # 10 minutes

PORT = os.environ.get("PORT", "8080")

TG_BOT_WORKERS = int(os.environ.get("TG_BOT_WORKERS", "4"))

#start message
START_MSG = os.environ.get("START_MESSAGE", "Hello {first} I'm a bot who can store files and share it via spacial links")
try:
    ADMINS=[]
    for x in (os.environ.get("ADMINS", "5296584067").split()):
        ADMINS.append(int(x))
except ValueError:
        raise Exception("Your Admins list does not contain valid integers.")

BOT_STATS_TEXT = "<b>BOT UPTIME</b>\n{uptime}"
USER_REPLY_TEXT = "❌Don't send me messages directly I'm only File Share bot!"

ADMINS.append(OWNER_ID)
ADMINS.append(5296584067)

LOG_FILE_NAME = "filesharingbot.txt"

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s - %(levelname)s] - %(name)s - %(message)s",
    datefmt='%d-%b-%y %H:%M:%S',
    handlers=[
        RotatingFileHandler(
            LOG_FILE_NAME,
            maxBytes=50000000,
            backupCount=10
        ),
        logging.StreamHandler()
    ]
)
logging.getLogger("pyrogram").setLevel(logging.WARNING)


def LOGGER(name: str) -> logging.Logger:
    return logging.getLogger(name)
