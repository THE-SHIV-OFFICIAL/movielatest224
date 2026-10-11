import re
import os
from os import environ, getenv
from Script import script

id_pattern = re.compile(r'^.\d+$')

def is_enabled(value, default):
    if value.lower() in ["true", "yes", "1", "enable", "y"]:
        return True
    elif value.lower() in ["false", "no", "0", "disable", "n"]:
        return False
    else:
        return default

# ============================
# Bot Information Configuration
# ============================

SESSION = environ.get('SESSION', 'Media_search')
API_ID = int(environ.get('API_ID', '23491399'))
API_HASH = environ.get('API_HASH', '2b7f62a2c17cdb83427074b9615cdb90')
BOT_TOKEN = environ.get('BOT_TOKEN', '8417848620:AAFPbucH9eO_mVU6IHiVS8RwXoi96hAqIh0')

# ============================
# Bot Settings Configuration
# ============================
CACHE_TIME = int(environ.get('CACHE_TIME', 300))
USE_CAPTION_FILTER = bool(environ.get('USE_CAPTION_FILTER', True))

PICS = (environ.get('PICS', 'https://h.uguu.se/hwzXceXP.jpg')).split()
DEFAULT_PIC = environ.get('DEFAULT_PIC', 'https://image.zaw-myo.workers.dev/image/ce01a504-28ce-4b56-8055-275837d7010e')
NOR_IMG = environ.get("NOR_IMG", "https://graph.org/file/e20b5fdaf217252964202.jpg")
MELCOW_VID = environ.get("MELCOW_VID", "https://graph.org/file/60e8a622b14796e4448ce.mp4")
SPELL_IMG = environ.get("SPELL_IMG", "https://graph.org/file/13702ae26fb05df52667c.jpg")
FSUB_PICS = (environ.get('FSUB_PICS', 'https://graph.org/file/7478ff3eac37f4329c3d8.jpg https://files.catbox.moe/wktt8l.jpg')).split()  # Fsub pic

# ============================
# Admin, Channels & Users Configuration
# ============================
ADMINS = [int(admin) if id_pattern.search(admin) else admin for admin in environ.get('ADMINS', '8723235165 8418584090').split()]
CHANNELS = [int(ch) if id_pattern.search(ch) else ch for ch in environ.get('CHANNELS', '-1002904776479').split()]
LOG_CHANNEL = int(environ.get('LOG_CHANNEL', '-1002155804090'))  # Log channel id (make sure bot is admin)
BIN_CHANNEL = int(environ.get('BIN_CHANNEL', '-1003910381589'))  # Bin channel id (make sure bot is admin)
FTMBOTZX_MOVIE_UPDATE_CHANNEL = int(environ.get('UPDATE_CHANNEL', '-1002227367557'))  # Notification of those who verify will be sent to your channel
auth_channel = environ.get('AUTH_CHANNEL', '-1002227367557')  # Channel/Group ID for force sub (make sure bot is admin)
DELETE_CHANNELS = [int(dch) if id_pattern.search(dch) else dch for dch in environ.get('DELETE_CHANNELS', '-1003648004418').split()]
support_chat_id = environ.get('SUPPORT_CHAT_ID', '-1003867756570')  # Support group id (make sure bot is admin)
reqst_channel = environ.get('REQST_CHANNEL_ID', '-1003648004418')  # Request channel id (make sure bot is admin)
AUTH_CHANNEL = [int(fch) if id_pattern.search(fch) else fch for fch in environ.get('AUTH_CHANNEL', '-1002926855756').split()]
MULTI_FSUB = [int(channel_id) for channel_id in environ.get('MULTI_FSUB', '-1001957497326 -1004432738931').split() if re.match(r'^-?\d+$', channel_id)]  # Channel for force sub (make sure bot is admin)

MAGIC_FORCE_SUB = {
    -1001957497326: "normal",
    -1004432738931: "normal"
}


