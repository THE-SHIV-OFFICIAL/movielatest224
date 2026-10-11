#Join Telegram Channel - @ftmbotzx_dhakad

import logging
from pyrogram import Client, filters, enums
from pyrogram.types import ChatJoinRequest
from database.users_chats_db import db
from info import ADMINS

# 🔹 Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

AUTH_CHANNEL = -1002926855756


@Client.on_chat_join_request(filters.chat(AUTH_CHANNEL))
async def join_reqs(client, message: ChatJoinRequest):
    logger.info(f"📩 Join request from {message.from_user.id} ({message.from_user.first_name}) in chat {message.chat.id}")

    if not await db.find_join_req(message.from_user.id):
        await db.add_join_req(message.from_user.id)
        logger.info(f"✅ User {message.from_user.id} added to DB")
    else:
        logger.info(f"ℹ️ User {message.from_user.id} already in DB")

@Client.on_message(filters.command("delreq") & filters.private & filters.user(ADMINS))
async def del_requests(client, message):
    await db.del_join_req()
    logger.info("🗑️ All join request entries deleted from DB")
    await message.reply("<b>⚙ ꜱᴜᴄᴄᴇꜱꜱғᴜʟʟʏ ᴄʜᴀɴɴᴇʟ ʟᴇғᴛ ᴜꜱᴇʀꜱ ᴅᴇʟᴇᴛᴇᴅ</b>")
