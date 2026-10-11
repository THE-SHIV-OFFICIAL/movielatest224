import logging
from struct import pack
import re
import base64
from pyrogram.file_id import FileId
from pymongo.errors import DuplicateKeyError
from umongo import Instance, Document, fields
from motor.motor_asyncio import AsyncIOMotorClient
from marshmallow.exceptions import ValidationError
from info import CAPTION_LANGUAGES, DATABASE_URI, DATABASE_URI2, DATABASE_NAME, COLLECTION_NAME, USE_CAPTION_FILTER, MAX_B_TN, FTMBOTZX_MOVIE_UPDATE_CHANNEL, OWNERID
from utils import get_settings, save_group_settings, temp, get_movie_update_status
from database.users_chats_db import add_name
from .Imdbposter import get_movie_details, fetch_image
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

#---------------------------------------------------------
#some basic variables needed
saveMedia = None
tempDict = {'indexDB': DATABASE_URI}

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

#primary db
client = AsyncIOMotorClient(DATABASE_URI)
db = client[DATABASE_NAME]
instance = Instance.from_db(db)

@instance.register
class Media(Document):
    file_id = fields.StrField(attribute='_id')
    file_ref = fields.StrField(allow_none=True)
    file_name = fields.StrField(required=True)
    file_size = fields.IntField(required=True)
    file_type = fields.StrField(allow_none=True)
    mime_type = fields.StrField(allow_none=True)
    caption = fields.StrField(allow_none=True)

    class Meta:
        indexes = ('$file_name', )
        collection_name = COLLECTION_NAME
#secondary db
client2 = AsyncIOMotorClient(DATABASE_URI2)
db2 = client2[DATABASE_NAME]
instance2 = Instance.from_db(db2)

@instance2.register
class Media2(Document):
    file_id = fields.StrField(attribute='_id')
    file_ref = fields.StrField(allow_none=True)
    file_name = fields.StrField(required=True)
    file_size = fields.IntField(required=True)
    file_type = fields.StrField(allow_none=True)
    mime_type = fields.StrField(allow_none=True)
    caption = fields.StrField(allow_none=True)

    class Meta:
        indexes = ('$file_name', )
        collection_name = COLLECTION_NAME

async def choose_mediaDB():
    """This Function chooses which database to use based on the value of indexDB key in the dict tempDict."""
    global saveMedia
    if tempDict['indexDB'] == DATABASE_URI:
        logger.info("Using first db (Media)")
        saveMedia = Media
    else:
        logger.info("Using second db (Media2)")
        saveMedia = Media2


async def send_msg(bot, filename, caption): 
    try:
        filename = re.sub(r'\(\@\S+\)|\[\@\S+\]|\b@\S+|\bwww\.\S+', '', filename).strip()
        caption = re.sub(r'\(\@\S+\)|\[\@\S+\]|\b@\S+|\bwww\.\S+', '', caption).strip()

        year_match = re.search(r"\b(19|20)\d{2}\b", caption)
        if year_match:
            year = year_match.group(0)
        else:
            year = None   
        pattern = r"(?i)(?:s|season)0*(\d{1,2})"
        season = re.search(pattern, caption)
        if not season:
            season = re.search(pattern, filename)
        if year:
            filename = filename[: filename.find(year) + 4]  
        if not year:   
          if season:
            season = season.group(1) if season else None 
            filename = filename[: filename.find(season) +1 ]
        qualities = ["ORG", "org", "hdcam", "HDCAM", "HQ", "hq", "HDRip", "hdrip", "camrip", "CAMRip", "hdtc", "predvd", "DVDscr", "dvdscr", "dvdrip", "dvdscr", "HDTC", "dvdscreen", "HDTS", "hdts"]
        quality = await get_qualities(caption.lower(), qualities) or "HDRip"
        language = ""
        possible_languages = CAPTION_LANGUAGES
        for lang in possible_languages:
            if lang.lower() in caption.lower():
                language += f"{lang}, "
        if not language:
            language = "Not idea 😄"
        else:
            language = language[:-2]
        filename = filename.replace('(', '').replace(')', '').replace('[', '').replace(']', '').replace('{', '').replace('}', '').replace(':', '').replace(';', '').replace("'", '').replace('-', '').replace('!', '')
        text = "#𝑵𝒆𝒘_𝑭𝒊𝒍𝒆_𝑨𝒅𝒅𝒆𝒅 ✅\n\n👷𝑵𝒂𝒎𝒆: `{}`\n\n🌳𝑸𝒖𝒂𝒍𝒊𝒕𝒚: {}\n\n🍁𝑨𝒖𝒅𝒊𝒐: {}"
        text = text.format(filename, quality, language)
        if await add_name(OWNERID, filename):
          imdb_task = get_movie_details(filename)
          imdb = await imdb_task
          resized_poster = None
          if imdb:
              poster_url = imdb.get('poster_url')
              if poster_url:
                  resized_poster_task = fetch_image(poster_url)
                  resized_poster = await resized_poster_task
          filenames = filename.replace(" ", '-')
          btn = [[InlineKeyboardButton('🌲 Get Files 🌲', url=f"https://telegram.me/{temp.U_NAME}?start=getfile-{filenames}")]]
          if resized_poster:
              await bot.send_photo(chat_id=FTMBOTZX_MOVIE_UPDATE_CHANNEL, photo=resized_poster, caption=text, reply_markup=InlineKeyboardMarkup(btn))
          else:              
              await bot.send_message(chat_id=FTMBOTZX_MOVIE_UPDATE_CHANNEL, text=text, reply_markup=InlineKeyboardMarkup(btn))
    except:
        pass



