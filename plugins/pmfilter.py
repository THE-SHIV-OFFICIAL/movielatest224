import asyncio
import re
import ast
import math
import random
import pytz
from datetime import datetime, timedelta, date, time
lock = asyncio.Lock()
from database.users_chats_db import db
from pyrogram.errors.exceptions.bad_request_400 import MediaEmpty, PhotoInvalidDimensions, WebpageMediaEmpty
from Script import script
import pyrogram
from database.connections_mdb import active_connection, all_connections, delete_connection, if_active, make_active, \
    make_inactive
from info import *
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, InputMediaPhoto, WebAppInfo
from pyrogram import Client, filters, enums
from pyrogram.errors import FloodWait, UserIsBlocked, MessageNotModified, PeerIdInvalid
from utils import get_size, is_subscribed, get_poster, search_gagala, temp, get_settings, save_group_settings, get_shortlink, get_tutorial, send_all, get_cap, imdb, get_tmdb_poster
from util.movie_display import movie_caption
from fuzzywuzzy import process
from database.config_db import mdb
from database.ia_filterdb import Media, Media2, get_file_details, get_search_results, get_bad_files
from database.filters_mdb import (
    del_all,
    find_filter,
    get_filters,
)
from database.gfilters_mdb import (
    find_gfilter,
    get_gfilters,
    del_allg
)
import logging
from urllib.parse import quote_plus
from util.file_properties import get_name, get_hash, get_media_file_size

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

# Search Logger Setup
search_log = logging.getLogger("searchLogger")

import requests
import string
import tracemalloc

tracemalloc.start()


TIMEZONE = "Asia/Kolkata"
BUTTON = {}
BUTTONS = {}
FRESH = {}
BUTTONS0 = {}
BUTTONS1 = {}
BUTTONS2 = {}
SPELL_CHECK = {}

# ==========================================
# 🌟 PREMIUM EMOJIS SETUP 🌟
# ==========================================
E_STAR = '<emoji id="6172611033694213759">⭐</emoji>'
E_MOVIE = '<emoji id="5375464961822695044">🎬</emoji>'
E_POP = '<emoji id="5873066287755695060">🍿</emoji>'
E_WARN = '<emoji id="6129782440157256336">⚠️</emoji>'
E_ROCKET = '<emoji id="6172332822892647766">🚀</emoji>'
E_CROWN = '<emoji id="6172370910662628916">👑</emoji>'
E_FIRE = '<emoji id="6170400139149055154">🔥</emoji>'
E_SPARKLE = '<emoji id="6125239923831217642">✨</emoji>'
E_SEARCH = '<emoji id="5429571366384842791">🔎</emoji>'
E_FILE = '<emoji id="5258514780469075716">📂</emoji>'
E_USER = '<emoji id="5258011929993026890">👤</emoji>'
E_TICK = '<emoji id="6280269890821558384">✅</emoji>'
E_CROSS = '<emoji id="6271611232457855630">❌</emoji>'
E_HEART = '<emoji id="6172491208401623963">🩷</emoji>'
E_TV = '<emoji id="6044356915029348425">📺</emoji>'
E_GEAR = '<emoji id="4965290516993278759">⚙️</emoji>'
E_WOW = '<emoji id="6190651601439428976">😍</emoji>'
E_TIME = '<emoji id="5408910404732595664">🕐</emoji>'
E_PIN = '<emoji id="6100424015111787987">📌</emoji>'
E_LINK = '<emoji id="5778455936410588193">🔗</emoji>'


def generate_random_alphanumeric():
    """Generate a random 8-letter alphanumeric string."""
    characters = string.ascii_letters + string.digits
    random_chars = ''.join(random.choice(characters) for _ in range(8))
    return random_chars

def get_shortlink_sync(url):
    try:
        rget = requests.get(f"https://{STREAM_SITE}/api?api={STREAM_API}&url={url}&alias={generate_random_alphanumeric()}")
        rjson = rget.json()
        if rjson["status"] == "success" or rget.status_code == 200:
            return rjson["shortenedUrl"]
        else:
            return url
    except Exception as e:
        print(f"Error in get_shortlink_sync: {e}")
        return url

async def get_shortlink(url):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, get_shortlink_sync, url)

# ==========================================
# 🚀 LOGGING FUNCTION
# ==========================================
async def send_search_log(client, message, search, total_results):
    try:
        is_avail = f"{E_TICK} <b>Aᴠᴀɪʟᴀʙʟᴇ</b>" if total_results > 0 else f"{E_CROSS} <b>Nᴏᴛ Aᴠᴀɪʟᴀʙʟᴇ</b>"

        user = message.from_user
        if user:
            user_mention = user.mention
            user_id = user.id
        else:
            user_mention = "Anonymous Admin"
            user_id = message.sender_chat.id if message.sender_chat else 0

        if message.chat.type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
            grp_name = message.chat.title
            grp_link = f"@{message.chat.username}" if message.chat.username else "Private Group"
            log_text = (
                f"{E_SEARCH} <b>#Nᴇᴡ_Gʀᴏᴜᴘ_Sᴇᴀʀᴄʜ</b>\n\n"
                f"👥 <b>Gʀᴏᴜᴘ:</b> {grp_name} ({grp_link})\n"
                f"{E_USER} <b>Usᴇʀ:</b> {user_mention} <code>[{user_id}]</code>\n"
                f"{E_MOVIE} <b>Mᴏᴠɪᴇ Sᴇᴀʀᴄʜᴇᴅ:</b> <code>{search}</code>\n"
                f"{E_FILE} <b>Sᴛᴀᴛᴜs:</b> {is_avail} ({total_results} Fɪʟᴇs)"
            )
        else:
            log_text = (
                f"{E_USER} <b>#Nᴇᴡ_Pʀɪᴠᴀᴛᴇ_Sᴇᴀʀᴄʜ (PM)</b>\n\n"
                f"{E_USER} <b>Usᴇʀ:</b> {user_mention} <code>[{user_id}]</code>\n"
                f"{E_MOVIE} <b>Mᴏᴠɪᴇ Sᴇᴀʀᴄʜᴇᴅ:</b> <code>{search}</code>\n"
                f"{E_FILE} <b>Sᴛᴀᴛᴜs:</b> {is_avail} ({total_results} Fɪʟᴇs)"
            )
        await client.send_message(LOG_CHANNEL, text=log_text, disable_web_page_preview=True)
    except Exception as e:
        logger.error(f"Failed to send search log to group: {e}")
# ==========================================

