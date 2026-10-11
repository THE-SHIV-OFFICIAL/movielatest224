"""TMDB matching and file-backed labels for Telegram movie results."""
import html
import re
from datetime import date
from difflib import SequenceMatcher

NOISE = re.compile(r'\b(?:s\d{1,2}|e\d{1,2}|season\s?\d{1,2}|episode\s?\d{1,2}|360p|480p|720p|1080p|1440p|2160p|4k|hevc|x264|x265|10bit|webrip|web[ .-]?dl|hdrip|dvdrip|bluray|hindi|english|dual\s?audio|movie|series|bengali|tamil|telugu|malayalam|kannada|punjabi|multi\s?audio|uncut|org|esubs?|hdtc|hdcam|camrip|pre\s?dvd|hq|aac|dd\s?5\s?1|v\d|south|dubbed|proper|extended|hdts|ott|amzn|nf|zee5|hotstar)\b', re.I)
YEAR = re.compile(r'\b(?:19|20)\d{2}\b')
LANGUAGES = ('Hindi', 'English', 'Tamil', 'Telugu', 'Malayalam', 'Kannada', 'Bengali', 'Punjabi', 'Marathi', 'Gujarati', 'Korean', 'Japanese', 'Spanish', 'French', 'German', 'Urdu', 'Bhojpuri')
QUALITIES = ('360p', '480p', '720p', '1080p', '1440p', '2160p')


def clean_title(query, filename=None):
    year_match = YEAR.search(query)
    if not year_match and filename:
        year_match = YEAR.search(filename)
    year = int(year_match.group()) if year_match else None
    title = query
    # Release names put the title before the year: "Liger 2022 UNCUT 720p ...".
    own_year = YEAR.search(query)
    if own_year and query[:own_year.start()].strip(' ([{-_.'):
        title = query[:own_year.start()]
    title = re.sub(r'@\w+|\[[^\]]*\]', ' ', title)
    title = YEAR.sub(' ', title)
    title = NOISE.sub(' ', title)
    title = re.sub(r'[^\w\s]', ' ', title, flags=re.UNICODE)
    return ' '.join(title.split()).strip(), year


def normalized(value):
    return ' '.join(re.findall(r'\w+', (value or '').casefold()))


def select_movie(results, title, year=None):
    """Never use a fuzzy or wrong-year result just because TMDB lists it first."""
    target = normalized(title)
    if not target:
        return None
    candidates = []
    for result in results:
        if result.get('media_type') not in ('movie', 'tv') or not result.get('poster_path'):
            continue
        names = [result.get('title'), result.get('name'), result.get('original_title'), result.get('original_name')]
        similarity = max((SequenceMatcher(None, target, normalized(name)).ratio() for name in names if name), default=0)
        if similarity < 0.86:
            continue
        release = (result.get('release_date') or result.get('first_air_date') or '')[:4]
        release_year = int(release) if release.isdigit() else None
        if year and release_year != year:
            continue
        # Exact names first; newest matching release next, then audience confidence.
        score = (similarity, release_year or 0, min(result.get('vote_count') or 0, 10000))
        candidates.append((score, result))
    return max(candidates, key=lambda item: item[0])[1] if candidates else None


def poster_variants(posters, primary):
    """Prefer the Hindi and English artworks of the SAME TMDB title."""
    chosen = []
    for lang in ('hi', 'en'):
        options = [p for p in posters if p.get('iso_639_1') == lang and p.get('file_path')]
        if options:
            chosen.append(max(options, key=lambda p: (p.get('vote_average') or 0, p.get('vote_count') or 0))['file_path'])
    if primary and primary not in chosen:
        chosen.insert(0, primary)
    return list(dict.fromkeys(chosen))[:2]


def file_details(files):
    languages, qualities, sizes = set(), set(), set()
    for file in files:
        name = getattr(file, 'file_name', '') or ''
        caption = getattr(file, 'caption', '') or ''
        label = f'{name} {caption}'
        for language in LANGUAGES:
            if re.search(r'(?<!\w)' + re.escape(language) + r'(?!\w)', label, re.I):
                languages.add(language)
        for quality in QUALITIES:
            if re.search(r'(?<!\w)' + re.escape(quality) + r'(?!\w)', label, re.I):
                qualities.add(quality)
        if re.search(r'(?<!\w)(?:4k|uhd)(?!\w)', label, re.I):
            qualities.add('2160p')
        size = getattr(file, 'file_size', 0) or 0
        if size > 0:
            sizes.add(f'{size / (1024 ** 3):.2f} GB')
    return (
        ', '.join(x for x in LANGUAGES if x in languages) or 'Not listed',
        ', '.join(x for x in QUALITIES if x in qualities) or 'Not listed',
        ', '.join(sorted(sizes, key=lambda s: float(s.split()[0]))[:12]) or 'Not listed',
    )


def file_years(files):
    """All years found across the file names/captions, latest first."""
    years = set()
    for file in files:
        label = f"{getattr(file, 'file_name', '') or ''} {getattr(file, 'caption', '') or ''}"
        years.update(YEAR.findall(label))
    return sorted(years, reverse=True)


def movie_caption(movie, files, total_results):
    languages, qualities, sizes = file_details(files)
    title = html.escape(str(movie.get('title') or 'Movie'))
    rating = movie.get('rating')
    rating_text = f"{rating}/10 ({movie.get('votes', 0):,} votes)" if rating is not None else 'Not rated yet'
    tmdb_year = str(movie.get('year') or '').strip()
    years = file_years(files)
    if tmdb_year and tmdb_year != '—' and tmdb_year not in years:
        years.append(tmdb_year)
    year_text = ', '.join(years) if years else '—'
    page_note = ' • shown files' if total_results > len(files) else ''
    return (f'<b>🎬 𝑴𝑶𝑽𝑰𝑬 𝑺𝑷𝑶𝑻𝑳𝑰𝑮𝑯𝑻</b>\n\n'
            f'🎥 <b>{title}</b>\n'
            f'⭐ <b>Rating:</b> {rating_text}\n'
            f'📅 <b>Year:</b> {html.escape(year_text)}\n'
            f'🗣️ <b>Languages:</b> {html.escape(languages)}{page_note}\n'
            f'🎞️ <b>Quality:</b> {html.escape(qualities)}{page_note}\n'
            f'💾 <b>File sizes:</b> {html.escape(sizes)}{page_note}\n'
            f'📁 <b>Available files:</b> {total_results}')
