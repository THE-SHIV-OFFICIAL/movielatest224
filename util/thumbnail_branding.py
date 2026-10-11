import logging
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps
try:
    import pytesseract  # heavy, only needed for on-demand OCR
except Exception:  # pragma: no cover
    pytesseract = None

from info import BIN_CHANNEL, BRANDING_ENABLED, BRANDING_TOP_TEXT, BRANDING_WATERMARK


logger = logging.getLogger(__name__)


def _norm(value: str) -> str:
    return re.sub(r"[^a-z0-9_]", "", (value or "").lower())


# Our own handles are never treated as foreign watermarks.
_OWN_HANDLES = {
    _norm(item) for item in re.findall(r"@?[A-Za-z0-9_]{4,}", f"{BRANDING_WATERMARK} {BRANDING_TOP_TEXT}")
    if "@" in item or "_" in item
} | {_norm(BRANDING_WATERMARK)}
_OWN_HANDLES.discard("")


def _aliases():
    raw = os.getenv("WATERMARK_ALIASES", "@korean_drama_box,korean_drama_box")
    return [_norm(value) for value in raw.split(",") if _norm(value)]


_LINK_RE = re.compile(
    r"(t\.me|telegram\.me|tg://|https?|www\.|\.com|\.in\b|\.net|\.org|\.xyz|\.me\b|\.site|\.app|\.live|\.cc|\.co\b|\.link|\.pro|\.fun|\.top|\.club)",
    re.I,
)


def _font(size: int):
    for path in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
    ):
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    try:
        return ImageFont.load_default(size)  # Pillow >= 10.1 scalable fallback
    except TypeError:
        return ImageFont.load_default()


def _is_own(text: str) -> bool:
    n = _norm(text)
    return bool(n) and any(own and (own in n or n in own) and len(n) >= 4 for own in _OWN_HANDLES)


def _is_watermark_token(text: str, aliases) -> bool:
    lowered = text.lower()
    n = _norm(text)
    if not n or _is_own(text):
        return False
    if "@" in text and len(n) >= 3:
        return True
    if _LINK_RE.search(lowered):
        return True
    if any(alias and alias in n for alias in aliases):
        return True
    # CamelCase / underscore channel-like names, e.g. RunningMoviesHD, Movie_Hub
    raw = re.sub(r"[^A-Za-z0-9_]", "", text)
    if "_" in raw and len(raw) >= 6:
        return True
    if len(raw) >= 8 and re.search(r"[a-z][A-Z]", raw) and any(w in lowered for w in ("movie", "hub", "hd", "film", "flix", "cinema", "bot", "tv")):
        return True
    return False


def _ocr_variants(image: Image.Image):
    """Upscale small Telegram thumbs and try several contrast variants so both
    white-on-dark and dark-on-light watermarks are read."""
    target = 1400
    scale = max(1.0, target / max(image.width, 1))
    big = image.resize((round(image.width * scale), round(image.height * scale)), Image.Resampling.LANCZOS)
    gray = ImageOps.grayscale(big)
    gray = ImageOps.autocontrast(gray, cutoff=1)
    sharp = gray.filter(ImageFilter.SHARPEN)
    inverted = ImageOps.invert(sharp)
    bright = sharp.point(lambda p: 255 if p > 200 else 0)  # isolates white text
    dark = sharp.point(lambda p: 0 if p < 60 else 255)     # isolates black text
    return scale, [sharp, inverted, bright, dark]


def _read_tokens(image: Image.Image):
    scale, variants = _ocr_variants(image)
    tokens = []
    for variant in variants:
        for psm in ("11", "6"):
            try:
                data = pytesseract.image_to_data(
                    variant, config=f"--psm {psm}", output_type=pytesseract.Output.DICT
                )
            except Exception:
                logger.exception("OCR pass failed")
                continue
            for index, raw_text in enumerate(data.get("text", [])):
                text = re.sub(r"\s+", "", raw_text or "")
                try:
                    conf = float(data["conf"][index])
                except (TypeError, ValueError):
                    conf = -1
                if not text or conf < 30:
                    continue
                tokens.append((
                    data["left"][index] / scale, data["top"][index] / scale,
                    data["width"][index] / scale, data["height"][index] / scale,
                    text, psm, data["block_num"][index], data["line_num"][index],
                ))
    return tokens


