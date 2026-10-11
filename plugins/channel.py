from pyrogram import Client, filters
from info import CHANNELS
from database.ia_filterdb import save_file
from util.fast_index import extract_media

media_filter = filters.document | filters.video | filters.audio


@Client.on_message(filters.chat(CHANNELS) & media_filter)
async def media(bot, message):
    """Media Handler - instant, no download/upload."""
    media = extract_media(message)
    if media is None:
        return
    await save_file(bot, media)