async def get_qualities(text, qualities: list):
    """Get all Quality from text"""
    quality = []
    for q in qualities:
        if q in text:
            quality.append(q)
    quality = ", ".join(quality)
    return quality[:-2] if quality.endswith(", ") else quality

def _caption_text(caption):
  """Accept str or pyrogram Str/caption objects safely."""
  if not caption:
    return None
  html_value = getattr(caption, 'html', None)
  return html_value if isinstance(html_value, str) else str(caption)


async def save_file(bot, media, notify=True):
  """Save file in database"""
  # TODO: Find better way to get same file_id for same media to avoid duplicates
  file_id, file_ref = unpack_new_file_id(media.file_id)
  file_name = re.sub(r"(_|\-|\.|\+)", " ", str(media.file_name))
  try:
    # Check for duplicates in both databases
    if await Media.count_documents({'file_id': file_id}, limit=1):
            logger.warning(f'{getattr(media, "file_name", "NO_FILE")} is already saved in primary DB !')
            return False, 0
    if await Media2.count_documents({'file_id': file_id}, limit=1):
            logger.warning(f'{getattr(media, "file_name", "NO_FILE")} is already saved in secondary DB !')
            return False, 0
    file = saveMedia(
      file_id=file_id,
      file_ref=file_ref,
      file_name=file_name,
      file_size=media.file_size,
      file_type=media.file_type,
      mime_type=media.mime_type,
      caption=_caption_text(getattr(media, 'caption', None)),
    )
  except ValidationError:
    logger.exception('Error occurred while saving file in database')
    return False, 2
  else:
    try:
      await file.commit()
    except DuplicateKeyError:   
      logger.warning(
        f'{getattr(media, "file_name", "NO_FILE")} is already saved in database'
      )
      return False, 0
    else:
      logger.info(f'{getattr(media, "file_name", "NO_FILE")} is saved to database')
      if not notify:
          return True, 1
      bot_id = bot.me.id
      try:
          status = await get_movie_update_status(bot_id)
          if status:
              logger.info(f"Movie update notifications are enabled for bot {bot_id}.")
              await send_msg(bot, file.file_name, file.caption)
          else:
              logger.info(f"Movie update notifications are disabled for bot {bot_id}.")
              status = False  
      except Exception as e:
          logger.error(f"Failed to fetch movie update notification status for bot {bot_id}: {e}")
          status = False  
      return True, 1