# ============================
# MongoDB Configuration
# ============================
DATABASE_URI = environ.get('DATABASE_URI', "mongodb+srv://preetdealbot5_db_user:movie2anjali@cluster22.ckn2tra.mongodb.net/?appName=Cluster22")
DATABASE_URI2 = environ.get('DATABASE_URI2', "mongodb+srv://preetdealbot5_db_user:movie2anjali@cluster22.ckn2tra.mongodb.net/?appName=Cluster22")
DATABASE_NAME = environ.get('DATABASE_NAME', "shiv")
COLLECTION_NAME = environ.get('COLLECTION_NAME', 'meher')

# ============================
# Movie Notification & Update Settings
# ============================
FTMBOTZX_MOVIE_UPDATE_NOTIFICATION = bool(environ.get('FTMBOTZX_MOVIE_UPDATE_NOTIFICATION', False))  # Notification On (True) / Off (False)
FTMBOTZX_IMAGE_FETCH = bool(environ.get('FTMBOTZX_IMAGE_FETCH', True))  # On (True) / Off (False)
CAPTION_LANGUAGES = ["Bhojpuri", "Hindi", "Bengali", "Tamil", "English", "Bangla", "Telugu", "Malayalam", "Kannada", "Marathi", "Punjabi", "Bengoli", "Gujrati", "Korean", "Gujarati", "Spanish", "French", "German", "Chinese", "Arabic", "Portuguese", "Russian", "Japanese", "Odia", "Assamese", "Urdu"]

# ============================
# Verification Settings
# ============================
VERIFY = bool(environ.get('VERIFY', False))  # Verification On (True) / Off (False)
FTMBOTZX_VERIFY_EXPIRE = int(environ.get('FTMBOTZX_VERIFY_EXPIRE', 48))  # Add time in hours
FTMBOTZX_VERIFIED_LOG = int(environ.get('FTMBOTZX_VERIFIED_LOG', '-1002120758420'))  # Log channel id (make sure bot is admin)
HOW_TO_VERIFY = environ.get('HOW_TO_VERIFY', 'https://t.me/sukoon_s')  # How to open tutorial link for verification

# ============================
# Link Shortener Configuration
# ============================
IS_SHORTLINK = bool(environ.get('IS_SHORTLINK', False))
SHORTLINK_URL = environ.get('SHORTLINK_URL', 'modijiurl.com')
SHORTLINK_API = environ.get('SHORTLINK_API', '79a8621baf4ba2a396eed551eb5d89634d64998f')
TUTORIAL = environ.get('TUTORIAL', 'https://t.me/Movie_box_update/187')  # Tutorial video link for opening shortlink website
IS_TUTORIAL = bool(environ.get('IS_TUTORIAL', False))

# ============================
# Channel & Group Links Configuration
# ============================
GRP_LNK = environ.get('GRP_LNK', 'https://t.me/movie_req_premium')
CHNL_LNK = environ.get('CHNL_LNK', 'https://t.me/betabot_hub')
OWNER_LNK = environ.get('OWNER_LNK', '@sukoon_s')
FTMBOTZX_MOVIE_UPDATE_CHANNEL_LNK = environ.get('UPDATE_CHANNEL_LNK', 'https://t.me/betabot_hub')
OWNERID = int(os.environ.get('OWNERID', '8418584090'))  # Replace with the actual admin ID

# ============================
# User Configuration
# ============================
auth_users = [int(user) if id_pattern.search(user) else user for user in environ.get('AUTH_USERS', '').split()]
AUTH_USERS = (auth_users + ADMINS) if auth_users else []

