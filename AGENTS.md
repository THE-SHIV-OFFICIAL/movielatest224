# Project rules

- Brand Telegram thumbnails during ingestion, archive the re-uploaded media in `BIN_CHANNEL`, and index that new file ID so cached delivery preserves the custom preview.
- Detect foreign watermarks with multi-pass upscaled OCR (handles, Telegram links, websites, aliases) and also rewrite captions/file names, so every old channel mark is swapped for our own branding.

- Keep TMDB title/year selection and file-backed display labels in `util/movie_display.py` so poster and availability claims stay consistent across Telegram search replies.
- When a Telegram media item has no thumbnail, extract a video frame if available or generate a branded cover so indexed file IDs always have the same preview branding. Do not alter video frames; this is preview-only.

- Media covers: the matching TMDB poster (title+year from file name) plus our branding replaces the original Telegram thumbnail; the OCR-cleaned old thumbnail is only a fallback when TMDB has no match.
- User delivery: videos are sent by file_id with a Telegram video cover built from the TMDB poster + branding (util/cover_send.py), falling back to a plain send; requires pyrofork with video cover support.
- Result filters: quality/language/season-part menus are built from the actual files (util/file_filters.py) and filtered/paginated in Python, so combined filters work regardless of word order.