async def get_search_results(chat_id, query, file_type=None, max_results=10, offset=0, filter=False):
    """For given query return (results, next_offset)"""
    if chat_id is not None:
        settings = await get_settings(int(chat_id))
        try:
            if settings['max_btn']:
                max_results = 10
            else:
                max_results = int(MAX_B_TN)
        except KeyError:
            await save_group_settings(int(chat_id), 'max_btn', False)
            settings = await get_settings(int(chat_id))
            if settings['max_btn']:
                max_results = 10
            else:
                max_results = int(MAX_B_TN)
    query = query.strip()
    #if filter:
        #better ?
        #query = query.replace(' ', r'(\s|\.|\+|\-|_)')
        #raw_pattern = r'(\s|_|\-|\.|\+)' + query + r'(\s|_|\-|\.|\+)'
    if not query:
        raw_pattern = '.'
    elif ' ' not in query:
        raw_pattern = r'(\b|[\.\+\-_])' + query + r'(\b|[\.\+\-_])'
    else:
        raw_pattern = query.replace(' ', r'.*[\s\.\+\-_()]')

    try:
        regex = re.compile(raw_pattern, flags=re.IGNORECASE)
    except:
        return []

    if USE_CAPTION_FILTER:
        filter = {'$or': [{'file_name': regex}, {'caption': regex}]}
    else:
        filter = {'file_name': regex}

    if file_type:
        filter['file_type'] = file_type

    # Get all results from both databases
    cursor = Media.find(filter)
    cursor2 = Media2.find(filter)
    cursor.sort('$natural', -1)
    cursor2.sort('$natural', -1)

    fileList1 = await cursor.to_list(length=None)
    fileList2 = await cursor2.to_list(length=None)

    # Combine and deduplicate by file_id
    all_files = fileList1 + fileList2
    seen_file_ids = set()
    unique_files = []

    for file in all_files:
        if file.file_id not in seen_file_ids:
            seen_file_ids.add(file.file_id)
            unique_files.append(file)

    total_results = len(unique_files)

    #verifies max_results is an even number or not
    if max_results%2 != 0: 
        logger.info(f"Since max_results is an odd number ({max_results}), bot will use {max_results+1} as max_results to make it even.")
        max_results += 1

    # Apply pagination to deduplicated results
    start_idx = offset
    end_idx = offset + max_results
    files = unique_files[start_idx:end_idx]

    next_offset = end_idx if end_idx < total_results else ''

    return files, next_offset, total_results


async def get_bad_files(query, file_type=None, filter=False):
    """For given query return (results, next_offset)"""
    query = query.strip()
    #if filter:
        #better ?
        #query = query.replace(' ', r'(\s|\.|\+|\-|_)')
        #raw_pattern = r'(\s|_|\-|\.|\+)' + query + r'(\s|_|\-|\.|\+)'
    if not query:
        raw_pattern = '.'
    elif ' ' not in query:
        raw_pattern = r'(\b|[\.\+\-_])' + query + r'(\b|[\.\+\-_])'
    else:
        raw_pattern = query.replace(' ', r'.*[\s\.\+\-_()]')

    try:
        regex = re.compile(raw_pattern, flags=re.IGNORECASE)
    except:
        return []

    if USE_CAPTION_FILTER:
        filter = {'$or': [{'file_name': regex}, {'caption': regex}]}
    else:
        filter = {'file_name': regex}

    if file_type:
        filter['file_type'] = file_type

    cursor = Media.find(filter)
    cursor2 = Media2.find(filter)

    cursor.sort('$natural', -1)
    cursor2.sort('$natural', -1)

    files = ((await cursor2.to_list(length=(await Media2.count_documents(filter))))+(await cursor.to_list(length=(await Media.count_documents(filter)))))

    total_results = len(files)

    return files, total_results

async def get_file_details(query):
    filter = {'file_id': query}
    cursor = Media.find(filter)
    filedetails = await cursor.to_list(length=1)
    if not filedetails:
        cursor2 = Media2.find(filter)
        filedetails = await cursor2.to_list(length=1)
    return filedetails


def encode_file_id(s: bytes) -> str:
    r = b""
    n = 0

    for i in s + bytes([22]) + bytes([4]):
        if i == 0:
            n += 1
        else:
            if n:
                r += b"\x00" + bytes([n])
                n = 0

            r += bytes([i])

    return base64.urlsafe_b64encode(r).decode().rstrip("=")

def encode_file_ref(file_ref: bytes) -> str:
    return base64.urlsafe_b64encode(file_ref).decode().rstrip("=")

def unpack_new_file_id(new_file_id):
    """Return file_id, file_ref"""
    decoded = FileId.decode(new_file_id)
    file_id = encode_file_id(
        pack(
            "<iiqq",
            int(decoded.file_type),
            decoded.dc_id,
            decoded.media_id,
            decoded.access_hash
        )
    )
    file_ref = encode_file_ref(decoded.file_reference)
    return file_id, file_ref