@Client.on_message(filters.group & filters.text & filters.incoming & ~filters.regex(r"^[/!]"))
async def give_filter(client, message):
    group_name = message.chat.title
    group_link = f"@{message.chat.username}" if message.chat.username else "No Username/Private Group"
    search_log.info(f"GROUP SEARCH | Group: {group_name} ({group_link}) | User: {message.from_user.first_name} [{message.from_user.id}] | Searched: {message.text}")

    if EMOJI_MODE:
        try:
            await message.react(emoji=random.choice(REACTIONS), big=True)
        except Exception as e:
            logger.error(f"Failed to react to message: {e}")
            pass
    await mdb.update_top_messages(message.from_user.id, message.text)
    if message.chat.id != SUPPORT_CHAT_ID:
        manual = await manual_filters(client, message)
        if manual == False:
            settings = await get_settings(message.chat.id)
            try:
                if settings['auto_ffilter']:
                    await auto_filter(client, message)
            except KeyError:
                grpid = await active_connection(str(message.from_user.id))
                await save_group_settings(grpid, 'auto_ffilter', True)
                settings = await get_settings(message.chat.id)
                if settings['auto_ffilter']:
                    await auto_filter(client, message) 
    else: 
        search = message.text
        temp_files, temp_offset, total_results = await get_search_results(chat_id=message.chat.id, query=search.lower(), offset=0, filter=True)

        # Log Bhejna for Support Chat
        await send_search_log(client, message, search, total_results)

        if total_results == 0:
            return
        else:
            return await message.reply_text(f"<b>Hᴇʏ {message.from_user.mention} {E_HEART},\n\nʏᴏᴜʀ ʀᴇǫᴜᴇsᴛ ɪꜱ ᴀʟʀᴇᴀᴅʏ ᴀᴠᴀɪʟᴀʙʟᴇ {E_TICK}\n\n{E_FILE} ꜰɪʟᴇꜱ ꜰᴏᴜɴᴅ : {str(total_results)}\n{E_SEARCH} ꜱᴇᴀʀᴄʜ :</b> <code>{search}</code>\n\n<b>{E_WARN} ᴛʜɪs ɪs ᴀ <u>sᴜᴘᴘᴏʀᴛ ɢʀᴏᴜᴘ</u> sᴏ ᴛʜᴀᴛ ʏᴏᴜ ᴄᴀɴ'ᴛ ɢᴇᴛ ғɪʟᴇs ғʀᴏᴍ ʜᴇʀᴇ...\n\n📝 ꜱᴇᴀʀᴄʜ ʜᴇʀᴇ : 👇</b>",   
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔍 ᴊᴏɪɴ ᴀɴᴅ ꜱᴇᴀʀᴄʜ ʜᴇʀᴇ 🔎", url=GRP_LNK)]]))

@Client.on_message(filters.private & filters.text & filters.incoming & ~filters.regex(r"^[/!]"))
async def pm_text(bot, message):
    bot_id = bot.me.id
    content = message.text
    user = message.from_user.first_name
    user_id = message.from_user.id

    search_log.info(f"DM SEARCH | User: {user} [{user_id}] | Searched: {content}")

    if EMOJI_MODE:
        try:
            await message.react(emoji=random.choice(REACTIONS), big=True)
        except Exception as e:
            logger.error(f"Failed to react to message: {e}")
            pass
    if content.startswith(("/", "#")):
        return  
    try:
        await mdb.update_top_messages(user_id, content)
        pm_search = await db.pm_search_status(bot_id)
        if pm_search:
            await auto_filter(bot, message)
        else:
            await message.reply_text(
             text=f"<b>🙋 ʜᴇʏ {user} {E_WOW} ,\n\n𝒀𝒐𝒖 𝒄𝒂𝒏 𝒔𝒆𝒂𝒓𝒄𝒉 𝒇𝒐𝒓 𝒎𝒐𝒗𝒊𝒆𝒔 𝒐𝒏𝒍𝒚 𝒐𝒏 𝒐𝒖𝒓 𝑴𝒐𝒗𝒊𝒆 𝑮𝒓𝒐𝒖𝒑. 𝒀𝒐𝒖 ᴀʀᴇ ɴᴏᴛ ᴀʟʟᴏᴡᴇᴅ ᴛᴏ ꜱᴇᴀʀᴄʜ ꜰᴏʀ ᴍᴏᴠɪᴇꜱ ᴏɴ ᴅɪʀᴇᴄᴛ ʙᴏᴛ. ᴘʟᴇᴀꜱᴇ ᴊᴏɪɴ ᴏᴜʀ ᴍᴏᴠɪᴇ ɢʀᴏᴜᴘ ʙʏ ᴄʟɪᴄᴋɪɴɢ ᴏɴ ᴛʜᴇ  ʀᴇǫᴜᴇꜱᴛ ʜᴇʀᴇ ʙᴜᴛᴛᴏɴ ɢɪᴠᴇɴ ʙᴇʟᴏᴡ ᴀɴᴅ ꜱᴇᴀʀᴄʜ ʏᴏᴜʀ ꜰᴀᴠᴏʀɪᴛᴇ ᴍᴏᴠɪᴇ ᴛʜᴇʀᴇ 👇\n\n<blockquote>आप केवल हमारे 𝑴𝒐𝒗𝒊𝒆 𝑮𝒓𝒐𝒖𝒑 पर ही 𝑴𝒐𝒗𝒊𝒆 𝑺𝒆𝒂𝒓𝒄𝒉 कर सकते हो । आपको 𝑫𝒊𝒓𝒆𝒄𝒕 𝑩𝒐𝒕 पर 𝑴𝒐𝒗𝒊𝒆 𝑺𝒆𝒂𝒓𝒄𝒉 करने की 𝑷𝒆𝒓𝒎𝒊𝒔𝒔𝒊𝒐𝒏 नहीं है कृपया नीचे दिए गए 𝑹𝑬𝑸𝑼𝑬𝑺𝑻 𝑯𝑬𝑹𝑬 वाले 𝑩𝒖ᴛᴛᴏɴ पर क्लिक करके हमारे 𝑴𝒐𝒗𝒊𝒆 𝑮𝒓𝒐𝒖𝒑 को  जৈoɪɴ करें और वहां पर अपनी मनपसंद 𝑴𝒐𝒗𝒊𝒆 𝑺𝒆𝒂𝒓𝒄𝒉 सर्च करें ।</blockquote></b>",   
             reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📝 ʀᴇǫᴜᴇsᴛ ʜᴇʀᴇ ", url=GRP_LNK)]])
            )
            await bot.send_message(
                chat_id=LOG_CHANNEL,
                text=f"<b>#𝐏𝐌_𝐌𝐒𝐆\n\n{E_USER} Nᴀᴍᴇ : {user}\n🆔 ID : {user_id}\n💬 Mᴇssᴀɢᴇ : {content}</b>"
            )
    except Exception as e:
        print(f"An error occurred: {str(e)}")

@Client.on_callback_query(filters.regex(r"^next"))
async def next_page(bot, query):
    ident, req, key, offset = query.data.split("_")
    curr_time = datetime.now(pytz.timezone('Asia/Kolkata')).time()
    if int(req) not in [query.from_user.id, 0]:
        return await query.answer(script.ALRT_TXT.format(query.from_user.first_name), show_alert=True)
    try:
        offset = int(offset)
    except:
        offset = 0
    if BUTTONS.get(key)!=None:
        search = BUTTONS.get(key)
    else:
        search = FRESH.get(key)
    if not search:
        await query.answer(script.OLD_ALRT_TXT.format(query.from_user.first_name),show_alert=True)
        return

    files, n_offset, total = await get_search_results(query.message.chat.id, search, offset=offset, filter=True)
    try:
        n_offset = int(n_offset)
    except:
        n_offset = 0

    if not files:
        return
    temp.GETALL[key] = files
    temp.SHORT[query.from_user.id] = query.message.chat.id
    settings = await get_settings(query.message.chat.id)
    pre = 'filep' if settings['file_secure'] else 'file'
    files = _sort_files_by_year(files)
    if settings['button']:
        btn = [
            [
                InlineKeyboardButton(
                    text=f"[{get_size(file.file_size)}] {' '.join(filter(lambda x: not x.startswith('[') and not x.startswith('@') and not x.startswith('www.'), file.file_name.split()))}", callback_data=f'{pre}#{file.file_id}'
                ),
            ]
            for file in files
        ]

        btn.insert(0, 
            [
                InlineKeyboardButton("⇈ Sᴇʟᴇᴄᴛ Oᴘᴛɪᴏɴ Hᴇʀᴇ ⇈", 'reqinfo')
            ]
        )
        btn.insert(0, 
            [ 
                InlineKeyboardButton("🎞️ Qᴜᴀʟɪᴛʏ", callback_data=f"qualities#{key}"),
                InlineKeyboardButton("🗣️ Lᴀɴɢᴜᴀɢᴇ", callback_data=f"languages#{key}"),
                InlineKeyboardButton("📺 Sᴇᴀsᴏɴ",  callback_data=f"seasons#{key}")
            ]
        )
        btn.insert(0, [
            InlineKeyboardButton("📤 Sᴇɴᴅ Aʟʟ", callback_data=f"sendfiles#{key}")
        ])

    else:
        btn = []
        btn.insert(0, 
            [
                InlineKeyboardButton("⇈ Sᴇʟᴇᴄᴛ Oᴘᴛɪᴏɴ Hᴇʀᴇ ⇈", 'reqinfo')
            ]
        )
        btn.insert(0, 
            [
                InlineKeyboardButton("🎞️ Qᴜᴀʟɪᴛʏ", callback_data=f"qualities#{key}"),
                InlineKeyboardButton("🗣️ Lᴀɴɢᴜᴀɢᴇ", callback_data=f"languages#{key}"),
                InlineKeyboardButton("📺 Sᴇᴀsᴏɴ",  callback_data=f"seasons#{key}")
            ]
        )
        btn.insert(0, [
            InlineKeyboardButton("📤 Sᴇɴᴅ Aʟʟ", callback_data=f"sendfiles#{key}")
        ])

    try:
        if settings['max_btn']:
            if 0 < offset <= 10:
                off_set = 0
            elif offset == 0:
                off_set = None
            else:
                off_set = offset - 10
            if n_offset == 0:
                btn.append(
                    [InlineKeyboardButton("⋞ ʙᴀᴄᴋ", callback_data=f"next_{req}_{key}_{off_set}"), InlineKeyboardButton(f"{math.ceil(int(offset)/10)+1} / {math.ceil(total/10)}", callback_data="pages")]
                )
            elif off_set is None:
                btn.append([InlineKeyboardButton("ᴘᴀɢᴇ", callback_data="pages"), InlineKeyboardButton(f"{math.ceil(int(offset)/10)+1} / {math.ceil(total/10)}", callback_data="pages"), InlineKeyboardButton("ɴᴇxᴛ ⋟", callback_data=f"next_{req}_{key}_{n_offset}")])
            else:
                btn.append(
                    [
                        InlineKeyboardButton("⋞ ʙᴀᴄᴋ", callback_data=f"next_{req}_{key}_{off_set}"),
                        InlineKeyboardButton(f"{math.ceil(int(offset)/10)+1} / {math.ceil(total/10)}", callback_data="pages"),
                        InlineKeyboardButton("ɴᴇxᴛ ⋟", callback_data=f"next_{req}_{key}_{n_offset}")
                    ],
                )
        else:
            if 0 < offset <= int(MAX_B_TN):
                off_set = 0
            elif offset == 0:
                off_set = None
            else:
                off_set = offset - int(MAX_B_TN)
            if n_offset == 0:
                btn.append(
                    [InlineKeyboardButton("⋞ ʙᴀᴄᴋ", callback_data=f"next_{req}_{key}_{off_set}"), InlineKeyboardButton(f"{math.ceil(int(offset)/int(MAX_B_TN))+1} / {math.ceil(total/int(MAX_B_TN))}", callback_data="pages")]
                )
            elif off_set is None:
                btn.append([InlineKeyboardButton("ᴘᴀɢᴇ", callback_data="pages"), InlineKeyboardButton(f"{math.ceil(int(offset)/int(MAX_B_TN))+1} / {math.ceil(total/int(MAX_B_TN))}", callback_data="pages"), InlineKeyboardButton("ɴᴇxᴛ ⋟", callback_data=f"next_{req}_{key}_{n_offset}")])
            else:
                btn.append(
                    [
                        InlineKeyboardButton("⋞ ʙᴀᴄᴋ", callback_data=f"next_{req}_{key}_{off_set}"),
                        InlineKeyboardButton(f"{math.ceil(int(offset)/int(MAX_B_TN))+1} / {math.ceil(total/int(MAX_B_TN))}", callback_data="pages"),
                        InlineKeyboardButton("ɴᴇxᴛ ⋟", callback_data=f"next_{req}_{key}_{n_offset}")
                    ],
                )
    except KeyError:
        await save_group_settings(query.message.chat.id, 'max_btn', True)
        if 0 < offset <= 10:
            off_set = 0
        elif offset == 0:
            off_set = None
        else:
            off_set = offset - 10
        if n_offset == 0:
            btn.append(
                [InlineKeyboardButton("⋞ ʙᴀᴄᴋ", callback_data=f"next_{req}_{key}_{off_set}"), InlineKeyboardButton(f"{math.ceil(int(offset)/10)+1} / {math.ceil(total/10)}", callback_data="pages")]
            )
        elif off_set is None:
            btn.append([InlineKeyboardButton("ᴘᴀɢᴇ", callback_data="pages"), InlineKeyboardButton(f"{math.ceil(int(offset)/10)+1} / {math.ceil(total/10)}", callback_data="pages"), InlineKeyboardButton("ɴᴇxᴛ ⋟", callback_data=f"next_{req}_{key}_{n_offset}")])
        else:
            btn.append(
                [
                    InlineKeyboardButton("⋞ ʙᴀᴄᴋ", callback_data=f"next_{req}_{key}_{off_set}"),
                    InlineKeyboardButton(f"{math.ceil(int(offset)/10)+1} / {math.ceil(total/10)}", callback_data="pages"),
                    InlineKeyboardButton("ɴᴇxᴛ ⋟", callback_data=f"next_{req}_{key}_{n_offset}")
                ],
            )
    if not settings["button"]:
        cur_time = datetime.now(pytz.timezone('Asia/Kolkata')).time()
        time_difference = timedelta(hours=cur_time.hour, minutes=cur_time.minute, seconds=(cur_time.second+(cur_time.microsecond/1000000))) - timedelta(hours=curr_time.hour, minutes=curr_time.minute, seconds=(curr_time.second+(curr_time.microsecond/1000000)))
        remaining_seconds = "{:.2f}".format(time_difference.total_seconds())
        cap = await get_cap(settings, remaining_seconds, files, query, total, search)
        try:
            await query.message.edit_text(text=cap, reply_markup=InlineKeyboardMarkup(btn), disable_web_page_preview=True)
        except MessageNotModified:
            pass
    else:
        try:
            await query.edit_message_reply_markup(
                reply_markup=InlineKeyboardMarkup(btn)
            )
        except MessageNotModified:
            pass
    await query.answer()

@Client.on_callback_query(filters.regex(r"^spol"))
async def advantage_spoll_choker(bot, query):
    _, id, user = query.data.split('#')
    if int(user) != 0 and query.from_user.id != int(user):
        return await query.answer(script.ALRT_TXT.format(query.from_user.first_name), show_alert=True)

    movies = await get_poster(id, id=True)
    movie = movies.get('title')
    movie = re.sub(r"[:-]", " ", movie)
    movie = re.sub(r"s+", " ", movie).strip()

    await query.answer(script.TOP_ALRT_MSG)
    gl = await global_filters(bot, query.message, text=movie)

    if gl == False:
        k = await manual_filters(bot, query.message, text=movie)

        if k == False:
            files, offset, total_results = await get_search_results(query.message.chat.id, movie, offset=0, filter=True)

            if files:
                k = (movie, files, offset, total_results)
                await auto_filter(bot, query, k)
            else:
                reqstr1 = query.from_user.id if query.from_user else 0
                reqstr = await bot.get_users(reqstr1)

                if NO_RESULTS_MSG:
                    await bot.send_message(chat_id=BIN_CHANNEL, text=(script.NORSLTS.format(reqstr.id, reqstr.mention, movie)))

                contact_admin_button = InlineKeyboardMarkup(
                    [[InlineKeyboardButton("🔰Cʟɪᴄᴋ ʜᴇʀᴇ & ʀᴇǫᴜᴇsᴛ ᴛᴏ ᴀᴅᴍɪɴ🔰", url=OWNER_LNK)]]
                )

                k = await query.message.edit(script.MVE_NT_FND, reply_markup=contact_admin_button)
                await asyncio.sleep(10)
                await k.delete()


# ==========================================
# QUALITY, LANGUAGE & SEASON / PART FILTERS
# Only options that really exist in the search results are shown.
# ==========================================
from util.file_filters import available as _available_options, apply_filters as _apply_filters, option_label as _option_label, sort_files_by_year as _sort_files_by_year

FILTERS = {}  # search key -> {"q": "720p", "l": "hindi", "s": "s1"}
_KIND_NAMES = {"q": ("🎞️", "Qᴜᴀʟɪᴛʏ"), "l": ("🗣️", "Lᴀɴɢᴜᴀɢᴇ"), "s": ("📺", "Sᴇᴀsᴏɴ / Pᴀʀᴛ")}
_KIND_BY_PREFIX = {"qualities": "q", "languages": "l", "seasons": "s", "fq": "q", "fl": "l", "fs": "s"}


def _not_owner(query):
    try:
        return int(query.from_user.id) not in [query.message.reply_to_message.from_user.id, 0]
    except Exception:
        return False


async def _all_files(key):
    search = FRESH.get(key) or BUTTONS.get(key)
    if not search:
        return None, None
    result = await get_bad_files(search.replace("_", " "))
    files = result[0] if isinstance(result, tuple) else (result or [])
    seen, unique = set(), []
    for f in files:
        if f.file_id not in seen:
            seen.add(f.file_id)
            unique.append(f)
    return search, unique


def _filter_row(key, active):
    def label(kind, short):
        icon, _ = _KIND_NAMES[kind]
        return f"✅ {_option_label(kind, active[kind])}" if kind in active else f"{icon} {short}"
    return [
        InlineKeyboardButton(label("q", "Qᴜᴀʟɪᴛʏ"), callback_data=f"qualities#{key}"),
        InlineKeyboardButton(label("l", "Lᴀɴɢᴜᴀɢᴇ"), callback_data=f"languages#{key}"),
        InlineKeyboardButton(label("s", "Sᴇᴀsᴏɴ"), callback_data=f"seasons#{key}"),
    ]


async def _show_filtered(query, key, offset=0):
    search, all_files = await _all_files(key)
    if search is None:
        return await query.answer("⚠️ Sᴇᴀʀᴄʜ ᴇxᴘɪʀᴇᴅ! Pʟᴇᴀsᴇ sᴇᴀʀᴄʜ ᴀɢᴀɪɴ.", show_alert=True)
    active = FILTERS.get(key, {})
    files = _apply_filters(all_files, active)
    if not files:
        return await query.answer("🚫 Iꜱ ꜰɪʟᴛᴇʀ ᴍᴇ ᴋᴏɪ ꜰɪʟᴇ ɴᴀʜɪ ᴍɪʟɪ 🚫", show_alert=True)
    settings = await get_settings(query.message.chat.id)
    per = 10 if settings.get('max_btn', True) else int(MAX_B_TN)
    total = len(files)
    offset = max(0, min(offset, (total - 1) // per * per))
    page = files[offset:offset + per]
    temp.GETALL[key] = page
    pre = 'filep' if settings['file_secure'] else 'file'

    btn = []
    if settings["button"]:
        btn = [[InlineKeyboardButton(
            text=f"📁 [{get_size(f.file_size)}] {' '.join(filter(lambda x: not x.startswith('[') and not x.startswith('@') and not x.startswith('www.'), f.file_name.split()))}",
            callback_data=f'{pre}#{f.file_id}')] for f in page]
    btn.insert(0, [InlineKeyboardButton("⇈ Sᴇʟᴇᴄᴛ Oᴘᴛɪᴏɴ Hᴇʀᴇ ⇈", 'reqinfo')])
    btn.insert(0, _filter_row(key, active))
    btn.insert(0, [InlineKeyboardButton("📤 Sᴇɴᴅ Aʟʟ", callback_data=f"sendfiles#{key}")])
    if active:
        btn.append([InlineKeyboardButton("♻️ Cʟᴇᴀʀ Fɪʟᴛᴇʀꜱ", callback_data=f"fclr#{key}")])

    pages = math.ceil(total / per)
    nav = []
    if offset > 0:
        nav.append(InlineKeyboardButton("⋞ ʙᴀᴄᴋ", callback_data=f"fpg#{key}#{offset - per}"))
    nav.append(InlineKeyboardButton(f"📄 {offset // per + 1} / {pages}", callback_data="pages"))
    if offset + per < total:
        nav.append(InlineKeyboardButton("ɴᴇxᴛ ⋟", callback_data=f"fpg#{key}#{offset + per}"))
    btn.append(nav)

    try:
        if not settings["button"]:
            cap = await get_cap(settings, "0.00", page, query, total, search)
            await query.message.edit_text(text=cap, reply_markup=InlineKeyboardMarkup(btn), disable_web_page_preview=True)
        else:
            await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(btn))
    except MessageNotModified:
        pass
    await query.answer()


@Client.on_callback_query(filters.regex(r"^(qualities|languages|seasons)#"))
async def filter_menu_cb_handler(client: Client, query: CallbackQuery):
    if _not_owner(query):
        return await query.answer(f"⚠️ ʜᴇʟʟᴏ {query.from_user.first_name},\nᴛʜɪꜱ ɪꜱ ɴᴏᴛ ʏᴏᴜʀ ᴍᴏᴠɪᴇ ʀᴇǫᴜᴇsᴛ,\nʀᴇǫᴜᴇsᴛ ʏᴏᴜʀ'ꜱ...", show_alert=True)
    prefix, key = query.data.split("#", 1)
    kind = _KIND_BY_PREFIX[prefix]
    search, all_files = await _all_files(key)
    if search is None:
        return await query.answer("⚠️ Sᴇᴀʀᴄʜ ᴇxᴘɪʀᴇᴅ! Pʟᴇᴀsᴇ sᴇᴀʀᴄʜ ᴀɢᴀɪɴ.", show_alert=True)
    active = FILTERS.get(key, {})
    others = {k: v for k, v in active.items() if k != kind}
    options = _available_options(_apply_filters(all_files, others), kind)
    icon, name = _KIND_NAMES[kind]
    if not options:
        return await query.answer(f"{icon} Iꜱ ᴍᴇ ᴋᴏɪ ᴀʟᴀɢ {name} ᴀᴠᴀɪʟᴀʙʟᴇ ɴᴀʜɪ ʜᴀɪ", show_alert=True)

    cb = {"q": "fq", "l": "fl", "s": "fs"}[kind]
    btn = [[InlineKeyboardButton(f"⇊ {icon} ꜱᴇʟᴇᴄᴛ {name} ⇊", callback_data="ident")]]
    row = []
    for value, label in options:
        if active.get(kind) == value:
            label = f"✅ {label}"
        row.append(InlineKeyboardButton(label, callback_data=f"{cb}#{value}#{key}"))
        if len(row) == 2:
            btn.append(row)
            row = []
    if row:
        btn.append(row)
    if kind in active:
        btn.append([InlineKeyboardButton("❌ Rᴇᴍᴏᴠᴇ Tʜɪꜱ Fɪʟᴛᴇʀ", callback_data=f"{cb}#clear#{key}")])
    btn.append([InlineKeyboardButton("⬅️ Bᴀᴄᴋ Tᴏ Fɪʟᴇꜱ", callback_data=f"fpg#{key}#0")])
    try:
        await query.edit_message_reply_markup(InlineKeyboardMarkup(btn))
    except MessageNotModified:
        pass
    await query.answer()


@Client.on_callback_query(filters.regex(r"^(fq|fl|fs)#"))
async def filter_pick_cb_handler(client: Client, query: CallbackQuery):
    if _not_owner(query):
        return await query.answer(f"⚠️ ʜᴇʟʟᴏ {query.from_user.first_name},\nᴛʜɪꜱ ɪꜱ ɴᴏᴛ ʏᴏᴜʀ ᴍᴏᴠɪᴇ ʀᴇǫᴜᴇsᴛ,\nʀᴇǫᴜᴇsᴛ ʏᴏᴜʀ'ꜱ...", show_alert=True)
    prefix, value, key = query.data.split("#", 2)
    kind = _KIND_BY_PREFIX[prefix]
    active = dict(FILTERS.get(key, {}))
    if value == "clear":
        active.pop(kind, None)
    elif value != "homepage":
        active[kind] = value
    FILTERS[key] = active
    await _show_filtered(query, key, 0)


@Client.on_callback_query(filters.regex(r"^fpg#"))
async def filter_page_cb_handler(client: Client, query: CallbackQuery):
    if _not_owner(query):
        return await query.answer(f"⚠️ ʜᴇʟʟᴏ {query.from_user.first_name},\nᴛʜɪꜱ ɪꜱ ɴᴏᴛ ʏᴏᴜʀ ᴍᴏᴠɪᴇ ʀᴇǫᴜᴇsᴛ,\nʀᴇǫᴜᴇsᴛ ʏᴏᴜʀ'ꜱ...", show_alert=True)
    _, key, offset = query.data.split("#", 2)
    try:
        offset = int(offset)
    except ValueError:
        offset = 0
    await _show_filtered(query, key, offset)


@Client.on_callback_query(filters.regex(r"^fclr#"))
async def filter_clear_cb_handler(client: Client, query: CallbackQuery):
    if _not_owner(query):
        return await query.answer(f"⚠️ ʜᴇʟʟᴏ {query.from_user.first_name},\nᴛʜɪꜱ ɪꜱ ɴᴏᴛ ʏᴏᴜʀ ᴍᴏᴠɪᴇ ʀᴇǫᴜᴇsᴛ,\nʀᴇǫᴜᴇsᴛ ʏᴏᴜʀ'ꜱ...", show_alert=True)
    key = query.data.split("#", 1)[1]
    FILTERS.pop(key, None)
    await _show_filtered(query, key, 0)

@Client.on_callback_query()
async def cb_handler(client: Client, query: CallbackQuery):
    lazyData = query.data
    try:
        link = await client.create_chat_invite_link(int(REQST_CHANNEL))
    except:
        pass
    if query.data == "close_data":
        await query.message.delete()
    elif query.data == "gfiltersdeleteallconfirm":
        await del_allg(query.message, 'gfilters')
        await query.answer("ᴅᴏɴᴇ !")
        return
    elif query.data == "gfiltersdeleteallcancel": 
        await query.message.reply_to_message.delete()
        await query.message.delete()
        await query.answer("ᴘʀᴏᴄᴇꜱꜱ ᴄᴀɴᴄᴇʟʟᴇᴅ !")
        return
    elif query.data == "delallconfirm":
        userid = query.from_user.id
        chat_type = query.message.chat.type

        if chat_type == enums.ChatType.PRIVATE:
            grpid = await active_connection(str(userid))
            if grpid is not None:
                grp_id = grpid
                try:
                    chat = await client.get_chat(grpid)
                    title = chat.title
                except:
                    await query.message.edit_text("Mᴀᴋᴇ sᴜʀᴇ I'ᴍ ᴘʀᴇsᴇɴᴛ ɪɴ ʏᴏᴜʀ ɢʀᴏᴜᴘ!!", quote=True)
                    return await query.answer(MSG_ALRT)
            else:
                await query.message.edit_text(
                    "I'ᴍ ɴᴏᴛ ᴄᴏɴɴᴇᴄᴛᴇᴅ ᴛᴏ ᴀɴʏ ɢʀᴏᴜᴘs !\nCʜᴇᴄᴋ /connections ᴏʀ ᴄᴏɴɴᴇᴄᴛ ᴛᴏ ᴀɴʏ ɢʀᴏᴜᴘs.",
                    quote=True
                )
                return await query.answer(MSG_ALRT)

        elif chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
            grp_id = query.message.chat.id
            title = query.message.chat.title

        else:
            return await query.answer(MSG_ALRT)

        st = await client.get_chat_member(grp_id, userid)
        if (st.status == enums.ChatMemberStatus.OWNER) or (str(userid) in ADMINS):
            await del_all(query.message, grp_id, title)
        else:
            await query.answer("Yᴏᴜ ɴᴇᴇᴅ ᴛᴏ ʙᴇ Gʀᴏᴜᴘ Oᴡɴᴇʀ ᴏʀ ᴀɴ Aᴜᴛʜ Usᴇʀ ᴛᴏ ᴅᴏ ᴛʜᴀᴛ !", show_alert=True)
    elif query.data == "delallcancel":
        userid = query.from_user.id
        chat_type = query.message.chat.type

        if chat_type == enums.ChatType.PRIVATE:
            await query.message.reply_to_message.delete()
            await query.message.delete()

        elif chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
            grp_id = query.message.chat.id
            st = await client.get_chat_member(grp_id, userid)
            if (st.status == enums.ChatMemberStatus.OWNER) or (str(userid) in ADMINS):
                await query.message.delete()
                try:
                    await query.message.reply_to_message.delete()
                except:
                    pass
            else:
                await query.answer("Tʜᴀᴛ's ɴᴏᴛ ғᴏʀ ʏᴏᴜ!!", show_alert=True)
    elif "groupcb" in query.data:
        await query.answer()

        group_id = query.data.split(":")[1]

        act = query.data.split(":")[2]
        hr = await client.get_chat(int(group_id))
        title = hr.title
        user_id = query.from_user.id

        if act == "":
            stat = "ᴄᴏɴɴᴇᴄᴛ"
            cb = "connectcb"
        else:
            stat = "ᴅɪꜱᴄᴏɴɴᴇᴄᴛ"
            cb = "disconnect"

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(f"{stat}", callback_data=f"{cb}:{group_id}"),
             InlineKeyboardButton("ᴅᴇʟᴇᴛᴇ", callback_data=f"deletecb:{group_id}")],
            [InlineKeyboardButton("ʙᴀᴄᴋ", callback_data="backcb")]
        ])

        await query.message.edit_text(
            f"Gʀᴏᴜᴘ Nᴀᴍᴇ : **{title}**\nGʀᴏᴜᴘ ID : `{group_id}`",
            reply_markup=keyboard,
            parse_mode=enums.ParseMode.MARKDOWN
        )
        return await query.answer(MSG_ALRT)
    elif "connectcb" in query.data:
        await query.answer()

        group_id = query.data.split(":")[1]

        hr = await client.get_chat(int(group_id))

        title = hr.title

        user_id = query.from_user.id

        mkact = await make_active(str(user_id), str(group_id))

        if mkact:
            await query.message.edit_text(
                f"Cᴏɴɴᴇᴄᴛᴇᴅ ᴛᴏ **{title}**",
                parse_mode=enums.ParseMode.MARKDOWN
            )
        else:
            await query.message.edit_text('Sᴏᴍᴇ ᴇʀʀᴏʀ ᴏᴄᴄᴜʀʀᴇᴅ!!', parse_mode=enums.ParseMode.MARKDOWN)
        return await query.answer(MSG_ALRT)
    elif "disconnect" in query.data:
        await query.answer()

        group_id = query.data.split(":")[1]

        hr = await client.get_chat(int(group_id))

        title = hr.title
        user_id = query.from_user.id

        mkinact = await make_inactive(str(user_id))

        if mkinact:
            await query.message.edit_text(
                f"Dɪsᴄᴏɴɴᴇᴄᴛᴇᴅ ғʀᴏᴍ **{title}**",
                parse_mode=enums.ParseMode.MARKDOWN
            )
        else:
            await query.message.edit_text(
                f"Sᴏᴍᴇ ᴇʀʀᴏʀ ᴏᴄᴄᴜʀʀᴇᴅ!!",
                parse_mode=enums.ParseMode.MARKDOWN
            )
        return await query.answer(MSG_ALRT)
    elif "deletecb" in query.data:
        await query.answer()

        user_id = query.from_user.id
        group_id = query.data.split(":")[1]

        delcon = await delete_connection(str(user_id), str(group_id))

        if delcon:
            await query.message.edit_text(
                "Sᴜᴄᴄᴇssғᴜʟʟʏ ᴅᴇʟᴇᴛᴇᴅ ᴄᴏɴɴᴇᴄᴛɪᴏɴ !"
            )
        else:
            await query.message.edit_text(
                f"Sᴏᴍᴇ ᴇʀʀᴏʀ ᴏᴄᴄᴜʀʀᴇᴅ!!",
                parse_mode=enums.ParseMode.MARKDOWN
            )
        return await query.answer(MSG_ALRT)
    elif query.data == "backcb":
        await query.answer()

        userid = query.from_user.id

        groupids = await all_connections(str(userid))
        if groupids is None:
            await query.message.edit_text(
                "Tʜᴇʀᴇ ᴀʀᴇ ɴᴏ ᴀᴄᴛɪᴠᴇ ᴄᴏɴɴᴇᴄᴛɪᴏɴs!! Cᴏɴɴᴇᴄᴛ ᴛᴏ sᴏᴍᴇ ɢʀᴏᴜᴘs ғɪʀsᴛ.",
            )
            return await query.answer(MSG_ALRT)
        buttons = []
        for groupid in groupids:
            try:
                ttl = await client.get_chat(int(groupid))
                title = ttl.title
                active = await if_active(str(userid), str(groupid))
                act = " - ACTIVE" if active else ""
                buttons.append(
                    [
                        InlineKeyboardButton(
                            text=f"{title}{act}", callback_data=f"groupcb:{groupid}:{act}"
                        )
                    ]
                )
            except:
                pass
        if buttons:
            await query.message.edit_text(
                "Yᴏᴜʀ ᴄᴏɴɴᴇᴄᴛᴇᴅ ɢʀᴏᴜᴘ ᴅᴇᴛᴀɪʟs ;\n\n",
                reply_markup=InlineKeyboardMarkup(buttons)
            )

    elif query.data.startswith("gfilteralert"):
        grp_id = query.message.chat.id
        i = query.data.split(":")[1]
        keyword = query.data.split(":")[2]
        reply_text, btn, alerts, fileid = await find_gfilter('gfilters', keyword)
        if alerts is not None:
            alerts = ast.literal_eval(alerts)
            alert = alerts[int(i)]
            alert = alert.replace("\\n", "\n").replace("\\t", "\t")
            await query.answer(alert, show_alert=True)

    elif query.data.startswith("alertmessage"):
        grp_id = query.message.chat.id
        i = query.data.split(":")[1]
        keyword = query.data.split(":")[2]
        reply_text, btn, alerts, fileid = await find_filter(grp_id, keyword)
        if alerts is not None:
            alerts = ast.literal_eval(alerts)
            alert = alerts[int(i)]
            alert = alert.replace("\\n", "\n").replace("\\t", "\t")
            await query.answer(alert, show_alert=True)

    elif query.data.startswith("file"):
        clicked = query.from_user.id
        try:
            typed = query.from_user.id
        except:
            typed = query.from_user.id
        ident, file_id = query.data.split("#")
        files_ = await get_file_details(file_id)
        if not files_:
            return await query.answer('Nᴏ sᴜᴄʜ ғɪʟᴇ ᴇxɪsᴛ.')
        files = files_[0]
        title = files.file_name
        size = get_size(files.file_size)
        f_caption = files.caption
        settings = await get_settings(query.message.chat.id)
        if CUSTOM_FILE_CAPTION:
            try:
                f_caption = CUSTOM_FILE_CAPTION.format(file_name='' if title is None else title,
                                                       file_size='' if size is None else size,
                                                       file_caption='' if f_caption is None else f_caption)
            except Exception as e:
                logger.exception(e)
            f_caption = f_caption
        if f_caption is None:
            f_caption = f"{files.file_name}"

        try:
            if settings['is_shortlink']:
                if clicked == query.from_user.id:
                    temp.SHORT[clicked] = query.message.chat.id
                    await query.answer(url=f"https://telegram.me/{temp.U_NAME}?start=short_{file_id}")
                    return
                else:
                    await query.answer(f"Hᴇʏ {query.from_user.first_name},\nTʜɪs Is Nᴏᴛ Yᴏᴜʀ Mᴏᴠɪᴇ Rᴇǫᴜᴇsᴛ.\nRᴇǫᴜᴇsᴛ Yᴏᴜʀ's !", show_alert=True)
            else:
                if clicked == query.from_user.id:
                    await query.answer(url=f"https://telegram.me/{temp.U_NAME}?start={ident}_{file_id}")
                    return
                else:
                    await query.answer(f"Hᴇʏ {query.from_user.first_name},\nTʜɪs Is Nᴏᴛ Yᴏᴜʀ Mᴏᴠɪᴇ Rᴇǫᴜᴇsᴛ.\nRᴇǫᴜᴇsᴛ Yᴏᴜʀ's !", show_alert=True)
        except UserIsBlocked:
            await query.answer('Uɴʙʟᴏᴄᴋ ᴛʜᴇ ʙᴏᴛ ᴍᴀʜɴ !', show_alert=True)
        except PeerIdInvalid:
            await query.answer(url=f"https://telegram.me/{temp.U_NAME}?start={ident}_{file_id}")
        except Exception as e:
            await query.answer(url=f"https://telegram.me/{temp.U_NAME}?start={ident}_{file_id}")

    elif query.data.startswith("sendfiles"):
        clicked = query.from_user.id
        ident, key = query.data.split("#")
        settings = await get_settings(query.message.chat.id)
        try:
            if settings.get('is_shortlink'):
                await query.answer(url=f"https://telegram.me/{temp.U_NAME}?start=sendfiles1_{key}")
                return
            else:
                await query.answer(url=f"https://telegram.me/{temp.U_NAME}?start=allfiles_{key}")
                return
        except UserIsBlocked:
            await query.answer('Uɴʙʟᴏᴄᴋ ᴛʜᴇ ʙᴏᴛ ᴍᴀʜɴ !', show_alert=True)
        except PeerIdInvalid:
            await query.answer(url=f"https://telegram.me/{temp.U_NAME}?start=sendfiles3_{key}")
        except Exception as e:
            logger.exception(e)
            await query.answer(url=f"https://telegram.me/{temp.U_NAME}?start=sendfiles4_{key}")


    elif query.data.startswith("del"):
        ident, file_id = query.data.split("#")
        files_ = await get_file_details(file_id)
        if not files_:
            return await query.answer('Nᴏ sᴜᴄʜ ғɪʟᴇ ᴇxɪsᴛ.')
        files = files_[0]
        title = files.file_name
        size = get_size(files.file_size)
        f_caption = files.caption
        settings = await get_settings(query.message.chat.id)
        if CUSTOM_FILE_CAPTION:
            try:
                f_caption = CUSTOM_FILE_CAPTION.format(file_name='' if title is None else title,
                                                       file_size='' if size is None else size,
                                                       file_caption='' if f_caption is None else f_caption)
            except Exception as e:
                logger.exception(e)
            f_caption = f_caption
        if f_caption is None:
            f_caption = f"{files.file_name}"
        await query.answer(url=f"https://telegram.me/{temp.U_NAME}?start=file_{file_id}")

    elif query.data.startswith("checksub"):
        ident, kk, file_id = query.data.split("#")
        channels = (await get_settings(int(query.from_user.id))).get('fsub')  
        if channels:
            btn = await is_subscribed(client, query, channels)
            if btn:
                await query.answer(
                    f"👋 Hello {query.from_user.first_name},\n\n"
                    "Yᴏᴜ ʜᴀᴠᴇ ɴᴏᴛ ᴊᴏɪɴᴇᴅ ᴀʟʟ ʀᴇǫᴜɪʀᴇᴅ ᴜᴘᴅᴀᴛᴇ Cʜᴀɴɴᴇʟs.\n"
                    "Pʟᴇᴀsᴇ ᴊᴏɪɴ ᴇᴀᴄʜ ᴄʜᴀɴɴᴇʟ ʟɪsᴛᴇᴅ ʙᴇʟᴏᴡ ᴀɴᴅ ᴛʀʏ ᴀɢᴀɪɴ.\n\n",
                    show_alert=True
                )
                btn.append([InlineKeyboardButton("♻️ ᴛʀʏ ᴀɢᴀɪɴ ♻️", callback_data=f"checksub#{kk}#{file_id}")])
                await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(btn))
                return
        await query.answer(url=f"https://t.me/{temp.U_NAME}?start={kk}_{file_id}")
        await query.message.delete()

    elif query.data == "pages":
        await query.answer()

    elif query.data.startswith("send_fsall"):
        temp_var, ident, key, offset = query.data.split("#")
        search = BUTTONS0.get(key)
        if not search:
            await query.answer(script.OLD_ALRT_TXT.format(query.from_user.first_name),show_alert=True)
            return
        files, n_offset, total = await get_search_results(query.message.chat.id, search, offset=int(offset), filter=True)
        await send_all(client, query.from_user.id, files, ident, query.message.chat.id, query.from_user.first_name, query)
        search = BUTTONS1.get(key)
        files, n_offset, total = await get_search_results(query.message.chat.id, search, offset=int(offset), filter=True)
        await send_all(client, query.from_user.id, files, ident, query.message.chat.id, query.from_user.first_name, query)
        search = BUTTONS2.get(key)
        files, n_offset, total = await get_search_results(query.message.chat.id, search, offset=int(offset), filter=True)
        await send_all(client, query.from_user.id, files, ident, query.message.chat.id, query.from_user.first_name, query)
        await query.answer(f"ʜᴇʏ {query.from_user.first_name}, ᴀʟʟ ꜰɪʟᴇꜱ ᴏɴ ᴛʜɪꜱ ᴘᴀɢᴇ ʜᴀꜱ ʙᴇᴇɴ ꜱᴇɴᴛ ꜱᴜᴄꜱꜱᴇꜱꜰᴜʟʟʏ ᴛᴏ ʏᴏᴜ ʙʏ ᴅᴍ !", show_alert=True)

    elif query.data.startswith("send_fall"):
        temp_var, ident, key, offset = query.data.split("#")
        if BUTTONS.get(key)!=None:
            search = BUTTONS.get(key)
        else:
            search = FRESH.get(key)
        if not search:
            await query.answer(script.OLD_ALRT_TXT.format(query.from_user.first_name),show_alert=True)
            return
        files, n_offset, total = await get_search_results(query.message.chat.id, search, offset=int(offset), filter=True)
        await send_all(client, query.from_user.id, files, ident, query.message.chat.id, query.from_user.first_name, query)
        await query.answer(f"ʜᴇʏ {query.from_user.first_name}, ᴀʟʟ ꜰɪʟᴇꜱ ᴏɴ ᴛʜɪꜱ ᴘᴀɢᴇ ʜᴀꜱ ʙᴇᴇɴ ꜱᴇɴᴛ ꜱᴜᴄꜱꜱᴇꜱꜰᴜʟʟʏ ᴛᴏ ʏᴏᴜ ʙʏ ᴅᴍ !", show_alert=True)

    elif query.data.startswith("killfilesdq"):
        ident, keyword = query.data.split("#")
        await query.message.edit_text(f"<b>{E_GEAR} Fetching Files for your query {keyword} on DB... Please wait...</b>")
        files, total = await get_bad_files(keyword)
        await query.message.edit_text(f"<b>{E_WARN} ꜰɪʟᴇ ᴅᴇʟᴇᴛᴇᴅ ᴘʀᴏᴄᴇꜱꜱ ᴡɪʟʟ ꜱᴛᴀʀᴛ ɪɴ 5 ꜱᴇᴄᴏɴᴅꜱ !</b>")
        await asyncio.sleep(5)
        deleted = 0
        async with lock:
            try:
                for file in files:
                    file_ids = file.file_id
                    file_name = file.file_name
                    result = await Media.collection.delete_one({
                        '_id': file_ids,
                    })
                    if not result.deleted_count:
                        result = await Media2.collection.delete_one({
                            '_id': file_ids,
                        })
                    if result.deleted_count:
                        logger.info(f'ꜰɪʟᴇ ꜰᴏᴜɴᴅ ꜰᴏʀ ʏᴏᴜʀ ǫᴜᴇʀʏ {keyword}! ꜱᴜᴄꜱꜱᴇꜱꜰᴜʟʟʏ ᴅᴇʟᴇᴛᴇᴅ {file_name} ꜰʀᴏᴍ ᴅᴀᴛᴀʙᴀsᴇ.')
                    deleted += 1
                    if deleted % 20 == 0:
                        await query.message.edit_text(f"<b>{E_GEAR} ᴘʀᴏᴄᴇꜱꜱ ꜱᴛᴀʀᴛᴇᴅ ꜰᴏʀ ᴅᴇʟᴇᴛɪɴɢ ꜰɪʟᴇꜱ ꜰʀᴏᴍ ᴅʙ. ꜱᴜᴄꜱꜱᴇꜱꜰᴜʟʟʏ ᴅᴇʟᴇᴛᴇᴅ {str(deleted)} ꜰɪʟᴇꜱ ꜰʀᴏᴍ ᴅʙ ꜰᴏʀ ʏᴏᴜʀ ǫᴜᴇʀʏ {keyword}.</b>\n\nᴘʟᴇᴀꜱᴇ ᴡᴀɪᴛ...</b>")
            except Exception as e:
                logger.exception(e)
                await query.message.edit_text(f'Error: {e}')
            else:
                await query.message.edit_text(f"<b>{E_TICK} ᴘʀᴏᴄᴇꜱꜱ ᴄᴏᴍᴘʟᴇᴛᴇᴅ ꜰᴏʀ ꜰɪʟᴇ ᴅᴇʟᴇᴛᴀᴛɪᴏɴ !\n\nꜱᴜᴄꜱꜱᴇꜱꜰᴜʟʟʏ ᴅᴇʟᴇᴛᴇᴅ {str(deleted)} ꜰɪʟᴇꜱ ꜰʀᴏᴍ ᴅʙ ꜰᴏʀ ʏᴏᴜʀ ǫᴜᴇʀʏ {keyword}.</b>")

    elif query.data.startswith("opnsetgrp"):
        ident, grp_id = query.data.split("#")
        userid = query.from_user.id if query.from_user else None
        st = await client.get_chat_member(grp_id, userid)
        if (
                st.status != enums.ChatMemberStatus.ADMINISTRATOR
                and st.status != enums.ChatMemberStatus.OWNER
                and str(userid) not in ADMINS
        ):
            await query.answer("ʏᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ ʀɪɢʜᴛs ᴛᴏ ᴅᴏ ᴛʜɪs !", show_alert=True)
            return
        title = query.message.chat.title
        settings = await get_settings(grp_id)
        if settings is not None:
            buttons = [
                [
                    InlineKeyboardButton('ʀᴇꜱᴜʟᴛ ᴘᴀɢᴇ',
                                         callback_data=f'setgs#button#{settings["button"]}#{str(grp_id)}'),
                    InlineKeyboardButton('ʙᴜᴛᴛᴏɴ' if settings["button"] else 'ᴛᴇxᴛ',
                                         callback_data=f'setgs#button#{settings["button"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('ꜰɪʟᴇ ꜱᴇɴᴅ ᴍᴏᴅᴇ', callback_data=f'setgs#botpm#{settings["botpm"]}#{str(grp_id)}'),
                    InlineKeyboardButton('ꜱᴛᴀʀᴛ' if settings["botpm"] else 'ᴀᴜᴛᴏ',
                                         callback_data=f'setgs#botpm#{settings["botpm"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('ꜰɪʟᴇ ꜱᴇᴄᴜʀᴇ',
                                         callback_data=f'setgs#file_secure#{settings["file_secure"]}#{str(grp_id)}'),
                    InlineKeyboardButton('ᴇɴᴀʙʟᴇ' if settings["file_secure"] else 'ᴅɪꜱᴀʙʟᴇ',
                                         callback_data=f'setgs#file_secure#{settings["file_secure"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('ɪᴍᴅʙ ᴘᴏꜱᴛᴇʀ', callback_data=f'setgs#imdb#{settings["imdb"]}#{str(grp_id)}'),
                    InlineKeyboardButton('ᴇɴᴀʙʟᴇ' if settings["imdb"] else 'ᴅɪꜱᴀʙʟᴇ',
                                         callback_data=f'setgs#imdb#{settings["imdb"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('ꜱᴘᴇʟʟ ᴄʜᴇᴄᴋ',
                                         callback_data=f'setgs#spell_check#{settings["spell_check"]}#{str(grp_id)}'),
                    InlineKeyboardButton('ᴇɴᴀʙʟᴇ' if settings["spell_check"] else 'ᴅɪꜱᴀʙʟᴇ',
                                         callback_data=f'setgs#spell_check#{settings["spell_check"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('ᴡᴇʟᴄᴏᴍᴇ ᴍꜱɢ', callback_data=f'setgs#welcome#{settings["welcome"]}#{str(grp_id)}'),
                    InlineKeyboardButton('ᴇɴᴀʙʟᴇ' if settings["welcome"] else 'ᴅɪꜱᴀʙʟᴇ',
                                         callback_data=f'setgs#welcome#{settings["welcome"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('ᴀᴜᴛᴏ ᴅᴇʟᴇᴛᴇ',
                                         callback_data=f'setgs#auto_delete#{settings["auto_delete"]}#{str(grp_id)}'),
                    InlineKeyboardButton('ᴇɴᴀʙʟᴇ' if settings["auto_delete"] else 'ᴅɪꜱᴀʙʟᴇ',
                                         callback_data=f'setgs#auto_delete#{settings["auto_delete"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('ᴀᴜᴛᴏ ꜰɪʟᴛᴇʀ',
                                         callback_data=f'setgs#auto_ffilter#{settings["auto_ffilter"]}#{str(grp_id)}'),
                    InlineKeyboardButton('ᴇɴᴀʙʟᴇ' if settings["auto_ffilter"] else 'ᴅɪꜱᴀʙʟᴇ',
                                         callback_data=f'setgs#auto_ffilter#{settings["auto_ffilter"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('ᴍᴀx ʙᴜᴛᴛᴏɴꜱ',
                                         callback_data=f'setgs#max_btn#{settings["max_btn"]}#{str(grp_id)}'),
                    InlineKeyboardButton('10' if settings["max_btn"] else f'{MAX_B_TN}',
                                         callback_data=f'setgs#max_btn#{settings["max_btn"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('ꜱʜᴏʀᴛʟɪɴᴋ',
                                         callback_data=f'setgs#is_shortlink#{settings["is_shortlink"]}#{str(grp_id)}'),
                    InlineKeyboardButton('ᴇɴᴀʙʟᴇ' if settings["is_shortlink"] else 'ᴅɪꜱᴀʙʟᴇ',
                                         callback_data=f'setgs#is_shortlink#{settings["is_shortlink"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('📡 FTM Gamma Mode',
                                         callback_data=f'setgs#ftm_gamma_mode#{settings.get("ftm_gamma_mode", False)}#{str(grp_id)}'),
                    InlineKeyboardButton('✅ Enabled' if settings.get("ftm_gamma_mode", False) else '❌ Disabled',
                                         callback_data=f'setgs#ftm_gamma_mode#{settings.get("ftm_gamma_mode", False)}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('⇋ ᴄʟᴏsᴇ ꜱᴇᴛᴛɪɴɢꜱ ᴍᴇɴᴜ ⇋', 
                                         callback_data='close_data'
                                         )
                ]
            ]
            reply_markup = InlineKeyboardMarkup(buttons)
            await query.message.edit_text(
                text=f"<b>{E_GEAR} ᴄʜᴀɴɢᴇ ʏᴏᴜʀ ꜱᴇᴛᴛɪɴɢꜱ ꜰᴏʀ {title} ᴀꜱ ʏᴏᴜ ᴡɪꜱʜ {E_SPARKLE}</b>",
                disable_web_page_preview=True,
                parse_mode=enums.ParseMode.HTML
            )
            await query.message.edit_reply_markup(reply_markup)

    elif query.data.startswith("opnsetpm"):
        ident, grp_id = query.data.split("#")
        userid = query.from_user.id if query.from_user else None
        st = await client.get_chat_member(grp_id, userid)
        if (
                st.status != enums.ChatMemberStatus.ADMINISTRATOR
                and st.status != enums.ChatMemberStatus.OWNER
                and str(userid) not in ADMINS
        ):
            await query.answer("Yᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ sᴜғғɪᴄɪᴀɴᴛ ʀɪɢʜᴛs ᴛᴏ ᴅᴏ ᴛʜɪs !", show_alert=True)
            return
        title = query.message.chat.title
        settings = await get_settings(grp_id)
        btn2 = [[
                 InlineKeyboardButton("ᴄʜᴇᴄᴋ ᴍʏ ᴅᴍ 🗳️", url=f"telegram.me/{temp.U_NAME}")
               ]]
        reply_markup = InlineKeyboardMarkup(btn2)
        await query.message.edit_text(f"<b>ʏᴏᴜʀ sᴇᴛᴛɪɴɢs ᴍᴇɴᴜ ғᴏʀ {title} ʜᴀs ʙᴇᴇɴ sᴇɴᴛ ᴛᴏ ʏᴏᴜ ʙʏ ᴅᴍ.</b>")
        await query.message.edit_reply_markup(reply_markup)
        if settings is not None:
            buttons = [
                [
                    InlineKeyboardButton('ʀᴇꜱᴜʟᴛ ᴘᴀɢᴇ',
                                         callback_data=f'setgs#button#{settings["button"]}#{str(grp_id)}'),
                    InlineKeyboardButton('ʙᴜᴛᴛᴏɴ' if settings["button"] else 'ᴛᴇxᴛ',
                                         callback_data=f'setgs#button#{settings["button"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('ꜰɪʟᴇ ꜱᴇɴᴅ ᴍᴏᴅᴇ', callback_data=f'setgs#botpm#{settings["botpm"]}#{str(grp_id)}'),
                    InlineKeyboardButton('ꜱᴛᴀʀᴛ' if settings["botpm"] else 'ᴀᴜᴛᴏ',
                                         callback_data=f'setgs#botpm#{settings["botpm"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('ꜰɪʟᴇ ꜱᴇᴄᴜʀᴇ',
                                         callback_data=f'setgs#file_secure#{settings["file_secure"]}#{str(grp_id)}'),
                    InlineKeyboardButton('ᴇɴᴀʙʟᴇ' if settings["file_secure"] else 'ᴅɪꜱᴀʙʟᴇ',
                                         callback_data=f'setgs#file_secure#{settings["file_secure"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('ɪᴍᴅʙ ᴘᴏꜱᴛᴇʀ', callback_data=f'setgs#imdb#{settings["imdb"]}#{str(grp_id)}'),
                    InlineKeyboardButton('ᴇɴᴀʙʟᴇ' if settings["imdb"] else 'ᴅɪꜱᴀʙʟᴇ',
                                         callback_data=f'setgs#imdb#{settings["imdb"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('ꜱᴘᴇʟʟ ᴄʜᴇᴄᴋ',
                                         callback_data=f'setgs#spell_check#{settings["spell_check"]}#{str(grp_id)}'),
                    InlineKeyboardButton('ᴇɴᴀʙʟᴇ' if settings["spell_check"] else 'ᴅɪꜱᴀʙʟᴇ',
                                         callback_data=f'setgs#spell_check#{settings["spell_check"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('ᴡᴇʟᴄᴏᴍᴇ ᴍꜱɢ', callback_data=f'setgs#welcome#{settings["welcome"]}#{str(grp_id)}'),
                    InlineKeyboardButton('ᴇɴᴀʙʟᴇ' if settings["welcome"] else 'ᴅɪꜱᴀʙʟᴇ',
                                         callback_data=f'setgs#welcome#{settings["welcome"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('ᴀᴜᴛᴏ ᴅᴇʟᴇᴛᴇ',
                                         callback_data=f'setgs#auto_delete#{settings["auto_delete"]}#{str(grp_id)}'),
                    InlineKeyboardButton('ᴇɴᴀʙʟᴇ' if settings["auto_delete"] else 'ᴅɪꜱᴀʙʟᴇ',
                                         callback_data=f'setgs#auto_delete#{settings["auto_delete"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('ᴀᴜᴛᴏ ꜰɪʟᴛᴇʀ',
                                         callback_data=f'setgs#auto_ffilter#{settings["auto_ffilter"]}#{str(grp_id)}'),
                    InlineKeyboardButton('ᴇɴᴀʙʟᴇ' if settings["auto_ffilter"] else 'ᴅɪꜱᴀʙʟᴇ',
                                         callback_data=f'setgs#auto_ffilter#{settings["auto_ffilter"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('ᴍᴀx ʙᴜᴛᴛᴏɴꜱ',
                                         callback_data=f'setgs#max_btn#{settings["max_btn"]}#{str(grp_id)}'),
                    InlineKeyboardButton('10' if settings["max_btn"] else f'{MAX_B_TN}',
                                         callback_data=f'setgs#max_btn#{settings["max_btn"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('ꜱʜᴏʀᴛʟɪɴᴋ',
                                         callback_data=f'setgs#is_shortlink#{settings["is_shortlink"]}#{str(grp_id)}'),
                    InlineKeyboardButton('ᴇɴᴀʙʟᴇ' if settings["is_shortlink"] else 'ᴅɪꜱᴀʙʟᴇ',
                                         callback_data=f'setgs#is_shortlink#{settings["is_shortlink"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('📡 FTM Gamma Mode',
                                         callback_data=f'setgs#ftm_gamma_mode#{settings.get("ftm_gamma_mode", False)}#{str(grp_id)}'),
                    InlineKeyboardButton('✅ Enabled' if settings.get("ftm_gamma_mode", False) else '❌ Disabled',
                                         callback_data=f'setgs#ftm_gamma_mode#{settings.get("ftm_gamma_mode", False)}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('⇋ ᴄʟᴏsᴇ ꜱᴇᴛᴛɪɴɢꜱ ᴍᴇɴᴜ ⇋', 
                                         callback_data='close_data'
                                         )
                ]
            ]
            reply_markup = InlineKeyboardMarkup(buttons)
            await client.send_message(
                chat_id=userid,
                text=f"<b>{E_GEAR} ᴄʜᴀɴɢᴇ ʏᴏᴜʀ ꜱᴇᴛᴛɪɴɢꜱ ꜰᴏʀ {title} ᴀꜱ ʏᴏᴜ ᴡɪꜱʜ {E_SPARKLE}</b>",
                reply_markup=reply_markup,
                disable_web_page_preview=True,
                parse_mode=enums.ParseMode.HTML,
                reply_to_message_id=query.message.id
            )

    elif query.data.startswith("show_option"):
        ident, from_user = query.data.split("#")
        btn = [[
                InlineKeyboardButton("⚠️ ᴜɴᴀᴠᴀɪʟᴀʙʟᴇ ⚠️", callback_data=f"unavailable#{from_user}"),
                InlineKeyboardButton("🟢 ᴜᴘʟᴏᴀᴅᴇᴅ 🟢", callback_data=f"uploaded#{from_user}")
             ],[
                InlineKeyboardButton("♻️ ᴀʟʀᴇᴀᴅʏ ᴀᴠᴀɪʟᴀʙʟᴇ ♻️", callback_data=f"already_available#{from_user}")
             ],[
                InlineKeyboardButton("📌 Not Released 📌", callback_data=f"Not_Released#{from_user}"),
                InlineKeyboardButton("♨️Type Correct Spelling♨️", callback_data=f"Type_Correct_Spelling#{from_user}")
             ],[
                InlineKeyboardButton("⚜️ Not Available In The Hindi ⚜️", callback_data=f"Not_Available_In_The_Hindi#{from_user}")
             ]]
        btn2 = [[
                 InlineKeyboardButton("ᴠɪᴇᴡ ꜱᴛᴀᴛᴜꜱ", url=f"{query.message.link}")
               ]]
        if query.from_user.id in ADMINS:
            user = await client.get_users(from_user)
            reply_markup = InlineKeyboardMarkup(btn)
            await query.message.edit_reply_markup(reply_markup)
            await query.answer("Hᴇʀᴇ ᴀʀᴇ ᴛʜᴇ ᴏᴘᴛɪᴏɴs !")
        else:
            await query.answer("Yᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ sᴜғғɪᴄɪᴀɴᴛ ʀɪɢʜᴛs ᴛᴏ ᴅᴏ ᴛʜɪs !", show_alert=True)

    elif query.data.startswith("unavailable"):
        ident, from_user = query.data.split("#")
        btn = [[
                InlineKeyboardButton("⚠️ ᴜɴᴀᴠᴀɪʟᴀʙʟᴇ ⚠️", callback_data=f"unalert#{from_user}")
              ]]
        btn2 = [[
                 InlineKeyboardButton('ᴊᴏɪɴ ᴄʜᴀɴɴᴇʟ', url=link.invite_link),
                 InlineKeyboardButton("ᴠɪᴇᴡ ꜱᴛᴀᴛᴜꜱ", url=f"{query.message.link}")
               ]]
        if query.from_user.id in ADMINS:
            user = await client.get_users(from_user)
            reply_markup = InlineKeyboardMarkup(btn)
            content = query.message.text
            await query.message.edit_text(f"<b><strike>{content}</strike></b>")
            await query.message.edit_reply_markup(reply_markup)
            await query.answer("Sᴇᴛ ᴛᴏ Uɴᴀᴠᴀɪʟᴀʙʟᴇ !")
            try:
                await client.send_message(chat_id=int(from_user), text=f"<u>{content}</u>\n\n<b>Hᴇʏ {user.mention}, Sᴏʀʀʏ Yᴏᴜʀ ʀᴇᴏ̨ᴜᴇsᴛ ɪs ᴜɴᴀᴠᴀɪʟᴀʙʟᴇ {E_WARN}. Sᴏ ᴏᴜʀ ᴍᴏᴅᴇʀᴀᴛᴏʀs ᴄᴀɴ'ᴛ ᴜᴘʟᴏᴀᴅ ɪᴛ.</b>", reply_markup=InlineKeyboardMarkup(btn2))
            except UserIsBlocked:
                await client.send_message(chat_id=int(SUPPORT_CHAT_ID), text=f"<u>{content}</u>\n\n<b>Hᴇʏ {user.mention}, Sᴏʀʀʏ Yᴏᴜʀ ʀᴇᴏ̨ᴜᴇsᴛ ɪs ᴜɴᴀᴠᴀɪʟᴀʙʟᴇ {E_WARN}. Sᴏ ᴏᴜʀ ᴍᴏᴅᴇʀᴀᴛᴏʀs ᴄᴀɴ'ᴛ ᴜᴘʟᴏᴀᴅ ɪᴛ.\n\nNᴏᴛᴇ: Tʜɪs ᴍᴇssᴀɢᴇ ɪs sᴇɴᴛ ᴛᴏ ᴛʜɪs ɢʀᴏᴜᴘ ʙᴇᴄᴀᴜsᴇ ʏᴏᴜ'ᴠᴇ ʙʟᴏᴄᴋᴇᴅ ᴛʜᴇ ʙᴏᴛ. Tᴏ sᴇɴᴅ ᴛʜɪs ᴍᴇssᴀɢᴇ ᴛᴏ ʏᴏᴜʀ PM, Mᴜsᴛ ᴜɴʙʟᴏᴄᴋ ᴛʜᴇ ʙᴏᴛ.</b>", reply_markup=InlineKeyboardMarkup(btn2))
        else:
            await query.answer("Yᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ sᴜғғɪᴄɪᴀɴᴛ ʀɪɢʜᴛs ᴛᴏ ᴅᴏ ᴛʜɪs !", show_alert=True)

    elif query.data.startswith("Not_Released"):
        ident, from_user = query.data.split("#")
        btn = [[
                InlineKeyboardButton("📌 Not Released 📌", callback_data=f"unalert#{from_user}")
              ]]
        btn2 = [[
                 InlineKeyboardButton('ᴊᴏɪɴ ᴄʜᴀɴɴᴇʟ', url=link.invite_link),
                 InlineKeyboardButton("ᴠɪᴇᴡ ꜱᴛᴀᴛᴜꜱ", url=f"{query.message.link}")
               ]]
        if query.from_user.id in ADMINS:
            user = await client.get_users(from_user)
            reply_markup = InlineKeyboardMarkup(btn)
            content = query.message.text
            await query.message.edit_text(f"<b><strike>{content}</strike></b>")
            await query.message.edit_reply_markup(reply_markup)
            await query.answer("Sᴇᴛ ᴛᴏ Uɴᴀᴠᴀɪʟᴀʙʟᴇ !")
            try:
                await client.send_message(chat_id=int(from_user), text=f"<u>{content}</u>\n\n<b>Hᴇʏ {user.mention}, The movie you requested has not been released yet {E_WARN}. Sᴏ ᴏᴜʀ ᴍᴏᴅᴇʀᴀᴛᴏʀs ᴄᴀɴ'ᴛ ᴜᴘʟᴏᴀᴅ ɪᴛ.</b>", reply_markup=InlineKeyboardMarkup(btn2))
            except UserIsBlocked:
                await client.send_message(chat_id=int(SUPPORT_CHAT_ID), text=f"<u>{content}</u>\n\n<b>Hᴇʏ {user.mention}, The movie you requested has not been released yet {E_WARN}. Sᴏ ᴏᴜʀ ᴍᴏᴅᴇʀᴀᴛᴏʀs ᴄᴀɴ'ᴛ ᴜᴘʟᴏᴀᴅ ɪᴛ.\n\nNᴏᴛᴇ: Tʜɪs ᴍᴇssᴀɢᴇ ɪs sᴇɴᴛ ᴛᴏ ᴛʜɪs ɢʀᴏᴜᴘ ʙᴇᴄᴀᴜsᴇ ʏᴏᴜ'ᴠᴇ ʙʟᴏᴄᴋᴇᴅ ᴛʜᴇ ʙᴏᴛ. Tᴏ sᴇɴᴅ ᴛʜɪs ᴍᴇssᴀɢᴇ ᴛᴏ ʏᴏᴜʀ PM, Mᴜsᴛ ᴜɴʙʟᴏᴄᴋ ᴛʜᴇ ʙᴏᴛ.</b>", reply_markup=InlineKeyboardMarkup(btn2))
        else:
            await query.answer("Yᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ sᴜғғɪᴄɪᴀɴᴛ ʀɪɢʜᴛs ᴛᴏ ᴅᴏ ᴛʜɪs !", show_alert=True)

    elif query.data.startswith("Type_Correct_Spelling"):
        ident, from_user = query.data.split("#")
        btn = [[
                InlineKeyboardButton("♨️ Type Correct Spelling ♨️", callback_data=f"unalert#{from_user}")
              ]]
        btn2 = [[
                 InlineKeyboardButton('ᴊᴏɪɴ ᴄʜᴀɴɴᴇʟ', url=link.invite_link),
                 InlineKeyboardButton("ᴠɪᴇᴡ ꜱᴛᴀᴛᴜꜱ", url=f"{query.message.link}")
               ]]
        if query.from_user.id in ADMINS:
            user = await client.get_users(from_user)
            reply_markup = InlineKeyboardMarkup(btn)
            content = query.message.text
            await query.message.edit_text(f"<b><strike>{content}</strike></b>")
            await query.message.edit_reply_markup(reply_markup)
            await query.answer("Sᴇᴛ ᴛᴏ Type Correct Spelling !")
            try:
                await client.send_message(chat_id=int(from_user), text=f"<u>{content}</u>\n\n<b>Hᴇʏ {user.mention}, The spelling of the movie you requested is incorrect {E_CROSS}. Please type the correct spelling of the movie name and try again.</b>", reply_markup=InlineKeyboardMarkup(btn2))
            except UserIsBlocked:
                await client.send_message(chat_id=int(SUPPORT_CHAT_ID), text=f"<u>{content}</u>\n\n<b>Hᴇʏ {user.mention}, The spelling of the movie you requested is incorrect {E_CROSS}. Please type the correct spelling of the movie name and try again.\n\nNᴏᴛᴇ: Tʜɪs ᴍᴇssᴀɢᴇ ɪs sᴇɴᴛ ᴛᴏ ᴛʜɪs ɢʀᴏᴜᴘ ʙᴇᴄᴀᴜsᴇ ʏᴏᴜ'ᴠᴇ ʙʟᴏᴄᴋᴇᴅ ᴛʜᴇ ʙᴏᴛ. Tᴏ sᴇɴᴅ ᴛʜɪs ᴍᴇssᴀɢᴇ ᴛᴏ ʏᴏᴜʀ PM, Mᴜsᴛ ᴜɴʙʟᴏᴄᴋ ᴛʜᴇ ʙᴏᴛ.</b>", reply_markup=InlineKeyboardMarkup(btn2))
        else:
            await query.answer("Yᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ sᴜғғɪᴄɪᴀɴᴛ ʀɪɢʜᴛs ᴛᴏ ᴅᴏ ᴛʜɪs !", show_alert=True)

    elif query.data.startswith("Not_Available_In_The_Hindi"):
        ident, from_user = query.data.split("#")
        btn = [[
                InlineKeyboardButton("⚜️ Not Available In The Hindi ⚜️", callback_data=f"unalert#{from_user}")
              ]]
        btn2 = [[
                 InlineKeyboardButton('ᴊᴏɪɴ ᴄʜᴀɴɴᴇʟ', url=link.invite_link),
                 InlineKeyboardButton("ᴠɪᴇᴡ ꜱᴛᴀᴛᴜꜱ", url=f"{query.message.link}")
               ]]
        if query.from_user.id in ADMINS:
            user = await client.get_users(from_user)
            reply_markup = InlineKeyboardMarkup(btn)
            content = query.message.text
            await query.message.edit_text(f"<b><strike>{content}</strike></b>")
            await query.message.edit_reply_markup(reply_markup)
            await query.answer("Sᴇᴛ ᴛᴏ Not Available In The Hindi  !")
            try:
                await client.send_message(chat_id=int(from_user), text=f"<u>{content}</u>\n\n<b>Hᴇʏ {user.mention}, Your request is not available in the Hindi language {E_CROSS}. Sᴏ ᴏᴜʀ ᴍᴏᴅᴇʀᴀᴛᴏʀs ᴄᴀɴ'ᴛ ᴜᴘʟᴏᴀᴅ ɪᴛ.</b>", reply_markup=InlineKeyboardMarkup(btn2))
            except UserIsBlocked:
                await client.send_message(chat_id=int(SUPPORT_CHAT_ID), text=f"<u>{content}</u>\n\n<b>Hᴇʏ {user.mention}, Your request is not available in the Hindi language {E_CROSS}. Sᴏ ᴏᴜʀ ᴍᴏᴅᴇʀᴀᴛᴏʀs ᴄᴀɴ'ᴛ ᴜᴘʟᴏᴀᴅ ɪᴛ.\n\nNᴏᴛᴇ: Tʜɪs ᴍᴇssᴀɢᴇ ɪs sᴇɴᴛ ᴛᴏ ᴛʜɪs ɢʀᴏᴜᴘ ʙᴇᴄᴀᴜsᴇ ʏᴏᴜ'ᴠᴇ ʙʟᴏᴄᴋᴇᴅ ᴛʜᴇ ʙᴏᴛ. Tᴏ sᴇɴᴅ ᴛʜɪs ᴍᴇssᴀɢᴇ ᴛᴏ ʏᴏᴜʀ PM, Mᴜsᴛ ᴜɴʙʟᴏᴄᴋ ᴛʜᴇ ʙᴏᴛ.</b>", reply_markup=InlineKeyboardMarkup(btn2))
        else:
            await query.answer("Yᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ sᴜғғɪᴄɪᴀɴᴛ ʀɪɢʜᴛs ᴛᴏ ᴅᴏ ᴛʜɪs !", show_alert=True)

    elif query.data.startswith("uploaded"):
        ident, from_user = query.data.split("#")
        btn = [[
                InlineKeyboardButton("🟢 ᴜᴘʟᴏᴀᴅᴇᴅ 🟢", callback_data=f"upalert#{from_user}")
              ]]
        btn2 = [[
                 InlineKeyboardButton('ᴊᴏɪɴ ᴄʜᴀɴɴᴇʟ', url=link.invite_link),
                 InlineKeyboardButton("ᴠɪᴇᴡ ꜱᴛᴀᴛᴜꜱ", url=f"{query.message.link}")
               ],[
                 InlineKeyboardButton("🔍 ꜱᴇᴀʀᴄʜ ʜᴇʀᴇ 🔎", url=GRP_LNK)
               ]]
        if query.from_user.id in ADMINS:
            user = await client.get_users(from_user)
            reply_markup = InlineKeyboardMarkup(btn)
            content = query.message.text
            await query.message.edit_text(f"<b><strike>{content}</strike></b>")
            await query.message.edit_reply_markup(reply_markup)
            await query.answer("Sᴇᴛ ᴛᴏ Uᴘʟᴏᴀᴅᴇᴅ !")
            try:
                await client.send_message(chat_id=int(from_user), text=f"<u>{content}</u>\n\n<b>Hᴇʏ {user.mention}, Yᴏᴜʀ ʀᴇᴏ̨ᴜᴇsᴛ ʜᴀs ʙᴇᴇɴ ᴜᴘʟᴏᴀᴅᴇᴅ {E_TICK} ʙʏ ᴏᴜʀ ᴍᴏᴅᴇʀᴀᴛᴏʀs. Kɪɴᴅʟʏ sᴇᴀʀᴄʜ ɪɴ ᴏᴜʀ Gʀᴏᴜᴘ.</b>", reply_markup=InlineKeyboardMarkup(btn2))
            except UserIsBlocked:
                await client.send_message(chat_id=int(SUPPORT_CHAT_ID), text=f"<u>{content}</u>\n\n<b>Hᴇʏ {user.mention}, Yᴏᴜʀ ʀᴇᴏ̨ᴜᴇsᴛ ʜᴀs ʙᴇᴇɴ ᴜᴘʟᴏᴀᴅᴇᴅ {E_TICK} ʙʏ ᴏᴜʀ ᴍᴏᴅᴇʀᴀᴛᴏʀs. Kɪɴᴅʟʏ sᴇᴀʀᴄʜ ɪɴ ᴏᴜʀ Gʀᴏᴜᴘ.\n\nNᴏᴛᴇ: Tʜɪs ᴍᴇssᴀɢᴇ ɪs sᴇɴᴛ ᴛᴏ ᴛʜɪs ɢʀᴏᴜᴘ ʙᴇᴄᴀᴜsᴇ ʏᴏᴜ'ᴠᴇ ʙʟᴏᴄᴋᴇᴅ ᴛʜᴇ ʙᴏᴛ. Tᴏ sᴇɴᴅ ᴛʜɪs ᴍᴇssᴀɢᴇ ᴛᴏ ʏᴏᴜʀ PM, Mᴜsᴛ ᴜɴʙʟᴏᴄᴋ ᴛʜᴇ ʙᴏᴛ.</b>", reply_markup=InlineKeyboardMarkup(btn2))
        else:
            await query.answer("Yᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ sᴜғғɪᴄɪᴀɴᴛ ʀɪɢʜᴛs ᴛᴏ ᴅᴏ ᴛʜɪs !", show_alert=True)

    elif query.data.startswith("already_available"):
        ident, from_user = query.data.split("#")
        btn = [[
                InlineKeyboardButton("♻️ ᴀʟʀᴇᴀᴅʏ ᴀᴠᴀɪʟᴀʙʟᴇ ♻️", callback_data=f"alalert#{from_user}")
              ]]
        btn2 = [[
                 InlineKeyboardButton('ᴊᴏɪɴ ᴄʜᴀɴɴᴇʟ', url=link.invite_link),
                 InlineKeyboardButton("ᴠɪᴇᴡ ꜱᴛᴀᴛᴜꜱ", url=f"{query.message.link}")
               ],[
                 InlineKeyboardButton("🔍 ꜱᴇᴀʀᴄʜ ʜᴇʀᴇ 🔎", url=GRP_LNK)
               ]]
        if query.from_user.id in ADMINS:
            user = await client.get_users(from_user)
            reply_markup = InlineKeyboardMarkup(btn)
            content = query.message.text
            await query.message.edit_text(f"<b><strike>{content}</strike></b>")
            await query.message.edit_reply_markup(reply_markup)
            await query.answer("Sᴇᴛ ᴛᴏ Aʟʀᴇᴀᴅʏ Aᴠᴀɪʟᴀʙʟᴇ !")
            try:
                await client.send_message(chat_id=int(from_user), text=f"<u>{content}</u>\n\n<b>Hᴇʏ {user.mention}, Yᴏᴜʀ ʀᴇᴏ̨ᴜᴇsᴛ ɪs ᴀʟʀᴇᴀᴅʏ ᴀᴠᴀɪʟᴀʙʟᴇ {E_FILE} ᴏɴ ᴏᴜʀ ʙᴏᴛ's ᴅᴀᴛᴀʙᴀsᴇ. Kɪɴᴅʟʏ sᴇᴀʀᴄʜ ɪɴ ᴏᴜʀ Gʀᴏᴜᴘ.</b>", reply_markup=InlineKeyboardMarkup(btn2))
            except UserIsBlocked:
                await client.send_message(chat_id=int(SUPPORT_CHAT_ID), text=f"<u>{content}</u>\n\n<b>Hᴇʏ {user.mention}, Yᴏᴜʀ ʀᴇᴏ̨ᴜᴇsᴛ ɪs ᴀʟʀᴇᴀᴅʏ ᴀᴠᴀɪʟᴀʙʟᴇ {E_FILE} ᴏɴ ᴏᴜʀ ʙᴏᴛ's ᴅᴀᴛᴀʙᴀsᴇ. Kɪɴᴅʟʏ sᴇᴀʀᴄʜ ɪɴ ᴏᴜʀ Gʀᴏᴜᴘ.\n\nNᴏᴛᴇ: Tʜɪs ᴍᴇssᴀɢᴇ ɪs sᴇɴᴛ ᴛᴏ ᴛʜɪs ɢʀᴏᴜᴘ ʙᴇᴄᴀᴜsᴇ ʏᴏᴜ'ᴠᴇ ʙʟᴏᴄᴋᴇᴅ ᴛʜᴇ ʙᴏᴛ. Tᴏ sᴇɴᴅ ᴛʜɪs ᴍᴇssᴀɢᴇ ᴛᴏ ʏᴏᴜʀ PM, Mᴜsᴛ ᴜɴʙʟᴏᴄᴋ ᴛʜᴇ ʙᴏᴛ.</b>", reply_markup=InlineKeyboardMarkup(btn2))
        else:
            await query.answer("Yᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ sᴜғғɪᴄɪᴀɴᴛ ʀɪɢʜᴛs ᴛᴏ ᴅᴏ ᴛʜɪs !", show_alert=True)

    elif query.data.startswith("alalert"):
        ident, from_user = query.data.split("#")
        if int(query.from_user.id) == int(from_user):
            user = await client.get_users(from_user)
            await query.answer(f"Hᴇʏ {user.first_name}, Yᴏᴜʀ Rᴇᴏ̨ᴜᴇsᴛ ɪs Aʟʀᴇᴀᴅʏ Aᴠᴀɪʟᴀʙʟᴇ !", show_alert=True)
        else:
            await query.answer("Yᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ sᴜғғɪᴄɪᴀɴᴛ ʀɪɢʜᴛs ᴛᴏ ᴅᴏ ᴛʜɪs !", show_alert=True)

    elif query.data.startswith("upalert"):
        ident, from_user = query.data.split("#")
        if int(query.from_user.id) == int(from_user):
            user = await client.get_users(from_user)
            await query.answer(f"Hᴇʏ {user.first_name}, Yᴏᴜʀ Rᴇᴏ̨ᴜᴇsᴛ ɪs Uᴘʟᴏᴀᴅᴇᴅ !", show_alert=True)
        else:
            await query.answer("Yᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ sᴜғғɪᴄɪᴀɴᴛ ʀɪɢʜᴛs ᴛᴏ ᴅᴏ ᴛʜɪs !", show_alert=True)

    elif query.data.startswith("unalert"):
        ident, from_user = query.data.split("#")
        if int(query.from_user.id) == int(from_user):
            user = await client.get_users(from_user)
            await query.answer(f"Hᴇʏ {user.first_name}, Yᴏᴜʀ Rᴇᴏ̨ᴜᴇsᴛ ɪs Uɴᴀᴠᴀɪʟᴀʙʟᴇ !", show_alert=True)
        else:
            await query.answer("Yᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ sᴜғғɪᴄɪᴀɴᴛ ʀɪɢʜᴛs ᴛᴏ ᴅᴏ ᴛʜɪs !", show_alert=True)


    elif lazyData.startswith("generate_stream_link"):
        _, file_id = lazyData.split(":")
        try:
            user_id = query.from_user.id
            username =  query.from_user.mention 

            log_msg = await client.send_cached_media(
                chat_id=LOG_CHANNEL,
                file_id=file_id,
            )
            fileName = {quote_plus(get_name(log_msg))}
            lazy_stream = f"{URL}watch/{str(log_msg.id)}/{quote_plus(get_name(log_msg))}?hash={get_hash(log_msg)}"
            lazy_download = f"{URL}{str(log_msg.id)}/{quote_plus(get_name(log_msg))}?hash={get_hash(log_msg)}"

            xo = await query.message.reply_text(f'💘')
            await asyncio.sleep(1)
            await xo.delete()

            await log_msg.reply_text(
                text=f"•• ʟɪɴᴋ ɢᴇɴᴇʀᴀᴛᴇᴅ ꜰᴏʀ ɪᴅ #{user_id} {E_TICK}\n•• ᴜꜱᴇʀɴᴀᴍᴇ : {username} \n\n•• ᖴᎥᒪᗴ Nᗩᗰᗴ : {fileName}",
                quote=True,
                disable_web_page_preview=True,
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🚀 Fast Download 🚀", url=lazy_download),  # we download Link
                                                    InlineKeyboardButton('🖥️ Watch online 🖥️', url=lazy_stream)]])  # web stream Link
            )
            ftmbotzx = await query.message.reply_text(
                text="•• ʟɪɴᴋ ɢᴇɴᴇʀᴀᴛᴇᴅ ☠︎⚔",
                quote=True,
                disable_web_page_preview=True,
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🚀 Fast Download 🚀", url=lazy_download),  # we download Link
                                                    InlineKeyboardButton('🖥️ Watch online 🖥️', url=lazy_stream)]])  # web stream Link
            )  

            await asyncio.sleep(120)  # Adjust the delay as needed
            await ftmbotzx.delete()
            return

        except Exception as e:
            print(e)  # print the error message
            await query.answer(f"⚠️ SOMETHING WENT WRONG \n\n{e}", show_alert=True)
            return

       #@ftmbotzx_dhakad

    elif query.data == "pagesn1":
        await query.answer(text=script.PAGE_TXT, show_alert=True)

    elif query.data == "reqinfo":
        await query.answer(text=script.REQINFO, show_alert=True)

    elif query.data == "select":
        await query.answer(text=script.SELECT, show_alert=True)

    elif query.data == "sinfo":
        await query.answer(text=script.SINFO, show_alert=True)

    elif query.data == "start":
        buttons = [[
                    InlineKeyboardButton('🔰 ᴀᴅᴅ ᴍᴇ ᴛᴏ ʏᴏᴜʀ ɢʀᴏᴜᴘ 🔰', url=f'http://telegram.me/{temp.U_NAME}?startgroup=true')
                ],[
                    InlineKeyboardButton('🕵️‍♂️ Tᴏᴘ Sᴇᴀʀᴄʜɪɴɢ', callback_data="topsearch"),
                    InlineKeyboardButton(' sᴜᴘᴘᴏʀᴛ 🔄', callback_data='channels')
                ],[
                    InlineKeyboardButton(' ʜᴇʟᴘ 🚨', callback_data='help'),
                    InlineKeyboardButton(' ᴀʙᴏᴜᴛ ❓ ', callback_data='about')
                ],[
                    InlineKeyboardButton('Eᴀʀɴ ᴍᴏɴᴇʏ..💲', callback_data="shortlink_info")
                ]]

        reply_markup = InlineKeyboardMarkup(buttons)
        current_time = datetime.now(pytz.timezone(TIMEZONE))
        curr_time = current_time.hour        
        if curr_time < 12:
            gtxt = "ɢᴏᴏᴅ ᴍᴏʀɴɪɴɢ 🌞" 
        elif curr_time < 17:
            gtxt = "ɢᴏᴏᴅ ᴀғᴛᴇʀɴᴏᴏɴ 🌓" 
        elif curr_time < 21:
            gtxt = "ɢᴏᴏᴅ ᴇᴠᴇɴɪɴɢ 🌘"
        else:
            gtxt = "ɢᴏᴏᴅ ɴɪɢʜᴛ 🌑"
        await client.edit_message_media(
            query.message.chat.id, 
            query.message.id, 
            InputMediaPhoto(random.choice(PICS))
        )
        await query.message.edit_text(
            text=script.START_TXT.format(query.from_user.mention, gtxt, temp.U_NAME, temp.B_NAME),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
        await query.answer(MSG_ALRT)

    elif query.data == "channels":
        buttons = [[
            InlineKeyboardButton('🎞 Mᴏᴠɪᴇ Gʀᴏᴜᴘ ', url=GRP_LNK),
            InlineKeyboardButton('☸️ ʙᴀᴄᴋᴜᴘ', url=CHNL_LNK)
        ],[
            InlineKeyboardButton('🗣📢 Mᴏᴠɪᴇ Nᴏᴛɪғɪᴄᴀᴛɪᴏɴ ', url=FTMBOTZX_MOVIE_UPDATE_CHANNEL_LNK),
        ],[
            InlineKeyboardButton('⇍ ʙᴀᴄᴋ ⇏', callback_data='start'),
            InlineKeyboardButton('➤ Cᴏɴᴛᴀᴄᴛ ', url=OWNER_LNK)
        ]] 
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.CHANNELS.format(query.from_user.mention),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )

    elif query.data == "users":
        buttons = [[
            InlineKeyboardButton('⇋ ʙᴀᴄᴋ ⇋', callback_data='help')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.USERS_TXT.format(query.from_user.mention),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )

    elif query.data == "group":
        buttons = [[
            InlineKeyboardButton('⇋ ʙᴀᴄᴋ ⇋', callback_data='help')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.GROUP_TXT.format(query.from_user.mention),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )


    elif query.data == "admic":
        if query.from_user.id not in ADMINS:
            return await query.answer("⚠️ ʏᴏᴜ'ʀᴇ ɴᴏᴛ ᴀ ʙᴏᴛ ᴀᴅᴍɪɴ !", show_alert=True)
        page = 0  
        buttons = [
            [InlineKeyboardButton('Next ➡️', callback_data=f'admic_next_{page}')],
            [InlineKeyboardButton('⇋ ʙᴀᴄᴋ ⇋', callback_data='help')]
        ]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=commands[page],  
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )

    elif query.data.startswith("admic_next_"):
        page = int(query.data.split('_')[-1]) + 1
        if page >= len(commands):
            page = len(commands) - 1

        buttons = []
        if page > 0:
            buttons.append(InlineKeyboardButton('Previous ⬅️', callback_data=f'admic_prev_{page}'))

        if page < len(commands) - 1:
            buttons.append(InlineKeyboardButton('Next ➡️', callback_data=f'admic_next_{page}'))

        reply_markup = InlineKeyboardMarkup([buttons, [InlineKeyboardButton('⇋ ʙᴀᴄᴋ ⇋', callback_data='help')]])
        await query.message.edit_text(
            text=commands[page],
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )

    elif query.data.startswith("admic_prev_"):
        page = int(query.data.split('_')[-1]) - 1
        if page < 0:
            page = 0  

        buttons = []
        if page > 0:
            buttons.append(InlineKeyboardButton('Previous ⬅️', callback_data=f'admic_prev_{page}'))

        if page < len(commands) - 1:
            buttons.append(InlineKeyboardButton('Next ➡️', callback_data=f'admic_next_{page}'))

        reply_markup = InlineKeyboardMarkup([buttons, [InlineKeyboardButton('⇋ ʙᴀᴄᴋ ⇋', callback_data='help')]])
        await query.message.edit_text(
            text=commands[page],
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )


    elif query.data == "help":
        buttons = [[
            InlineKeyboardButton('🛠️ Aᴅᴍɪɴ', callback_data='admic')
        ],[
            InlineKeyboardButton('👨🏻‍💼 ᴜꜱᴇʀ', callback_data='users'),
            InlineKeyboardButton('🤝 ɢʀᴏᴜᴘ', callback_data='group')
        ],[
            InlineKeyboardButton ('🎫 sᴛɪᴄᴋᴇʀ ɪᴅ', callback_data='sticker'),
            InlineKeyboardButton('🌿 ᴛᴇʟᴇɢʀᴀᴘʜ', callback_data='tele')
        ],[
            InlineKeyboardButton('🚩 ғᴏɴᴛ', callback_data='font'),
            InlineKeyboardButton('📋 Jsᴏɴ', callback_data='json')
        ],[
            InlineKeyboardButton('⇋ ʙᴀᴄᴋ ᴛᴏ ʜᴏᴍᴇ ⇋', callback_data='start')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.HELP_TXT.format(query.from_user.mention),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data == "about":
        buttons = [[
            InlineKeyboardButton('‼️ ᴅɪꜱᴄʟᴀɪᴍᴇʀ ‼️', callback_data='disclaimer'),
            InlineKeyboardButton ('🪔 sᴏᴜʀᴄᴇ', callback_data='source'),
        ],[
            InlineKeyboardButton('⇋ ʙᴀᴄᴋ ᴛᴏ ʜᴏᴍᴇ ⇋', callback_data='start')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.ABOUT_TXT.format(temp.U_NAME, temp.B_NAME, OWNER_LNK),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )

    elif query.data == "source":
        buttons = [[
            InlineKeyboardButton('Sᴏᴜʀᴄᴇ Cᴏᴅᴇ 📜', url='https://t.me/Hidden_Xman'),
            InlineKeyboardButton('⇋ ʙᴀᴄᴋ ⇋', callback_data='about')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.SOURCE_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )


    elif query.data == "json":
        buttons = [[
            InlineKeyboardButton('⇍ ʙᴀᴄᴋ ⇏', callback_data='help')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text="● ◌ ◌"
        )
        await query.message.edit_text(
            text="● ● ◌"
        )
        await query.message.edit_text(
            text="● ● ●"
        )
        reply_markup = InlineKeyboardMarkup(buttons)
        await client.edit_message_media(
            query.message.chat.id, 
            query.message.id, 
            InputMediaPhoto(random.choice(PICS))
        )
        await query.message.edit_text(
            text=(script.JSON_TXT),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )

    elif query.data == "sticker":
            btn = [[
                    InlineKeyboardButton("⇋ ʙᴀᴄᴋ ⇋", callback_data="help")                    
                  ]]
            await client.edit_message_media(
                query.message.chat.id, 
                query.message.id, 
                InputMediaPhoto(random.choice(PICS))
            )
            reply_markup = InlineKeyboardMarkup(btn)
            await query.message.edit_text(
                text=(script.STICKER_TXT),
                reply_markup=reply_markup,
                parse_mode=enums.ParseMode.HTML
        )
    elif query.data == "tele":
            btn = [[
                    InlineKeyboardButton("⟸ Bᴀᴄᴋ", callback_data="help"),
                    InlineKeyboardButton("Cᴏɴᴛᴀᴄᴛ", url=OWNER_LNK)
                  ]]
            await client.edit_message_media(
                query.message.chat.id, 
                query.message.id, 
                InputMediaPhoto(random.choice(PICS))
            )
            reply_markup = InlineKeyboardMarkup(btn)
            await query.message.edit_text(
                text=(script.TELE_TXT),
                reply_markup=reply_markup,
                parse_mode=enums.ParseMode.HTML
        )

    elif query.data == "font":
            btn = [[
                    InlineKeyboardButton("⇋ ʙᴀᴄᴋ ⇋", callback_data="help")
                  ]]
            await client.edit_message_media(
                query.message.chat.id, 
                query.message.id, 
                InputMediaPhoto(random.choice(PICS))
            )
            reply_markup = InlineKeyboardMarkup(btn)
            await query.message.edit_text(
                text=(script.FONT_TXT),
                reply_markup=reply_markup,
                parse_mode=enums.ParseMode.HTML
        )

    elif query.data == "shortlink_info":
            btn = [[
                    InlineKeyboardButton("1 / 3", callback_data="pagesn1"),
                    InlineKeyboardButton("ɴᴇxᴛ ⋟", callback_data="shortlink_info2")
                    ],[
                    InlineKeyboardButton('⇋ ʙᴀᴄᴋ ᴛᴏ ʜᴏᴍᴇ ⇋', callback_data='start')
                    ]]
            reply_markup = InlineKeyboardMarkup(btn)
            await query.message.edit_text(
                text=(script.SHORTLINK_INFO),
                reply_markup=reply_markup,
                parse_mode=enums.ParseMode.HTML
            )   
    elif query.data == "shortlink_info2":
            btn = [[
            InlineKeyboardButton("⋞ ʙᴀᴄᴋ", callback_data="shortlink_info"),
            InlineKeyboardButton("2 / 3", callback_data="pagesn1"),
            InlineKeyboardButton("ɴᴇxᴛ ⋟", callback_data="shortlink_info3")
            ],[
            InlineKeyboardButton('⇋ ʙᴀᴄᴋ ᴛᴏ ʜᴏᴍᴇ ⇋', callback_data='start')
            ]]
            reply_markup = InlineKeyboardMarkup(btn)
            await query.message.edit_text(
                text=(script.SHORTLINK_INFO2),
                reply_markup=reply_markup,
                parse_mode=enums.ParseMode.HTML
            )
    elif query.data == "shortlink_info3":
            btn = [[
            InlineKeyboardButton("⋞ ʙᴀᴄᴋ", callback_data="shortlink_info2"),
            InlineKeyboardButton("3 / 3", callback_data="pagesn1")
            ],[
            InlineKeyboardButton('⇋ ʙᴀᴄᴋ ᴛᴏ ʜᴏᴍᴇ ⇋', callback_data='start')
            ]]
            reply_markup = InlineKeyboardMarkup(btn)
            await query.message.edit_text(
                text=(script.SHORTLINK_INFO3),
                reply_markup=reply_markup,
                parse_mode=enums.ParseMode.HTML
            )   

    elif query.data == "disclaimer":
            btn = [[
                    InlineKeyboardButton("⇋ ʙᴀᴄᴋ ⇋", callback_data="about")
                  ]]
            reply_markup = InlineKeyboardMarkup(btn)
            await query.message.edit_text(
                text=(script.DISCLAIMER_TXT),
                reply_markup=reply_markup,
                parse_mode=enums.ParseMode.HTML 
            )
    elif query.data.startswith("setgs"):
        ident, set_type, status, grp_id = query.data.split("#")
        grpid = await active_connection(str(query.from_user.id))

        if str(grp_id) != str(grpid):
            await query.message.edit("Yᴏᴜʀ Aᴄᴛɪᴠᴇ Cᴏɴɴᴇᴄᴛɪᴏɴ Hᴀs Bᴇᴇɴ Cʜᴀɴɢᴇᴅ. Gᴏ Tᴏ /connections ᴀɴᴅ ᴄʜᴀɴɢᴇ ʏᴏᴜʀ ᴀᴄᴛɪᴠᴇ ᴄᴏɴɴᴇᴄᴛɪᴏɴ.")
            return await query.answer(MSG_ALRT)

        if set_type == 'is_shortlink' and query.from_user.id not in ADMINS:
            return await query.answer(text=f"Hey {query.from_user.first_name}, You can't change shortlink settings for your group !\n\nIt's an admin only setting !", show_alert=True)

        if status == "True":
            await save_group_settings(grpid, set_type, False)
        else:
            await save_group_settings(grpid, set_type, True)

        settings = await get_settings(grpid)

        if settings is not None:
            buttons = [
                [
                    InlineKeyboardButton('ʀᴇꜱᴜʟᴛ ᴘᴀɢᴇ',
                                         callback_data=f'setgs#button#{settings["button"]}#{str(grp_id)}'),
                    InlineKeyboardButton('ʙᴜᴛᴛᴏɴ' if settings["button"] else 'ᴛᴇxᴛ',
                                         callback_data=f'setgs#button#{settings["button"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('ꜰɪʟᴇ ꜱᴇɴᴅ ᴍᴏᴅᴇ', callback_data=f'setgs#botpm#{settings["botpm"]}#{str(grp_id)}'),
                    InlineKeyboardButton('ꜱᴛᴀʀᴛ' if settings["botpm"] else 'ᴀᴜᴛᴏ',
                                         callback_data=f'setgs#botpm#{settings["botpm"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('ꜰɪʟᴇ ꜱᴇᴄᴜʀᴇ',
                                         callback_data=f'setgs#file_secure#{settings["file_secure"]}#{str(grp_id)}'),
                    InlineKeyboardButton('ᴇɴᴀʙʟᴇ' if settings["file_secure"] else 'ᴅɪꜱᴀʙʟᴇ',
                                         callback_data=f'setgs#file_secure#{settings["file_secure"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('ɪᴍᴅʙ ᴘᴏꜱᴛᴇʀ', callback_data=f'setgs#imdb#{settings["imdb"]}#{str(grp_id)}'),
                    InlineKeyboardButton('ᴇɴᴀʙʟᴇ' if settings["imdb"] else 'ᴅɪꜱᴀʙʟᴇ',
                                         callback_data=f'setgs#imdb#{settings["imdb"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('ꜱᴘᴇʟʟ ᴄʜᴇᴄᴋ',
                                         callback_data=f'setgs#spell_check#{settings["spell_check"]}#{str(grp_id)}'),
                    InlineKeyboardButton('ᴇɴᴀʙʟᴇ' if settings["spell_check"] else 'ᴅɪꜱᴀʙʟᴇ',
                                         callback_data=f'setgs#spell_check#{settings["spell_check"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('ᴡᴇʟᴄᴏᴍᴇ ᴍꜱɢ', callback_data=f'setgs#welcome#{settings["welcome"]}#{str(grp_id)}'),
                    InlineKeyboardButton('ᴇɴᴀʙʟᴇ' if settings["welcome"] else 'ᴅɪꜱᴀʙʟᴇ',
                                         callback_data=f'setgs#welcome#{settings["welcome"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('ᴀᴜᴛᴏ ᴅᴇʟᴇᴛᴇ',
                                         callback_data=f'setgs#auto_delete#{settings["auto_delete"]}#{str(grp_id)}'),
                    InlineKeyboardButton('ᴇɴᴀʙʟᴇ' if settings["auto_delete"] else 'ᴅɪꜱᴀʙʟᴇ',
                                         callback_data=f'setgs#auto_delete#{settings["auto_delete"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('ᴀᴜᴛᴏ ꜰɪʟᴛᴇʀ',
                                         callback_data=f'setgs#auto_ffilter#{settings["auto_ffilter"]}#{str(grp_id)}'),
                    InlineKeyboardButton('ᴇɴᴀʙʟᴇ' if settings["auto_ffilter"] else 'ᴅɪꜱᴀʙʟᴇ',
                                         callback_data=f'setgs#auto_ffilter#{settings["auto_ffilter"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('ᴍᴀx ʙᴜᴛᴛᴏɴꜱ',
                                         callback_data=f'setgs#max_btn#{settings["max_btn"]}#{str(grp_id)}'),
                    InlineKeyboardButton('10' if settings["max_btn"] else f'{MAX_B_TN}',
                                         callback_data=f'setgs#max_btn#{settings["max_btn"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('ꜱʜᴏʀᴛʟɪɴᴋ',
                                         callback_data=f'setgs#is_shortlink#{settings["is_shortlink"]}#{str(grp_id)}'),
                    InlineKeyboardButton('ᴇɴᴀʙʟᴇ' if settings["is_shortlink"] else 'ᴅɪꜱᴀʙʟᴇ',
                                         callback_data=f'setgs#is_shortlink#{settings["is_shortlink"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('📡 FTM Gamma Mode',
                                         callback_data=f'setgs#ftm_gamma_mode#{settings.get("ftm_gamma_mode", False)}#{str(grp_id)}'),
                    InlineKeyboardButton('✅ Enabled' if settings.get("ftm_gamma_mode", False) else '❌ Disabled',
                                         callback_data=f'setgs#ftm_gamma_mode#{settings.get("ftm_gamma_mode", False)}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('⇋ ᴄʟᴏsᴇ ꜱᴇᴛᴛɪɴɢꜱ ᴍᴇɴᴜ ⇋', 
                                         callback_data='close_data'
                                         )
                ]
            ]
            reply_markup = InlineKeyboardMarkup(buttons)
            await query.message.edit_reply_markup(reply_markup)
    await query.answer(MSG_ALRT)


async def auto_filter(client, msg, spoll=False):
    curr_time = datetime.now(pytz.timezone('Asia/Kolkata')).time()

    if not spoll:
        message = msg
        if message.text.startswith("/"): return  # ignore commands
        if re.findall(r"((^\/|^,|^!|^\.|^[\U0001F600-\U000E007F]).*)", message.text):
            return
        if len(message.text) < 100:
            search = message.text         
            search = search.lower()

            # Check if FTM Gamma Mode is enabled for this group
            settings = await get_settings(message.chat.id)
            ftm_gamma_enabled = settings.get('ftm_gamma_mode', True)  # Default enabled

            # If gamma mode is enabled, respond with deep-link to PM
            if ftm_gamma_enabled and message.chat.type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
                # Replace spaces with hyphens for deep-link
                query_param = search.replace(" ", "-")

                # Create deep-link to PM for file download
                bot_username = temp.U_NAME.replace("@", "") if temp.U_NAME.startswith("@") else temp.U_NAME
                deep_link = f"https://t.me/{bot_username}?start=getfile-{query_param}"
                add_group_link = f"https://t.me/{bot_username}?startgroup=true"

                gamma_response = (
                    f"Hey 👋🏻 {message.from_user.first_name} "
                    f"{message.from_user.last_name or ''} ({message.from_user.id}) {E_WOW}\n\n"
                    f"🔖 Title : {message.text}\n"
                    f"📫 Your File is Ready Below 👇"
                )

                buttons = [
                    [InlineKeyboardButton("📥 Download File", url=deep_link)],
                    [InlineKeyboardButton("➕ Add Me to Your Group", url=add_group_link)]
                ]

                await message.reply_text(
                    gamma_response,
                    reply_markup=InlineKeyboardMarkup(buttons),
                    disable_web_page_preview=True
                )
                return

            m=await message.reply_text(f'<b>{E_SEARCH} sᴇᴀʀᴄʜɪɴɢ</b> <code>{search}</code>')
            find = search.split(" ")
            search = ""
            removes = ["in","upload", "series", "full", "horror", "thriller", "mystery", "print", "file"]
            for x in find:
                if x in removes:
                    continue
                else:
                    search = search + x + " "
            search = search.replace("-", " ")
            search = search.replace(":","")
            files, offset, total_results = await get_search_results(message.chat.id ,search, offset=0, filter=True)
            settings = await get_settings(message.chat.id)

            # Log Bhejna
            await send_search_log(client, message, search, total_results)

            if not files:
                if settings["spell_check"]:
                    ai_sts = await m.edit(f'{E_GEAR} ᴘʟᴇᴀꜱᴇ ᴡᴀɪᴛ, ᴀɪ ɪꜱ ᴄʜᴇᴄᴋɪɴɢ ʏᴏᴜʀ ꜱᴘᴇʟʟɪɴɢ...')
                    is_misspelled = await ai_spell_check(chat_id = message.chat.id,wrong_name=search)
                    if is_misspelled:
                        await ai_sts.edit(f'<b>{E_TICK} Aɪ Sᴜɢɢᴇsᴛᴇᴅ ᴍᴇ<code> {is_misspelled}</code> \nSᴏ Iᴍ Sᴇᴀʀᴄʜɪɴɢ ғᴏʀ <code>{is_misspelled}</code></b>')
                        await asyncio.sleep(2)
                        message.text = is_misspelled
                        await ai_sts.delete()
                        return await auto_filter(client, message)
                    await ai_sts.delete()
                    return await advantage_spell_chok(client, message)
        else:
            return
    else:
        message = msg.message.reply_to_message  # msg will be callback query
        search, files, offset, total_results = spoll
        m=await message.reply_text(f'<b>{E_SEARCH} sᴇᴀʀᴄʜɪɴɢ</b> <code>{search}</code>')
        settings = await get_settings(message.chat.id)
        await msg.message.delete()

        # Log Bhejna
        await send_search_log(client, message, search, total_results)

    pre = 'filep' if settings['file_secure'] else 'file'
    key = f"{message.chat.id}-{message.id}"
    FRESH[key] = search
    temp.GETALL[key] = files
    temp.SHORT[message.from_user.id] = message.chat.id
    files = _sort_files_by_year(files)
    if settings["button"]:
        btn = [
            [
                InlineKeyboardButton(
                    text=f"[{get_size(file.file_size)}] {' '.join(filter(lambda x: not x.startswith('[') and not x.startswith('@') and not x.startswith('www.'), file.file_name.split()))}", callback_data=f'{pre}#{file.file_id}'
                ),
            ]
            for file in files
        ]
        btn.insert(0, 
            [
                InlineKeyboardButton("⇈ Sᴇʟᴇᴄᴛ Oᴘᴛɪᴏɴ Hᴇʀᴇ ⇈", 'reqinfo')
            ]
        )
        btn.insert(0, 
            [
                InlineKeyboardButton("🎞️ Qᴜᴀʟɪᴛʏ", callback_data=f"qualities#{key}"),
                InlineKeyboardButton("🗣️ Lᴀɴɢᴜᴀɢᴇ", callback_data=f"languages#{key}"),
                InlineKeyboardButton("📺 Sᴇᴀsᴏɴ",  callback_data=f"seasons#{key}")
            ]
        )
        btn.insert(0, [
            InlineKeyboardButton("📤 Sᴇɴᴅ Aʟʟ", callback_data=f"sendfiles#{key}")
        ])

    else:
        btn = []
        btn.insert(0, 
            [
                InlineKeyboardButton("⇈ Sᴇʟᴇᴄᴛ Oᴘᴛɪᴏɴ Hᴇʀᴇ ⇈", 'reqinfo')
            ]
        )
        btn.insert(0, 
            [
                InlineKeyboardButton("🎞️ Qᴜᴀʟɪᴛʏ", callback_data=f"qualities#{key}"),
                InlineKeyboardButton("🗣️ Lᴀɴɢᴜᴀɢᴇ", callback_data=f"languages#{key}"),
                InlineKeyboardButton("📺 Sᴇᴀsᴏɴ",  callback_data=f"seasons#{key}")
            ]
        )
        btn.insert(0, [
            InlineKeyboardButton("📤 Sᴇɴᴅ Aʟʟ", callback_data=f"sendfiles#{key}")
        ])

    if offset != "":
        req = message.from_user.id if message.from_user else 0
        try:
            if settings['max_btn']:
                btn.append(
                    [InlineKeyboardButton("ᴘᴀɢᴇ", callback_data="pages"), InlineKeyboardButton(text=f"1/{math.ceil(int(total_results)/10)}",callback_data="pages"), InlineKeyboardButton(text="ɴᴇxᴛ ⋟",callback_data=f"next_{req}_{key}_{offset}")]
                )
            else:
                btn.append(
                    [InlineKeyboardButton("ᴘᴀɢᴇ", callback_data="pages"), InlineKeyboardButton(text=f"1/{math.ceil(int(total_results)/int(MAX_B_TN))}",callback_data="pages"), InlineKeyboardButton(text="ɴᴇxᴛ ⋟",callback_data=f"next_{req}_{key}_{offset}")]
                )
        except KeyError:
            await save_group_settings(message.chat.id, 'max_btn', True)
            btn.append(
                [InlineKeyboardButton("ᴘᴀɢᴇ", callback_data="pages"), InlineKeyboardButton(text=f"1/{math.ceil(int(total_results)/10)}",callback_data="pages"), InlineKeyboardButton(text="ɴᴇxᴛ ⋟",callback_data=f"next_{req}_{key}_{offset}")]
            )
    else:
        btn.append(
            [InlineKeyboardButton(text="↭ ɴᴏ ᴍᴏʀᴇ ᴘᴀɢᴇꜱ ᴀᴠᴀɪʟᴀʙʟᴇ ↭",callback_data="pages")]
        )
    imdb = await get_poster(search, file=(files[0]).file_name) if settings["imdb"] else None
    cur_time = datetime.now(pytz.timezone('Asia/Kolkata')).time()
    time_difference = timedelta(hours=cur_time.hour, minutes=cur_time.minute, seconds=(cur_time.second+(cur_time.microsecond/1000000))) - timedelta(hours=curr_time.hour, minutes=curr_time.minute, seconds=(cur_time.second+(cur_time.microsecond/1000000)))
    remaining_seconds = "{:.2f}".format(time_difference.total_seconds())
    TEMPLATE = script.IMDB_TEMPLATE_TXT
    if imdb:
        cap = TEMPLATE.format(
            qurey=search,
            title=imdb['title'],
            votes=imdb['votes'],
            aka=imdb["aka"],
            seasons=imdb["seasons"],
            box_office=imdb['box_office'],
            localized_title=imdb['localized_title'],
            kind=imdb['kind'],
            imdb_id=imdb["imdb_id"],
            cast=imdb["cast"],
            runtime=imdb["runtime"],
            countries=imdb["countries"],
            certificates=imdb["certificates"],
            languages=imdb["languages"],
            director=imdb["director"],
            writer=imdb["writer"],
            producer=imdb["producer"],
            composer=imdb["composer"],
            cinematographer=imdb["cinematographer"],
            music_team=imdb["music_team"],
            distributors=imdb["distributors"],
            release_date=imdb['release_date'],
            year=imdb['year'],
            genres=imdb['genres'],
            poster=imdb['poster'],
            plot=imdb['plot'],
            rating=imdb['rating'],
            url=imdb['url'],
            **locals()
        )
        temp.IMDB_CAP[message.from_user.id] = cap
        if not settings["button"]:
            cap+=f"\n\n<b>📚 <u>Your Requested Files</u> 👇\n\n</b>"
            for file in files:
                cap += f"<b>\n<a href='https://telegram.me/{temp.U_NAME}?start=files_{file.file_id}'> {E_FILE} {get_size(file.file_size)} ▷ {' '.join(filter(lambda x: not x.startswith('[') and not x.startswith('@') and not x.startswith('www.'), file.file_name.split()))}\n</a></b>"
    else:
        if settings["button"]:
            cap = f"<b>{E_TV} ᴛɪᴛʟᴇ : <code>{search}</code>\n{E_FILE} ᴛᴏᴛᴀʟ ꜰɪʟᴇꜱ : <code>{total_results}</code>\n{E_USER} ʀᴇǫᴜᴇsᴛᴇᴅ ʙʏ : {message.from_user.mention}\n{E_TIME} ʀᴇsᴜʟᴛ ɪɴ : <code>{remaining_seconds} Sᴇᴄᴏɴᴅs</code>\n\n{E_ROCKET} 𝑹𝒆𝒒𝒖𝒆𝒔𝒕𝒆ᴅ 𝑭ɪʟᴇ 👇 \n\n</b>"
        else:
            cap = f"<b>{E_TV} ᴛɪᴛʟᴇ : <code>{search}</code>\n{E_FILE} ᴛᴏᴛᴀʟ ꜰɪʟᴇꜱ : <code>{total_results}</code>\n{E_USER} ʀᴇǫᴜᴇsᴛᴇᴅ ʙʏ : {message.from_user.mention}\n{E_TIME} ʀᴇsᴜʟᴛ ɪɴ : <code>{remaining_seconds} Sᴇᴄᴏɴᴅs</code>\n\n{E_ROCKET} 𝑹𝒆𝒒𝒖𝒆𝒔𝒕𝒆ᴅ 𝑭ɪʟᴇ 👇 \n\n</b>"
            for file in files:
                cap += f"<b><a href='https://telegram.me/{temp.U_NAME}?start=files_{file.file_id}'> {E_FILE} {get_size(file.file_size)} ▷ {' '.join(filter(lambda x: not x.startswith('[') and not x.startswith('@') and not x.startswith('www.'), file.file_name.split()))}\n\n</a></b>"

    # TMDB posters belong to the exact matched release; all availability is file-backed.
    tmdb = None
    try:
        if TMDB_POSTER:
            tmdb = await get_tmdb_poster(search, filename=files[0].file_name)
    except Exception as e:
        logger.error(f"TMDB fetch failed: {e}")

    file_links = ""
    if tmdb:
        cap = movie_caption(tmdb, files, total_results)
        if not settings["button"]:
            from html import escape
            for file in files:
                name = escape(file.file_name or '')
                link = f"\n<a href='https://telegram.me/{temp.U_NAME}?start=files_{file.file_id}'>📁 {get_size(file.file_size)} ▷ {name}</a>"
                if len(file_links) + len(link) > 3000:
                    break
                file_links += link
    elif TMDB_POSTER:
        # Do not show an unrelated IMDb cover when TMDB could not confirm the title.
        cap += "\n\n🎞️ <b>Poster unavailable for this title</b>"

    posters = tmdb.get("posters", []) if tmdb else []
    if not TMDB_POSTER and imdb and imdb.get("poster"):
        posters = [imdb["poster"]]
    sent = None
    album = []
    extra_message = None
    if len(posters) > 1:
        try:
            album = await message.reply_media_group([
                InputMediaPhoto(media=url, caption=cap if index == 0 else None,
                                has_spoiler=POSTER_SPOILER)
                for index, url in enumerate(posters[:2])
            ])
            # Telegram albums cannot carry a button keyboard.
            sent = await message.reply_text("📂 <b>Available files</b>" + file_links, reply_markup=InlineKeyboardMarkup(btn))
        except Exception as e:
            logger.error(f"Poster album send failed: {e}")
            if album:
                for item in album:
                    try:
                        await item.delete()
                    except Exception:
                        pass
                album = []
    if sent is None and posters:
        try:
            sent = await message.reply_photo(
                photo=posters[0], caption=cap,
                has_spoiler=POSTER_SPOILER,
                reply_markup=InlineKeyboardMarkup(btn)
            )
            if file_links:
                extra_message = await message.reply_text("📂 <b>Available files</b>" + file_links)
        except Exception as e:
            logger.error(f"Poster send failed: {e}")
    if sent is None:
        sent = await message.reply_text(
            text=(cap + file_links)[:4096] if tmdb else cap[:4096], reply_markup=InlineKeyboardMarkup(btn),
            disable_web_page_preview=True
        )

    try:
        await m.delete()
    except Exception:
        pass

    try:
        await asyncio.sleep(DELETE_TIME)
        await sent.delete()
        for item in album:
            await item.delete()
        if extra_message:
            await extra_message.delete()
        await message.delete()
    except Exception as e:
        logger.error(f"Error in auto-delete: {e}")

async def ai_spell_check(chat_id, wrong_name):
    async def search_movie(wrong_name):
        search_results = imdb.search_movie(wrong_name)
        movie_list = [movie['title'] for movie in search_results]
        return movie_list
    movie_list = await search_movie(wrong_name)
    if not movie_list:
        return
    for _ in range(5):
        closest_match = process.extractOne(wrong_name, movie_list)
        if not closest_match or closest_match[1] <= 80:
            return 
        movie = closest_match[0]
        files, offset, total_results = await get_search_results(chat_id=chat_id, query=movie)
        if files:
            return movie
        movie_list.remove(movie)

async def advantage_spell_chok(client, message):
    mv_id = message.id
    search = message.text
    chat_id = message.chat.id
    settings = await get_settings(chat_id)
    query = re.sub(
        r"\b(pl(i|e)*?(s|z+|ease|se|ese|(e+)s(e)?)|((send|snd|giv(e)?|gib)(\sme)?)|movie(s)?|new|latest|br((o|u)h?)*|^h(e|a)?(l)*(o)*|mal(ayalam)?|t(h)?amil|file|that|find|und(o)*|kit(t(i|y)?)?o(w)?|thar(u)?(o)*w?|kittum(o)*|aya(k)*(um(o)*)?|full\smovie|any(one)|with\ssubtitle(s)?)",
        "", message.text, flags=re.IGNORECASE)
    query = query.strip() + " movie"
    try:
        movies = await get_poster(search, bulk=True)
    except:
        k = await message.reply(script.I_CUDNT.format(message.from_user.mention))
        await asyncio.sleep(60)
        await k.delete()
        try:
            await message.delete()
        except:
            pass
        return
    if not movies:
        google = search.replace(" ", "+")
        button = [[
            InlineKeyboardButton("🔍 ᴄʜᴇᴄᴋ ꜱᴘᴇʟʟɪɴɢ ᴏɴ ɢᴏᴏɢʟᴇ 🔍", url=f"https://www.google.com/search?q={google}")
        ]]
        k = await message.reply_text(text=script.I_CUDNT.format(search), reply_markup=InlineKeyboardMarkup(button))
        await asyncio.sleep(120)
        await k.delete()
        try:
            await message.delete()
        except:
            pass
        return
    user = message.from_user.id if message.from_user else 0
    buttons = [[
        InlineKeyboardButton(text=movie.get('title'), callback_data=f"spol#{movie.movieID}#{user}")
    ]
        for movie in movies
    ]
    buttons.append(
        [InlineKeyboardButton("🚫 ᴄʟᴏsᴇ 🚫", callback_data='close_data')]
    )
    d = await message.reply_text(text=script.CUDNT_FND.format(message.from_user.mention), reply_markup=InlineKeyboardMarkup(buttons), reply_to_message_id=message.id)
    await asyncio.sleep(120)
    await d.delete()
    try:
        await message.delete()
    except:
        pass


async def manual_filters(client, message, text=False):
    settings = await get_settings(message.chat.id)
    group_id = message.chat.id
    name = text or message.text
    reply_id = message.reply_to_message.id if message.reply_to_message else message.id
    keywords = await get_filters(group_id)
    for keyword in reversed(sorted(keywords, key=len)):
        pattern = r"( |^|[^\w])" + re.escape(keyword) + r"( |$|[^\w])"
        if re.search(pattern, name, flags=re.IGNORECASE):
            reply_text, btn, alert, fileid = await find_filter(group_id, keyword)

            if reply_text:
                reply_text = reply_text.replace("\\n", "\n").replace("\\t", "\t")

            if btn is not None:
                try:
                    if fileid == "None":
                        if btn == "[]":
                            joelkb = await client.send_message(
                                group_id, 
                                reply_text, 
                                disable_web_page_preview=True,
                                protect_content=True if settings["file_secure"] else False,
                                reply_to_message_id=reply_id
                            )
                            manual = await manual_filters(client, message)
                            if manual == False:
                                settings = await get_settings(message.chat.id)
                                try:
                                    if settings['auto_ffilter']:
                                        await auto_filter(client, message)
                                        try:
                                            if settings['auto_delete']:
                                                await joelkb.delete()
                                        except KeyError:
                                            grpid = await active_connection(str(message.from_user.id))
                                            await save_group_settings(grpid, 'auto_delete', True)
                                            settings = await get_settings(message.chat.id)
                                            if settings['auto_delete']:
                                                await joelkb.delete()
                                    else:
                                        try:
                                            if settings['auto_delete']:
                                                await asyncio.sleep(600)
                                                await joelkb.delete()
                                        except KeyError:
                                            grpid = await active_connection(str(message.from_user.id))
                                            await save_group_settings(grpid, 'auto_delete', True)
                                            settings = await get_settings(message.chat.id)
                                            if settings['auto_delete']:
                                                await asyncio.sleep(600)
                                                await joelkb.delete()
                                except KeyError:
                                    grpid = await active_connection(str(message.from_user.id))
                                    await save_group_settings(grpid, 'auto_ffilter', True)
                                    settings = await get_settings(message.chat.id)
                                    if settings['auto_ffilter']:
                                        await auto_filter(client, message) 
                            else:
                                try:
                                    if settings['auto_delete']:
                                        await joelkb.delete()
                                except KeyError:
                                    grpid = await active_connection(str(message.from_user.id))
                                    await save_group_settings(grpid, 'auto_delete', True)
                                    settings = await get_settings(message.chat.id)
                                    if settings['auto_delete']:
                                        await joelkb.delete()

                        else:
                            button = eval(btn)
                            joelkb = await client.send_message(
                                group_id,
                                reply_text,
                                disable_web_page_preview=True,
                                reply_markup=InlineKeyboardMarkup(button),
                                protect_content=True if settings["file_secure"] else False,
                                reply_to_message_id=reply_id
                            )
                            manual = await manual_filters(client, message)
                            if manual == False:
                                settings = await get_settings(message.chat.id)
                                try:
                                    if settings['auto_ffilter']:
                                        await auto_filter(client, message)
                                        try:
                                            if settings['auto_delete']:
                                                await joelkb.delete()
                                        except KeyError:
                                            grpid = await active_connection(str(message.from_user.id))
                                            await save_group_settings(grpid, 'auto_delete', True)
                                            settings = await get_settings(message.chat.id)
                                            if settings['auto_delete']:
                                                await joelkb.delete()
                                    else:
                                        try:
                                            if settings['auto_delete']:
                                                await asyncio.sleep(600)
                                                await joelkb.delete()
                                        except KeyError:
                                            grpid = await active_connection(str(message.from_user.id))
                                            await save_group_settings(grpid, 'auto_delete', True)
                                            settings = await get_settings(message.chat.id)
                                            if settings['auto_delete']:
                                                await asyncio.sleep(600)
                                                await joelkb.delete()
                                except KeyError:
                                    grpid = await active_connection(str(message.from_user.id))
                                    await save_group_settings(grpid, 'auto_ffilter', True)
                                    settings = await get_settings(message.chat.id)
                                    if settings['auto_ffilter']:
                                        await auto_filter(client, message) 
                            else:
                                try:
                                    if settings['auto_delete']:
                                        await joelkb.delete()
                                except KeyError:
                                    grpid = await active_connection(str(message.from_user.id))
                                    await save_group_settings(grpid, 'auto_delete', True)
                                    settings = await get_settings(message.chat.id)
                                    if settings['auto_delete']:
                                        await joelkb.delete()


                except Exception as e:
                    logger.exception(e)
            break
    else:
        return False

async def global_filters(client, message, text=False):
    settings = await get_settings(message.chat.id)
    group_id = message.chat.id
    name = text or message.text
    reply_id = message.reply_to_message.id if message.reply_to_message else message.id
    keywords = await get_gfilters('gfilters')
    for keyword in reversed(sorted(keywords, key=len)):
        pattern = r"( |^|[^\w])" + re.escape(keyword) + r"( |$|[^\w])"
        if re.search(pattern, name, flags=re.IGNORECASE):
            reply_text, btn, alert, fileid = await find_gfilter('gfilters', keyword)

            if reply_text:
                reply_text = reply_text.replace("\\n", "\n").replace("\\t", "\t")

            if btn is not None:
                try:
                    if fileid == "None":
                        if btn == "[]":
                            joelkb = await client.send_message(
                                group_id, 
                                reply_text, 
                                disable_web_page_preview=True,
                                reply_to_message_id=reply_id
                            )
                            manual = await manual_filters(client, message)
                            if manual == False:
                                settings = await get_settings(message.chat.id)
                                try:
                                    if settings['auto_ffilter']:
                                        await auto_filter(client, message)
                                        try:
                                            if settings['auto_delete']:
                                                await joelkb.delete()
                                        except KeyError:
                                            grpid = await active_connection(str(message.from_user.id))
                                            await save_group_settings(grpid, 'auto_delete', True)
                                            settings = await get_settings(message.chat.id)
                                            if settings['auto_delete']:
                                                await joelkb.delete()
                                    else:
                                        try:
                                            if settings['auto_delete']:
                                                await asyncio.sleep(600)
                                                await joelkb.delete()
                                        except KeyError:
                                            grpid = await active_connection(str(message.from_user.id))
                                            await save_group_settings(grpid, 'auto_delete', True)
                                            settings = await get_settings(message.chat.id)
                                            if settings['auto_delete']:
                                                await asyncio.sleep(600)
                                                await joelkb.delete()
                                except KeyError:
                                    grpid = await active_connection(str(message.from_user.id))
                                    await save_group_settings(grpid, 'auto_ffilter', True)
                                    settings = await get_settings(message.chat.id)
                                    if settings['auto_ffilter']:
                                        await auto_filter(client, message) 
                            else:
                                try:
                                    if settings['auto_delete']:
                                        await joelkb.delete()
                                except KeyError:
                                    grpid = await active_connection(str(message.from_user.id))
                                    await save_group_settings(grpid, 'auto_delete', True)
                                    settings = await get_settings(message.chat.id)
                                    if settings['auto_delete']:
                                        await joelkb.delete()

                        else:
                            button = eval(btn)
                            joelkb = await client.send_message(
                                group_id,
                                reply_text,
                                disable_web_page_preview=True,
                                reply_markup=InlineKeyboardMarkup(button),
                                reply_to_message_id=reply_id
                            )
                            manual = await manual_filters(client, message)
                            if manual == False:
                                settings = await get_settings(message.chat.id)
                                try:
                                    if settings['auto_ffilter']:
                                        await auto_filter(client, message)
                                        try:
                                            if settings['auto_delete']:
                                                await joelkb.delete()
                                        except KeyError:
                                            grpid = await active_connection(str(message.from_user.id))
                                            await save_group_settings(grpid, 'auto_delete', True)
                                            settings = await get_settings(message.chat.id)
                                            if settings['auto_delete']:
                                                await joelkb.delete()
                                    else:
                                        try:
                                            if settings['auto_delete']:
                                                await asyncio.sleep(600)
                                                await joelkb.delete()
                                        except KeyError:
                                            grpid = await active_connection(str(message.from_user.id))
                                            await save_group_settings(grpid, 'auto_delete', True)
                                            settings = await get_settings(message.chat.id)
                                            if settings['auto_delete']:
                                                await asyncio.sleep(600)
                                                await joelkb.delete()
                                except KeyError:
                                    grpid = await active_connection(str(message.from_user.id))
                                    await save_group_settings(grpid, 'auto_ffilter', True)
                                    settings = await get_settings(message.chat.id)
                                    if settings['auto_ffilter']:
                                        await auto_filter(client, message) 
                            else:
                                try:
                                    if settings['auto_delete']:
                                        await joelkb.delete()
                                except KeyError:
                                    grpid = await active_connection(str(message.from_user.id))
                                    await save_group_settings(grpid, 'auto_delete', True)
                                    settings = await get_settings(message.chat.id)
                                    if settings['auto_delete']:
                                        await joelkb.delete()


                except Exception as e:
                    logger.exception(e)
            break
    else:
        return False
