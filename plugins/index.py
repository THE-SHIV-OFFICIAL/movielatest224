import logging
import asyncio
from pyrogram import Client, filters, enums
from pyrogram.errors import FloodWait
from pyrogram.errors.exceptions.bad_request_400 import ChannelInvalid, ChatAdminRequired, UsernameInvalid, UsernameNotModified
from info import ADMINS
from info import INDEX_REQ_CHANNEL as LOG_CHANNEL
from database.ia_filterdb import save_file
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils import temp
from util.fast_index import extract_media
import time
import re
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
lock = asyncio.Lock()


@Client.on_callback_query(filters.regex(r'^index'))
async def index_files(bot, query):
    if query.data.startswith('index_cancel'):
        temp.CANCEL = True
        return await query.answer("Cancelling Indexing")
    _, raju, chat, lst_msg_id, from_user = query.data.split("#")
    if raju == 'reject':
        await query.message.delete()
        await bot.send_message(int(from_user),
                               f'Your Submission for indexing {chat} has been decliened by our moderators.',
                               reply_to_message_id=int(lst_msg_id))
        return

    if lock.locked():
        return await query.answer('Wait until previous process complete.', show_alert=True)
    msg = query.message

    await query.answer('Processing...⏳', show_alert=True)
    if int(from_user) not in ADMINS:
        await bot.send_message(int(from_user),
                               f'Your Submission for indexing {chat} has been accepted by our moderators and will be added soon.',
                               reply_to_message_id=int(lst_msg_id))
    await msg.edit(
        "Starting Indexing",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton('Cancel', callback_data='index_cancel')]]
        )
    )
    try:
        chat = int(chat)
    except:
        chat = chat
    await index_files_to_db(int(lst_msg_id), chat, msg, bot)