# ============================
# Miscellaneous Configuration
# ============================
NO_RESULTS_MSG = bool(environ.get("NO_RESULTS_MSG", True))  # True if you want no results messages in Log Channel
MAX_B_TN = environ.get("MAX_B_TN", "8")
MAX_BTN = is_enabled((environ.get('MAX_BTN', "True")), True)
PORT = environ.get("PORT", "8080")
MSG_ALRT = environ.get('MSG_ALRT', 'Made with love 😘 by @sukoon_s . Share & Support Us ♥️')
SUPPORT_CHAT = environ.get('SUPPORT_CHAT', 'https://t.me/movie_req_premium')  # Support group link (make sure bot is admin)
P_TTI_SHOW_OFF = is_enabled((environ.get('P_TTI_SHOW_OFF', "True")), True)
IMDB = is_enabled((environ.get('IMDB', "True")), True)
TMDB_API_KEY = environ.get("TMDB_API_KEY", "")
TMDB_POSTER = is_enabled((environ.get('TMDB_POSTER', "True")), True)
POSTER_SPOILER = is_enabled((environ.get('POSTER_SPOILER', "True")), True)
DELETE_TIME = int(environ.get("DELETE_TIME", "600"))
AUTO_FFILTER = is_enabled((environ.get('AUTO_FFILTER', "True")), True)
AUTO_DELETE = is_enabled((environ.get('AUTO_DELETE', "True")), True)
AUTO_DELETE_ENABLED = is_enabled((environ.get('AUTO_DELETE_ENABLED', "False")), False)  # Auto delete bot messages after 30 seconds
SINGLE_BUTTON = is_enabled((environ.get('SINGLE_BUTTON', "True")), True) # pm & Group button or link mode (True) / Off (False)
CUSTOM_FILE_CAPTION = environ.get("CUSTOM_FILE_CAPTION", f"{script.CAPTION}")
BATCH_FILE_CAPTION = environ.get("BATCH_FILE_CAPTION", CUSTOM_FILE_CAPTION)
IMDB_TEMPLATE = environ.get("IMDB_TEMPLATE", f"{script.IMDB_TEMPLATE_TXT}")
IMDBSEARCH_TEMPLATE = environ.get("IMDBSEARCH_TEMPLATE", f"{script.IMDBSEARCH_TEMPLATE}")
LONG_IMDB_DESCRIPTION = is_enabled(environ.get("LONG_IMDB_DESCRIPTION", "True"), True)
SPELL_CHECK_REPLY = is_enabled(environ.get("SPELL_CHECK_REPLY", "True"), True)
MAX_LIST_ELM = environ.get("MAX_LIST_ELM", None)
INDEX_REQ_CHANNEL = int(environ.get('INDEX_REQ_CHANNEL', LOG_CHANNEL))
FILE_STORE_CHANNEL = [int(ch) for ch in (environ.get('FILE_STORE_CHANNEL', '-1003910381589')).split()]
MELCOW_NEW_USERS = is_enabled((environ.get('MELCOW_NEW_USERS', "True")), True)
PROTECT_CONTENT = is_enabled((environ.get('PROTECT_CONTENT', "False")), False)
PUBLIC_FILE_STORE = is_enabled((environ.get('PUBLIC_FILE_STORE', "False")), True)
PM_SEARCH = bool(environ.get('PM_SEARCH', True))  # PM Search On (True) / Off (False)
EMOJI_MODE = bool(environ.get('EMOJI_MODE', False))  # Emoji status On (True) / Off (False)

# ============================
# Thumbnail Branding
# ============================
BRANDING_ENABLED = is_enabled(environ.get('BRANDING_ENABLED', 'True'), True)
BRANDING_TOP_TEXT = environ.get('BRANDING_TOP_TEXT', 'BOT- @Movie_box_xbot')
BRANDING_WATERMARK = environ.get('BRANDING_WATERMARK', '@BETABOT_HUB')

# ============================
# Bot Configuration
# ============================
auth_grp = environ.get('AUTH_GROUP', '-1002155804090')
AUTH_CHANNEL = int(auth_channel) if auth_channel and id_pattern.search(auth_channel) else None
AUTH_GROUPS = [int(ch) for ch in auth_grp.split()] if auth_grp else None
REQST_CHANNEL = int(reqst_channel) if reqst_channel and id_pattern.search(reqst_channel) else None
SUPPORT_CHAT_ID = int(support_chat_id) if support_chat_id and id_pattern.search(support_chat_id) else None
LANGUAGES = ["malayalam", "", "tamil", "", "english", "", "hindi", "", "telugu", "", "kannada", "", "gujarati", "", "marathi", "", "punjabi", ""]
QUALITIES = ["360P", "", "480P", "", "720P", "", "1080P", "", "1440P", "", "2160P", ""]
SEASONS = ["season 1" , "season 2" , "season 3" , "season 4", "season 5" , "season 6" , "season 7" , "season 8" , "season 9" , "season 10"]