def _merge_boxes(boxes, pad):
    merged = []
    for box in sorted(boxes):
        x1, y1, x2, y2 = box
        for i, (a1, b1, a2, b2) in enumerate(merged):
            overlap_y = min(y2, b2) - max(y1, b1)
            if x1 <= a2 + pad and a1 <= x2 + pad and overlap_y > 0.4 * min(y2 - y1, b2 - b1):
                merged[i] = (min(a1, x1), min(b1, y1), max(a2, x2), max(b2, y2))
                break
        else:
            merged.append(box)
    # One more pass so chains of overlaps collapse into a single box.
    if len(merged) != len(boxes):
        return _merge_boxes(merged, pad)
    return merged


def _text_boxes(image: Image.Image):
    """Return boxes (x1, y1, x2, y2) covering every foreign watermark line."""
    aliases = _aliases()
    tokens = _read_tokens(image)
    hits = []
    for token in tokens:
        text = token[4]
        if _is_watermark_token(text, aliases):
            hits.append(token)
        elif any(word in text.lower() for word in ("telegram", "join", "subscribe")):
            hits.append(token)

    boxes = []
    for left, top, w, h, _text, _psm, _blk, _ln in hits:
        center_y = top + h / 2
        line = [
            t for t in tokens
            if abs((t[1] + t[3] / 2) - center_y) <= min(h, t[3]) * 0.5
            and not _is_own(t[4])
            and abs(t[3] - h) <= max(h, t[3]) * 0.5
        ]
        # Only grow the box across words that sit next to each other on the line,
        # so the whole "Search on Telegram 👉 @Channel" phrase is covered but
        # unrelated poster text far away is not.
        x1, x2 = left, left + w
        y1, y2 = top, top + h
        gap = max(h * 2.2, image.width * 0.06)
        changed = True
        while changed:
            changed = False
            for t in line:
                tx1, tx2 = t[0], t[0] + t[2]
                if tx2 >= x1 - gap and tx1 <= x2 + gap and (tx1 < x1 or tx2 > x2):
                    x1, x2 = min(x1, tx1), max(x2, tx2)
                    y1, y2 = min(y1, t[1]), max(y2, t[1] + t[3])
                    changed = True
        if (y2 - y1) > h * 1.8:
            x1, y1, x2, y2 = left, top, left + w, top + h
        boxes.append((x1, y1, x2, y2))

    pad = max(4, image.height * 0.02)
    return [tuple(int(round(v)) for v in box) for box in _merge_boxes(boxes, pad)]