@Client.on_message((filters.forwarded | (filters.regex(r"(https://)?(t\.me/|telegram\.me/|telegram\.dog/)(c/)?(\d+|[a-zA-Z_0-9]+)/(\d+)$")) & filters.text ) & filters.private & filters.incoming)
async def send_for_index(bot, message):
    if message.text:
        regex = re.compile(r"(https://)?(t\.me/|telegram\.me/|telegram\.dog/)(c/)?(\d+|[a-zA-Z_0-9]+)/(\d+)$")
        match = regex.match(message.text)
        if not match:
            return await message.reply('Invalid link')
        chat_id = match.group(4)
        last_msg_id = int(match.group(5))
        if chat_id.isnumeric():
            chat_id  = int(("-100" + chat_id))
    elif message.forward_from_chat.type == enums.ChatType.CHANNEL:
        last_msg_id = message.forward_from_message_id
        chat_id = message.forward_from_chat.username or message.forward_from_chat.id
    else:
        return
    try:
        await bot.get_chat(chat_id)
    except ChannelInvalid:
        return await message.reply('This may be a private channel / group. Make me an admin over there to index the files.')
    except (UsernameInvalid, UsernameNotModified):
        return await message.reply('Invalid Link specified.')
    except Exception as e:
        logger.exception(e)
        return await message.reply(f'Errors - {e}')
    try:
        k = await bot.get_messages(chat_id, last_msg_id)
    except:
        return await message.reply('Make Sure That Iam An Admin In The Channel, if channel is private')
    if k.empty:
        return await message.reply('This may be group and iam not a admin of the group.')

    if message.from_user.id in ADMINS:
        buttons = [
            [
                InlineKeyboardButton('Yes',
                                     callback_data=f'index#accept#{chat_id}#{last_msg_id}#{message.from_user.id}')
            ],
            [
                InlineKeyboardButton('close', callback_data='close_data'),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(buttons)
        return await message.reply(
            f'Do you Want To Index This Channel/ Group ?\n\nChat ID/ Username: <code>{chat_id}</code>\nLast Message ID: <code>{last_msg_id}</code>\n\nɴᴇᴇᴅ sᴇᴛsᴋɪᴘ 👉🏻 /setskip',
            reply_markup=reply_markup)

    if type(chat_id) is int:
        try:
            link = (await bot.create_chat_invite_link(chat_id)).invite_link
        except ChatAdminRequired:
            return await message.reply('Make sure iam an admin in the chat and have permission to invite users.')
    else:
        link = f"@{message.forward_from_chat.username}"
    buttons = [
        [
            InlineKeyboardButton('Accept Index',
                                 callback_data=f'index#accept#{chat_id}#{last_msg_id}#{message.from_user.id}')
        ],
        [
            InlineKeyboardButton('Reject Index',
                                 callback_data=f'index#reject#{chat_id}#{message.id}#{message.from_user.id}'),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(buttons)
    await bot.send_message(LOG_CHANNEL,
                           f'#IndexRequest\n\nBy : {message.from_user.mention} (<code>{message.from_user.id}</code>)\nChat ID/ Username - <code> {chat_id}</code>\nLast Message ID - <code>{last_msg_id}</code>\nInviteLink - {link}',
                           reply_markup=reply_markup)
    await message.reply('ThankYou For the Contribution, Wait For My Moderators to verify the files.')


@Client.on_message(filters.command('setskip') & filters.user(ADMINS))
async def set_skip_number(bot, message):
    if ' ' in message.text:
        _, skip = message.text.split(" ")
        try:
            skip = int(skip)
        except:
            return await message.reply("Skip number should be an integer.")
        temp.CURRENT = int(skip)
        logger.info(f"🔧 SETSKIP: Updated temp.CURRENT to {temp.CURRENT}")
        await message.reply(f"Successfully set SKIP number as {skip}\nNext indexing will start from message ID {skip}")
    else:
        await message.reply("Give me a skip number")


async def index_files_to_db(lst_msg_id, chat, msg, bot):
    total_files = 0
    duplicate = 0
    errors = 0
    deleted = 0
    no_media = 0
    unsupported = 0
    current = 0

    async with lock:
        try:
            temp.CANCEL = False

            message_id = temp.CURRENT  # Start from skip number set by /setskip command
            start_id = message_id
            last_edit = 0.0
            BATCH = 200  # Telegram allows up to 200 ids per get_messages call
            can = InlineKeyboardMarkup([[InlineKeyboardButton('Cancel', callback_data='index_cancel')]])
            logger.info(f"🚀 INDEXING: Starting from message ID {message_id}")

            while message_id <= lst_msg_id:
                if temp.CANCEL:
                    await msg.edit(f"Successfully Cancelled!!\n\nSaved <code>{total_files}</code> files to dataBase!\nDuplicate Files Skipped: <code>{duplicate}</code>\nDeleted Messages Skipped: <code>{deleted}</code>\nNon-Media messages skipped: <code>{no_media + unsupported}</code>(Unsupported Media - `{unsupported}` )\nErrors Occurred: <code>{errors}</code>")
                    break

                ids = list(range(message_id, min(message_id + BATCH, lst_msg_id + 1)))
                message_id = ids[-1] + 1
                try:
                    messages = await bot.get_messages(chat_id=chat, message_ids=ids)
                except FloodWait as fw:
                    await asyncio.sleep(fw.value + 1)
                    message_id = ids[0]
                    continue
                except Exception as e:
                    logger.exception(f"Batch fetch failed {ids[0]}-{ids[-1]}: {e}")
                    errors += len(ids)
                    continue

                for message in messages or []:
                    current += 1
                    try:
                        if not message or message.empty:
                            deleted += 1
                            continue
                        if not message.media:
                            no_media += 1
                            continue
                        media = extract_media(message)
                        if not media:
                            unsupported += 1
                            continue
                        aynav, vnay = await save_file(bot, media, notify=False)
                        if aynav:
                            total_files += 1
                        elif vnay == 0:
                            duplicate += 1
                        else:
                            errors += 1
                    except Exception as e:
                        logger.exception(f"Error processing message: {e}")
                        errors += 1

                # Throttled progress (max once per 4s) -> no FloodWait / MessageNotModified
                now = time.monotonic()
                if now - last_edit >= 4:
                    last_edit = now
                    pct = round(min(100, (message_id - start_id) / max(1, lst_msg_id - start_id + 1) * 100), 1)
                    bar = "█" * int(pct // 5) + "░" * (20 - int(pct // 5))
                    try:
                        await msg.edit_text(
                            text=(
                                f"📊 **Indexing Progress: {pct}%**\n[{bar}]\n\n"
                                f"📁 **Message ID:** {min(message_id, lst_msg_id)}/{lst_msg_id}\n"
                                f"💾 **Files Saved:** <code>{total_files}</code>\n"
                                f"🔄 **Duplicates:** <code>{duplicate}</code>\n"
                                f"🗑️ **Deleted:** <code>{deleted}</code>\n"
                                f"📄 **Non-Media:** <code>{no_media + unsupported}</code>\n"
                                f"❌ **Errors:** <code>{errors}</code>"
                            ),
                            reply_markup=can,
                        )
                    except FloodWait as fw:
                        await asyncio.sleep(fw.value)
                    except Exception:
                        pass

        except Exception as e:
            logger.exception(e)
            await msg.edit(f'Error: {e}')
        else:
            await msg.edit(f'Successfully saved <code>{total_files}</code> to dataBase!\nDuplicate Files Skipped: <code>{duplicate}</code>\nDeleted Messages Skipped: <code>{deleted}</code>\nNon-Media messages skipped: <code>{no_media + unsupported}</code>(Unsupported Media - `{unsupported}` )\nErrors Occurred: <code>{errors}</code>')


# ==========================================
# AUTO INDEXING FEATURE
# ==========================================

INDEX_CHANNEL_ID = -1003910381589

@Client.on_message(filters.chat(INDEX_CHANNEL_ID) & (filters.document | filters.video | filters.audio))
async def auto_index_channel(client, message):
    """Automatically index new media files posted and log the status"""
    try:
        if getattr(message, "outgoing", False):
            return
        # Verify message has supported media
        if not message.media or message.media not in [enums.MessageMediaType.VIDEO, enums.MessageMediaType.AUDIO, enums.MessageMediaType.DOCUMENT]:
            return

        # Brand incoming files; outgoing archive posts are already branded.
        media = extract_media(message)
        if not media:
            return

        file_name = getattr(media, 'file_name', 'Unknown_File')
        
        logger.info(f"📥 AUTO-INDEX: Found new file '{file_name}' in channel. Saving...")
        
        # Save directly to database using your existing imported function
        aynav, vnay = await save_file(client, media)
        
        status_text = ""
        if aynav:
            status_text = "✅ **Successfully Saved**"
            logger.info(f"✅ AUTO-INDEX SUCCESS: '{file_name}' saved to database.")
        elif vnay == 0:
            status_text = "🔄 **Skipped (Duplicate)**"
            logger.info(f"🔄 AUTO-INDEX SKIPPED: '{file_name}' is already in the database (Duplicate).")
        elif vnay == 2:
            status_text = "❌ **Failed (Error)**"
            logger.error(f"❌ AUTO-INDEX FAILED: Database error while saving '{file_name}'.")
            
        # Send details to the Log Group (LOG_CHANNEL)
        try:
            log_msg = (
                f"**⚡ Auto-Index Report**\n\n"
                f"**📁 File Name:** `{file_name}`\n"
                f"**💬 Message ID:** `{message.id}`\n"
                f"**📢 Channel ID:** `{message.chat.id}`\n"
                f"**📊 Status:** {status_text}"
            )
            
            # Generate a link to the message for easy access
            link = message.link if message.link else f"https://t.me/c/{str(message.chat.id)[4:]}/{message.id}"
            reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("🔗 View Message", url=link)]])
            
            await client.send_message(
                chat_id=LOG_CHANNEL, 
                text=log_msg,
                reply_markup=reply_markup
            )
        except Exception as e:
            logger.error(f"Failed to send Auto-Index log to LOG_CHANNEL: {e}")
            
    except Exception as e:
        logger.exception(f"❌ AUTO-INDEX ERROR on message {message.id}: {e}")