# ============================
# Server & Web Configuration
# ============================

STREAM_MODE = bool(environ.get('STREAM_MODE', False)) # Set Stream mode True or False

NO_PORT = bool(environ.get('NO_PORT', False))
APP_NAME = None
if 'DYNO' in environ:
    ON_HEROKU = True
    APP_NAME = environ.get('APP_NAME')
else:
    ON_HEROKU = False
BIND_ADRESS = str(getenv('WEB_SERVER_BIND_ADDRESS', 'shivamtv.koyeb.app'))
FQDN = str(getenv('FQDN', BIND_ADRESS)) if not ON_HEROKU or getenv('FQDN') else (APP_NAME + '.herokuapp.com' if APP_NAME else 'localhost')
URL = "https://{}/".format(FQDN) if ON_HEROKU or NO_PORT else "https://{}/".format(FQDN, PORT)
SLEEP_THRESHOLD = int(environ.get('SLEEP_THRESHOLD', '60'))
WORKERS = int(environ.get('WORKERS', '4'))
SESSION_NAME = str(environ.get('SESSION_NAME', 'BETABBOTS'))
MULTI_CLIENT = False
name = str(environ.get('name', 'BETABOT'))
PING_INTERVAL = int(environ.get("PING_INTERVAL", "1200"))  # 20 minutes
if 'DYNO' in environ:
    ON_HEROKU = True
    APP_NAME = str(getenv('APP_NAME'))
else:
    ON_HEROKU = False
HAS_SSL = bool(getenv('HAS_SSL', True))
if HAS_SSL:
    URL = "https://{}/".format(FQDN)
else:
    URL = "http://{}/".format(FQDN)

# ============================
# Reactions Configuration
# ============================
REACTIONS = ["❤️", "🔥", "😍", "😂", "😮", "😢", "😡", "👍", "👎", "🎉", "💯", "⚡", "🆒"]

# ============================
# FTM Gamma Mode Configuration
# ============================
FTM_GAMMA_MODE = bool(environ.get('FTM_GAMMA_MODE', True))

  