def _erase_marks(image: Image.Image, boxes):
    """Remove old watermark text by repainting it from the surrounding picture."""
    if not boxes:
        return image
    try:
        import cv2
        import numpy as np
    except Exception:
        logger.warning("OpenCV missing; blurring old watermarks instead")
        out = image.copy()
        for x1, y1, x2, y2 in boxes:
            region = out.crop((x1, y1, x2, y2)).filter(ImageFilter.GaussianBlur(8))
            out.paste(region, (x1, y1))
        return out

    arr = np.array(image)
    gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
    mask = np.zeros(gray.shape, np.uint8)
    w, h = image.size
    for x1, y1, x2, y2 in boxes:
        px, py = max(4, (y2 - y1) // 3), max(3, (y2 - y1) // 4)
        x1, y1 = max(0, x1 - px), max(0, y1 - py)
        x2, y2 = min(w, x2 + px), min(h, y2 + py)
        crop = gray[y1:y2, x1:x2]
        if crop.size == 0:
            continue
        median = np.median(crop)
        text = (np.abs(crop.astype(int) - int(median)) > 45).astype(np.uint8) * 255
        # Fall back to the whole box when the text blends into the background.
        if text.mean() < 8:
            text[:] = 255
        mask[y1:y2, x1:x2] = np.maximum(mask[y1:y2, x1:x2], text)
    mask = cv2.dilate(mask, np.ones((5, 5), np.uint8), iterations=2)
    repaired = cv2.inpaint(arr, mask, 7, cv2.INPAINT_TELEA)
    return Image.fromarray(repaired)


def _draw_brand_badge(image: Image.Image, center_x: int, center_y: int, scale: float = 1.0):
    """One stylish badge: soft shadow, dark glass pill, accent outline, white text."""
    width, height = image.size
    size = max(14, round(height * 0.068 * scale))
    font = _font(size)
    probe = ImageDraw.Draw(image)
    while size > 12:
        tb = probe.textbbox((0, 0), BRANDING_WATERMARK, font=font)
        if tb[2] - tb[0] <= width * 0.62:
            break
        size -= 1
        font = _font(size)
    tb = probe.textbbox((0, 0), BRANDING_WATERMARK, font=font)
    text_w, text_h = tb[2] - tb[0], tb[3] - tb[1]
    pad_x, pad_y = round(size * 0.9), round(size * 0.45)
    bw, bh = text_w + pad_x * 2, text_h + pad_y * 2
    x1 = min(max(6, center_x - bw // 2), width - bw - 6)
    y1 = min(max(6, center_y - bh // 2), height - bh - 6)
    x2, y2 = x1 + bw, y1 + bh
    radius = bh // 2

    base = image.convert("RGBA")
    shadow = Image.new("RGBA", base.size, (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle(
        (x1 + 2, y1 + 4, x2 + 2, y2 + 4), radius=radius, fill=(0, 0, 0, 150))
    shadow = shadow.filter(ImageFilter.GaussianBlur(max(3, size // 4)))
    base = Image.alpha_composite(base, shadow)

    badge = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(badge)
    d.rounded_rectangle((x1, y1, x2, y2), radius=radius, fill=(12, 16, 24, 205),
                        outline=(255, 196, 0, 255), width=max(2, size // 9))
    # Small accent dot before the text for a designed look.
    dot_r = max(3, size // 6)
    dot_cx = x1 + pad_x // 2
    d.ellipse((dot_cx - dot_r, (y1 + y2) // 2 - dot_r, dot_cx + dot_r, (y1 + y2) // 2 + dot_r),
              fill=(255, 196, 0, 255))
    d.text((x1 + pad_x - tb[0] + dot_r // 2, y1 + pad_y - tb[1]), BRANDING_WATERMARK, font=font,
           fill=(255, 255, 255, 255))
    return Image.alpha_composite(base, badge).convert("RGB")


def apply_thumbnail_branding(source_path: str, output_path: str):
    image = Image.open(source_path).convert("RGB")
    if max(image.size) < 640:
        factor = 640 / max(image.size)
        image = image.resize((round(image.width * factor), round(image.height * factor)), Image.Resampling.LANCZOS)
    width, height = image.size

    boxes = _text_boxes(image)
    logger.info("Thumbnail branding: %d old watermark(s) removed", len(boxes))
    image = _erase_marks(image, boxes)

    # Exactly one badge. Bottom (or no) watermark -> bottom centre; otherwise at
    # the biggest old watermark's spot.
    if boxes:
        x1, y1, x2, y2 = max(boxes, key=lambda b: (b[2] - b[0]) * (b[3] - b[1]))
        cy = (y1 + y2) // 2
        cx = width // 2 if cy > height * 0.55 else (x1 + x2) // 2
    else:
        cx, cy = width // 2, round(height * 0.88)
    return _finish_branding(image, cx, cy, output_path)


def _finish_branding(image: Image.Image, cx: int, cy: int, output_path: str, scale: float = 1.0, max_side: int = 320):
    """Draw our badge + top bot label and save a Telegram-sized JPEG thumbnail."""
    width, height = image.size
    image = _draw_brand_badge(image, cx, cy, scale)

    # Top bot label.
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    top_font = _font(max(14, round(height * 0.048 * scale)))
    top_bbox = draw.textbbox((0, 0), BRANDING_TOP_TEXT, font=top_font)
    top_w, top_h = top_bbox[2] - top_bbox[0], top_bbox[3] - top_bbox[1]
    top_x, top_y = max(10, round(width * 0.035)), max(8, round(height * 0.03))
    pad_x, pad_y = max(8, round(width * 0.016)), max(5, round(height * 0.012))
    draw.rounded_rectangle(
        (top_x - pad_x, top_y - pad_y, min(width - 4, top_x + top_w + pad_x), top_y + top_h + pad_y),
        radius=(top_h + pad_y * 2) // 2, fill=(12, 16, 24, 190),
    )
    draw.text((top_x - top_bbox[0], top_y - top_bbox[1]), BRANDING_TOP_TEXT, font=top_font,
              fill=(255, 255, 255, 245))

    result = Image.alpha_composite(image.convert("RGBA"), overlay).convert("RGB")
    result.thumbnail((max_side, max_side), Image.Resampling.LANCZOS)
    # Telegram rejects thumbnails over 200 KB (covers are normal photos).
    limit = 190 * 1024 if max_side <= 320 else 4 * 1024 * 1024
    for quality in (92, 85, 75, 65):
        result.save(output_path, "JPEG", quality=quality, optimize=True)
        if os.path.getsize(output_path) < limit:
            break
    return output_path


def _cover_fit(image: Image.Image, size):
    """Scale and centre-crop so the image fully fills `size`."""
    return ImageOps.fit(image, size, Image.Resampling.LANCZOS, centering=(0.5, 0.35))


def build_tmdb_cover(poster_path: str, output_path: str, backdrop_path: str = None, aspect: float = 16 / 9, max_side: int = 320):
    """Make a clean cover from TMDB artwork (no foreign marks) with our branding.

    Landscape videos: backdrop (or blurred poster) fills the frame and the official
    poster sits in the centre, so the title artwork is always visible.
    Portrait files/documents: the poster itself is used.
    """
    poster = Image.open(poster_path).convert("RGB")
    if aspect <= 1:
        height = 960
        width = max(320, round(height * aspect))
        canvas = _cover_fit(poster, (width, height))
    else:
        width = 1280
        height = max(360, round(width / aspect))
        if backdrop_path and os.path.exists(backdrop_path):
            background = _cover_fit(Image.open(backdrop_path).convert("RGB"), (width, height))
            background = background.filter(ImageFilter.GaussianBlur(3))
        else:
            background = _cover_fit(poster, (width, height)).filter(ImageFilter.GaussianBlur(22))
        shade = Image.new("RGB", background.size, (8, 10, 16))
        canvas = Image.blend(background, shade, 0.38)
        ph = round(height * 0.86)
        pw = round(ph * poster.width / poster.height)
        front = poster.resize((pw, ph), Image.Resampling.LANCZOS)
        px, py = (width - pw) // 2, round(height * 0.05)
        glow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        ImageDraw.Draw(glow).rectangle((px - 4, py + 6, px + pw + 4, py + ph + 10), fill=(0, 0, 0, 170))
        glow = glow.filter(ImageFilter.GaussianBlur(14))
        canvas = Image.alpha_composite(canvas.convert("RGBA"), glow).convert("RGB")
        canvas.paste(front, (px, py))
    w, h = canvas.size
    return _finish_branding(canvas, w // 2, round(h * 0.87), output_path, scale=1.45, max_side=max_side)


async def _download_url(url: str, path: str):
    import aiohttp
    async with aiohttp.ClientSession() as session:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=20)) as resp:
            if resp.status != 200:
                return None
            data = await resp.read()
    if not data:
        return None
    Path(path).write_bytes(data)
    Image.open(path).verify()
    return path


async def _tmdb_cover(media, media_type, caption, workdir):
    """Branded cover built from the matching TMDB poster, or None."""
    try:
        from utils import get_tmdb_poster
    except Exception:
        logger.warning("TMDB lookup unavailable for cover", exc_info=True)
        return None
    file_name = getattr(media, "file_name", None) or ""
    query = re.sub(r"[._]+", " ", file_name.rsplit(".", 1)[0]) or (caption or "").split("\n")[0]
    query = re.sub(r"@[A-Za-z0-9_]+|\[[^\]]*\]", " ", query).strip()
    if not query:
        return None
    try:
        movie = await get_tmdb_poster(query, file_name)
        if not movie or not movie.get("poster"):
            logger.info("No TMDB poster for %r; using fallback preview", query)
            return None
        poster = await _download_url(movie["poster"], str(Path(workdir) / "tmdb_poster.jpg"))
        if not poster:
            return None
        backdrop = None
        if movie.get("backdrop"):
            try:
                backdrop = await _download_url(movie["backdrop"], str(Path(workdir) / "tmdb_backdrop.jpg"))
            except Exception:
                backdrop = None
        aspect = 16 / 9
        w, h = getattr(media, "width", 0) or 0, getattr(media, "height", 0) or 0
        if media_type == "video" and w and h:
            aspect = w / h
        elif media_type != "video":
            aspect = 2 / 3
        out = str(Path(workdir) / "tmdb_cover.jpg")
        build_tmdb_cover(poster, out, backdrop, aspect)
        logger.info("Using TMDB cover for %r -> %s", query, movie.get("title"))
        return out
    except Exception:
        logger.warning("TMDB cover failed for %r", query, exc_info=True)
        return None


# ---------------------------------------------------------------------------
# Caption / file-name branding
# ---------------------------------------------------------------------------
_HANDLE_RE = re.compile(r"@[A-Za-z0-9_]{3,}")
_TG_LINK_RE = re.compile(r"(?:https?://)?(?:t\.me|telegram\.me|telegram\.dog)/[^\s\)\]\>]+", re.I)
_URL_RE = re.compile(r"(?:https?://|www\.)[^\s\)\]\>]+", re.I)


def replace_text_watermarks(text):
    """Swap every foreign @handle / Telegram link / website in text with our handle."""
    if not text:
        return text

    def swap(match):
        return match.group(0) if _is_own(match.group(0)) else BRANDING_WATERMARK

    text = _TG_LINK_RE.sub(swap, text)
    text = _URL_RE.sub(swap, text)
    text = _HANDLE_RE.sub(swap, text)
    for alias in _aliases():
        if alias and alias not in _OWN_HANDLES:
            text = re.sub(re.escape(alias), BRANDING_WATERMARK.lstrip("@"), text, flags=re.I)
    # Collapse repeated replacements like "@ME @ME".
    esc = re.escape(BRANDING_WATERMARK)
    text = re.sub(rf"({esc})(?:[\s\-_|:,]*{esc})+", r"\1", text)
    return text


def replace_filename_watermarks(name):
    if not name:
        return name
    stem, dot, ext = name.rpartition(".")
    if not dot:
        stem, ext = name, ""
    clean = replace_text_watermarks(stem)
    clean = re.sub(r"[\\/:*?\"<>|]", "_", clean).strip() or stem
    return f"{clean}.{ext}" if ext else clean


def _clean_media(media, media_type, caption):
    media.file_type = media_type
    media.caption = replace_text_watermarks(caption) if BRANDING_ENABLED else caption
    if BRANDING_ENABLED and getattr(media, "file_name", None):
        media.file_name = replace_filename_watermarks(media.file_name)
    return media


def _make_base_thumbnail(media_path: str, media_type: str, output_path: str, name: str):
    """Generate a usable preview when Telegram did not supply a thumbnail."""
    if media_type == "video" and shutil.which("ffmpeg"):
        try:
            subprocess.run(
                ["ffmpeg", "-nostdin", "-loglevel", "error", "-y", "-ss", "1",
                 "-i", media_path, "-frames:v", "1", "-vf", "scale=640:-2",
                 output_path], check=True, timeout=35, capture_output=True,
            )
            if Path(output_path).is_file() and Path(output_path).stat().st_size:
                return
        except (OSError, subprocess.SubprocessError):
            logger.warning("Could not extract video preview; using generated cover", exc_info=True)

    # Audio, documents and videos without a decodable frame still get a brandable
    # preview, rather than silently keeping a blank or foreign thumbnail.
    image = Image.new("RGB", (640, 360), (22, 29, 43))
    draw = ImageDraw.Draw(image)
    font = _font(25)
    label = re.sub(r"\s+", " ", name.rsplit(".", 1)[0]).strip() or "Movie"
    while label and draw.textbbox((0, 0), label, font=font)[2] > 550:
        label = label[:-1]
    draw.text((45, 145), label, font=font, fill=(240, 243, 248))
    image.save(output_path, "JPEG", quality=90)


async def brand_and_archive_message(bot, message):
    """Re-upload media with a branded Telegram thumbnail and return its media object."""
    media_type = next((kind for kind in ("document", "video", "audio")
                       if getattr(message, kind, None) is not None), None)
    if not media_type:
        return None
    media = getattr(message, media_type)
    if not BRANDING_ENABLED or getattr(message, "outgoing", False):
        media.file_type = media_type
        media.caption = message.caption
        return media

    thumbs = getattr(media, "thumbs", None) or []
    with tempfile.TemporaryDirectory(prefix="betabot_brand_") as workdir:
        try:
            original_thumb = str(Path(workdir) / "original.jpg")
            branded_thumb = str(Path(workdir) / "branded.jpg")
            media_path = await bot.download_media(message, file_name=workdir + "/")
            if not media_path:
                raise ValueError("Telegram download returned no media")
            # 1) Official TMDB poster + our branding replaces the old cover entirely.
            tmdb_thumb = await _tmdb_cover(media, media_type, message.caption, workdir)
            if tmdb_thumb:
                branded_thumb = tmdb_thumb
            elif thumbs:
                # Largest available thumbnail gives OCR the best chance.
                biggest = max(thumbs, key=lambda t: (getattr(t, "width", 0) or 0) * (getattr(t, "height", 0) or 0))
                await bot.download_media(biggest.file_id, file_name=original_thumb)
            else:
                _make_base_thumbnail(
                    media_path, media_type, original_thumb,
                    replace_filename_watermarks(getattr(media, "file_name", None) or "Movie"),
                )
            if not tmdb_thumb:
                apply_thumbnail_branding(original_thumb, branded_thumb)

            clean_name = replace_filename_watermarks(
                getattr(media, "file_name", None) or os.path.basename(media_path)
            )
            if clean_name and clean_name != os.path.basename(media_path):
                new_path = str(Path(workdir) / clean_name)
                os.replace(media_path, new_path)
                media_path = new_path

            common = dict(
                chat_id=BIN_CHANNEL,
                caption=replace_text_watermarks(message.caption),
                thumb=branded_thumb,
                file_name=clean_name,
            )
            if media_type == "video":
                extra = {}
                try:
                    import inspect
                    if "cover" in inspect.signature(bot.send_video).parameters:
                        extra["cover"] = branded_thumb  # newer Telegram video cover
                except (TypeError, ValueError):
                    pass
                sent = await bot.send_video(
                    video=media_path,
                    duration=getattr(media, "duration", 0),
                    width=getattr(media, "width", 0),
                    height=getattr(media, "height", 0),
                    supports_streaming=getattr(media, "supports_streaming", True),
                    **extra,
                    **common,
                )
            elif media_type == "audio":
                sent = await bot.send_audio(
                    audio=media_path,
                    duration=getattr(media, "duration", 0),
                    performer=getattr(media, "performer", None),
                    title=getattr(media, "title", None),
                    **common,
                )
            else:
                sent = await bot.send_document(document=media_path, **common)

            branded_media = getattr(sent, media_type)
            branded_media.file_type = media_type
            branded_media.caption = sent.caption
            return branded_media
        except Exception:
            logger.exception("Thumbnail branding failed; indexing the original media")
            return _clean_media(media, media_type, message.caption)
