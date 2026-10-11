"""Zero-download indexing helpers.

Indexing never downloads or re-uploads media. We only read file_id / name /
caption from the message and clean foreign watermarks at text level.
"""
from pyrogram import enums
from util.thumbnail_branding import _clean_media

SUPPORTED = (enums.MessageMediaType.VIDEO, enums.MessageMediaType.AUDIO, enums.MessageMediaType.DOCUMENT)


def extract_media(message):
    """Return a cleaned media object ready for save_file(), or None."""
    if not message or getattr(message, "empty", False) or message.media not in SUPPORTED:
        return None
    media = getattr(message, message.media.value, None)
    if media is None:
        return None
    caption = message.caption.html if message.caption else None
    return _clean_media(media, message.media.value, caption)