# ============================
# Command admin
# ============================
commands = [
    """• /system - <code>sʏsᴛᴇᴍ ɪɴғᴏʀᴍᴀᴛɪᴏɴ</code>
• /del_msg - <code>ʀᴇᴍᴏᴠᴇ ғɪʟᴇ ɴᴀᴍᴇ ᴄᴏʟʟᴇᴄᴛɪᴏɴ ɴᴏтɪғɪᴄᴀᴛɪᴏн...</code>
• /movie_update - <code>ᴏɴ ᴏғғ ᴀᴄᴄᴏʀᴅɪɴɢ ʏᴏᴜʀ ɴᴇᴇᴅᴇᴅ...</code>
• /pm_search - <code>ᴘᴍ sᴇᴀʀᴄʜ ᴏɴ ᴏғғ ᴀᴄᴄᴏʀᴅɪɴɢ ʏᴏᴜʀ ɴᴇᴇᴅᴇᴅ...</code>
• /logs - <code>ɢᴇᴛ ᴛʜᴇ ʀᴇᴄᴇɴᴛ ᴇʀʀᴏʀꜱ.</code>
• /delete - <code>ᴅᴇʟᴇᴛᴇ ᴀ ꜱᴘᴇᴄɪꜰɪᴄ ꜰɪʟᴇ ꜰʀᴏᴍ ᴅʙ.</code>
• /users - <code>ɢᴇᴛ ʟɪꜱᴛ ᴏꜰ ᴍʏ ᴜꜱᴇʀꜱ ᴀɴᴅ ɪᴅꜱ.</code>
• /chats - <code>ɢᴇᴛ ʟɪꜱᴛ ᴏꜰ ᴍʏ ᴄʜᴀᴛꜱ ᴀɴᴅ ɪᴅꜱ.</code>
• /leave  - <code>ʟᴇᴀᴠᴇ ꜰʀᴏᴍ ᴀ ᴄʜᴀᴛ.</code>
• /disable  -  <code>ᴅɪꜱᴀʙʟᴇ ᴀ ᴄʜᴀᴛ.</code>""",

    """• /ban  - <code>ʙᴀɴ ᴀ ᴜꜱᴇʀ.</code>
• /unban  - <code>ᴜɴʙᴀɴ ᴀ ᴜꜱᴇʀ.</code>
• /channel - <code>ɢᴇᴛ ʟɪꜱᴛ ᴏꜰ ᴛᴏᴛᴀʟ ᴄᴏɴɴᴇᴄᴛᴇᴅ ɢʀᴏᴜᴘꜱ.</code>
• /broadcast - <code>ʙʀᴏᴀᴅᴄᴀꜱᴛ ᴀ ᴍᴇꜱꜱᴀɢᴇ ᴛᴏ ᴀʟʟ ᴜꜱᴇʀꜱ.</code>
• /grp_broadcast - <codeʙʀᴏᴀᴅᴄᴀsᴛ ᴀ ᴍᴇssᴀɢᴇ ᴛᴏ ᴀʟʟ ᴄᴏɴɴᴇᴄᴛᴇᴅ ɢʀᴏᴜᴘs.</code>
• /gfilter - <code>ᴀᴅᴅ ɢʟᴏʙᴀʟ ғɪʟᴛᴇʀs.</code>
• /gfilters - <code>ᴠɪᴇᴡ ʟɪsᴛ ᴏғ ᴀʟʟ ɢʟᴏʙᴀʟ ғɪʟᴛᴇʀs.</code>
• /delg - <code>ᴅᴇʟᴇᴛᴇ ᴀ sᴘᴇᴄɪғɪᴄ ɢʟᴏʙᴀʟ ғɪʟᴛᴇʀ.</code>
• /delallg - <code>ᴅᴇʟᴇᴛᴇ ᴀʟʟ Gғɪʟᴛᴇʀs ғʀᴏᴍ ᴛʜᴇ ʙᴏᴛ's ᴅᴀᴛᴀʙᴀsᴇ.</code>
• /deletefiles - <code>ᴅᴇʟᴇᴛᴇ CᴀᴍRɪᴘ ᴀɴᴅ PʀᴇDVD ғɪʟᴇs ғʀᴏᴍ ᴛʜᴇ ʙᴏᴛ's ᴅᴀᴛᴀʙᴀsᴇ.</code>
• /send - <code>ꜱᴇɴᴅ ᴍᴇꜱꜱᴀɢᴇ ᴛᴏ ᴀ ᴘᴀʀᴛɪᴄᴜʟᴀʀ ᴜꜱᴇʀ.</code>""",

    """• /restart - <code>ʀᴇꜱᴛᴀʀᴛ ᴛʜᴇ ʙᴏᴛ.</code>"""
]



# ============================
# Logs Configuration
# ============================
LOG_STR = "🎛️ Current Customized Configurations:\n"
LOG_STR += f"🎬 IMDB Results: {'✅ Enabled' if IMDB else '❌ Disabled'}\n"
LOG_STR += f"📱 P_TTI_SHOW_OFF: {'✅ Users redirected to PM' if P_TTI_SHOW_OFF else '❌ Direct file sending'}\n"
LOG_STR += f"🔘 SINGLE_BUTTON: {'✅ Combined filename/size' if SINGLE_BUTTON else '❌ Separate buttons'}\n"
LOG_STR += f"📝 CUSTOM_FILE_CAPTION: {'✅ Enabled: ' + CUSTOM_FILE_CAPTION if CUSTOM_FILE_CAPTION else '❌ Using default captions'}\n"
LOG_STR += f"📚 LONG_IMDB_DESCRIPTION: {'✅ Extended plot enabled' if LONG_IMDB_DESCRIPTION else '❌ Short plot'}\n"
LOG_STR += f"🔤 SPELL_CHECK_REPLY: {'✅ Smart suggestions enabled' if SPELL_CHECK_REPLY else '❌ Disabled'}\n"
