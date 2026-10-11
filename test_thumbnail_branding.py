import asyncio
import importlib
import sys
import tempfile
import types
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from PIL import Image

# The image helpers should remain testable without live bot credentials.
_original_info = sys.modules.get("info")
sys.modules["info"] = types.SimpleNamespace(
    BIN_CHANNEL=-100123, BRANDING_ENABLED=True,
    BRANDING_TOP_TEXT="BOT- @Movie_box_xbot", BRANDING_WATERMARK="@BETABOT_HUB",
)
try:
    branding = importlib.import_module("util.thumbnail_branding")
finally:
    if _original_info is None:
        sys.modules.pop("info", None)
    else:
        sys.modules["info"] = _original_info


class BrandingTests(unittest.TestCase):
    def test_no_thumbnail_generates_cover_with_existing_badges(self):
        with tempfile.TemporaryDirectory() as directory:
            base = str(Path(directory) / "base.jpg")
            branded = str(Path(directory) / "branded.jpg")
            branding._make_base_thumbnail("unused", "document", base, "Movie.mkv")
            with patch.object(branding, "_text_boxes", return_value=[]):
                branding.apply_thumbnail_branding(base, branded)
            with Image.open(branded) as image:
                self.assertEqual(image.format, "JPEG")
                self.assertGreater(image.width, 0)

    def test_no_thumbnail_media_is_archived_not_indexed_unbranded(self):
        class Bot:
            async def download_media(self, source, file_name):
                path = str(Path(file_name) / "video.mkv")
                Path(path).write_bytes(b"media")
                return path

            async def send_document(self, document, **kwargs):
                assert Path(kwargs["thumb"]).is_file()
                assert Path(document).is_file()
                sent_media = SimpleNamespace(file_name=kwargs["file_name"])
                return SimpleNamespace(document=sent_media, caption=kwargs["caption"])

        media = SimpleNamespace(file_name="Movie @otherchannel.mkv", thumbs=[])
        message = SimpleNamespace(document=media, video=None, audio=None,
                                  caption="Watch @otherchannel", outgoing=False)
        with patch.object(branding, "_text_boxes", return_value=[]):
            result = asyncio.run(branding.brand_and_archive_message(Bot(), message))
        self.assertIsNot(result, media)
        self.assertIn("@BETABOT_HUB", result.file_name)
        self.assertIn("@BETABOT_HUB", result.caption)

    def test_tmdb_cover_matches_video_shape_and_is_telegram_sized(self):
        with tempfile.TemporaryDirectory() as directory:
            poster = str(Path(directory) / "poster.jpg")
            Image.new("RGB", (500, 750), (180, 40, 30)).save(poster)
            out = str(Path(directory) / "cover.jpg")
            branding.build_tmdb_cover(poster, out, None, 16 / 9)
            with Image.open(out) as image:
                self.assertLessEqual(max(image.size), 320)
                self.assertGreater(image.width, image.height)
            self.assertLess(Path(out).stat().st_size, 200 * 1024)

    def test_tmdb_cover_replaces_old_thumbnail(self):
        sent = {}

        class Bot:
            async def download_media(self, source, file_name):
                if not file_name.endswith("/"):
                    raise AssertionError("old thumbnail must not be downloaded")
                path = str(Path(file_name) / "video.mkv")
                Path(path).write_bytes(b"media")
                return path

            async def send_video(self, video, **kwargs):
                sent.update(kwargs)
                return SimpleNamespace(video=SimpleNamespace(file_name=kwargs["file_name"]), caption=kwargs["caption"])

        async def fake_cover(media, media_type, caption, workdir):
            out = str(Path(workdir) / "tmdb_cover.jpg")
            Image.new("RGB", (320, 180)).save(out)
            return out

        media = SimpleNamespace(file_name="Liger 2022 720p.mkv", thumbs=[SimpleNamespace(file_id="old", width=320, height=180)],
                                duration=10, width=1280, height=720)
        message = SimpleNamespace(video=media, document=None, audio=None, caption="Liger", outgoing=False)
        with patch.object(branding, "_tmdb_cover", fake_cover):
            asyncio.run(branding.brand_and_archive_message(Bot(), message))
        self.assertTrue(sent["thumb"].endswith("tmdb_cover.jpg"))


if __name__ == "__main__":
    unittest.main()
