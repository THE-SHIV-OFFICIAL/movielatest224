
import asyncio
import logging
from pyrogram import Client
from info import *

# Initialize storage for multiple clients
multi_clients = {}
work_loads = {}

# Main bot client
FtmbotzxBot = Client(
    "ftmbotzxbot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    sleep_threshold=SLEEP_THRESHOLD,
    workers=50,
    plugins={"root": "plugins"}
)

# Backward compatibility
ftmbotzxBot = FtmbotzxBot
