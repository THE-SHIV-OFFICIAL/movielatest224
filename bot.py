import sys
import glob
import importlib
from pathlib import Path
from pyrogram import idle
import logging
import logging.config
import time  

# Get logging configurations


# Set up specific loggers
logger = logging.getLogger('bot')
pyrogram_logger = logging.getLogger("pyrogram")
pyrogram_logger.setLevel(logging.WARNING)
imdb_logger = logging.getLogger("imdbpy")
imdb_logger.setLevel(logging.ERROR)
aiohttp_logger = logging.getLogger("aiohttp")
aiohttp_logger.setLevel(logging.WARNING)

# Create custom formatter for colorful and attractive messages
class ColoredFormatter(logging.Formatter):
    # Color codes for terminal
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
        'RESET': '\033[0m'      # Reset
    }

    EMOJIS = {
        'DEBUG': '🔍',
        'INFO': '✅',
        'WARNING': '⚠️',
        'ERROR': '🔴',
        'CRITICAL': '💥'
    }

    def format(self, record):
        # Add emoji and color
        color = self.COLORS.get(record.levelname, '')
        emoji = self.EMOJIS.get(record.levelname, '')
        reset = self.COLORS['RESET']

        # Format with color and emoji
        record.levelname = f"{color}{emoji} {record.levelname}{reset}"
        return super().format(record)

from pyrogram import Client, __version__
from pyrogram.raw.all import layer
from database.ia_filterdb import Media, Media2, tempDict, choose_mediaDB, db as clientDB
from database.users_chats_db import db
from info import *
from utils import temp
from typing import Union, Optional, AsyncGenerator
from pyrogram import types
from Script import script 
from datetime import date, datetime 
import pytz
from aiohttp import web
from plugins import web_server, check_expired_premium

import asyncio
from pyrogram import idle
from ftmbotzx_botz import FtmbotzxBot
from util.keepalive import ping_server
from ftmbotzx_botz.clients import initialize_clients
botStartTime = time.time()

ppath = "plugins/*.py"
files = glob.glob(ppath)
loop = asyncio.get_event_loop()

async def Ftmbotzx_start():
    try:
        logger.info("🚀 Starting FtmBotzx Bot...")
        await FtmbotzxBot.start()

        bot_info = await FtmbotzxBot.get_me()
        FtmbotzxBot.username = bot_info.username
        logger.info(f"✅ Bot authenticated as: @{bot_info.username}")

        logger.info("🔧 Initializing additional clients...")
        await initialize_clients()

        logger.info("📦 Loading plugins...")
        loaded_plugins = 0
        for name in files:
            try:
                with open(name) as a:
                    patt = Path(a.name)
                    plugin_name = patt.stem.replace(".py", "")
                    plugins_dir = Path(f"plugins/{plugin_name}.py")
                    import_path = "plugins.{}".format(plugin_name)
                    spec = importlib.util.spec_from_file_location(import_path, plugins_dir)
                    load = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(load)
                    sys.modules["plugins." + plugin_name] = load
                    logger.info(f"  📄 {plugin_name}")
                    loaded_plugins += 1
            except Exception as e:
                logger.error(f"❌ Failed to load plugin {plugin_name}: {e}")

        logger.info(f"✅ Successfully loaded {loaded_plugins} plugins")

        logger.info("🔄 Setting up additional configurations...")
        if ON_HEROKU:
            logger.info("☁️ Heroku environment detected - Starting keep-alive service")
            asyncio.create_task(ping_server())

        logger.info("🚫 Loading banned users and chats...")
        b_users, b_chats = await db.get_banned()
        temp.BANNED_USERS = b_users
        temp.BANNED_CHATS = b_chats
        logger.info(f"📊 Loaded {len(b_users)} banned users and {len(b_chats)} banned chats")

        logger.info("🗂️ Ensuring database indexes...")
        await Media.ensure_indexes()
        await Media2.ensure_indexes()

        logger.info("💾 Checking database storage...")
        stats = await clientDB.command('dbStats')
        free_dbSize = round(512-((stats['dataSize']/(1024*1024))+(stats['indexSize']/(1024*1024))), 2)
        if DATABASE_URI2 and free_dbSize<62:
            tempDict["indexDB"] = DATABASE_URI2
            logger.warning(f"⚠️ Primary DB has only {free_dbSize} MB left - Using secondary DB")
        elif DATABASE_URI2 is None:
            logger.error("❌ Missing second DB URI! Add SECONDDB_URI now! Exiting...")
            exit()
        else:
            logger.info(f"💚 Primary DB has enough space ({free_dbSize}MB) - Using primary DB")

        await choose_mediaDB()   
        me = await FtmbotzxBot.get_me()
        temp.ME = me.id
        temp.U_NAME = me.username
        temp.B_NAME = me.first_name
        temp.B_LINK = me.mention
        FtmbotzxBot.username = '@' + me.username

        logger.info("⏰ Starting premium check task...")
        FtmbotzxBot.loop.create_task(check_expired_premium(FtmbotzxBot))

        logger.info(f"🎯 Movie Box Bot v5.0.2025 with Pyrogram v2.3.45 (Layer 187) started successfully!")
        logger.info("📊 Configuration Summary:")
        logger.info(LOG_STR)
        logger.info(script.LOGO)

        # Send restart notification
        tz = pytz.timezone('Asia/Kolkata')
        today = date.today()
        now = datetime.now(tz)
        time_str = now.strftime("%H:%M:%S %p")

        try:
            if LOG_CHANNEL:
                await FtmbotzxBot.send_message(chat_id=LOG_CHANNEL, text=script.RESTART_TXT.format(temp.B_LINK, today, time_str))
                logger.info("✅ Restart notification sent to log channel")
            else:
                logger.warning("⚠️ LOG_CHANNEL not configured - Skipping restart notification")
        except Exception as e:
            logger.warning(f"⚠️ Failed to send restart notification: {e}")

        # Start web server
        logger.info(f"🌐 Starting web server on port {PORT}...")
        app = web.AppRunner(await web_server())
        await app.setup()
        bind_address = "0.0.0.0"
        await web.TCPSite(app, bind_address, PORT).start()
        logger.info(f"✅ Web server started successfully on {bind_address}:{PORT}")

        logger.info("🎉 Shiv Bot is now running and ready to serve!")
        await idle()

    except Exception as e:
        logger.error(f"💥 Fatal error during bot startup: {e}")
        raise

if __name__ == '__main__':
    try:
        loop.run_until_complete(Ftmbotzx_start())
    except KeyboardInterrupt:
        logging.info('Service Stopped Bye 👋')
