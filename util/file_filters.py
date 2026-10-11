"""Detect which qualities / languages / seasons / parts really exist in files."""
import re

QUALITY_ORDER = ["360p", "480p", "540p", "720p", "1080p", "1440p", "2160p"]
LANGUAGE_NAMES = ["Hindi", "English", "Tamil", "Telugu", "Malayalam", "Kannada", "Bengali",
                  "Marathi", "Punjabi", "Gujarati", "Bhojpuri", "Odia", "Urdu", "Korean",
                  "Japanese", "Chinese", "Spanish", "French", "German", "Russian", "Arabic",
                  "Multi Audio", "Dual Audio"]
_LANG_ALIASES = {"Bengali": r"bengali|bangla|bengoli", "Gujarati": r"gujarati|gujrati",
                 "Hindi": r"hindi|hin", "English": r"english|eng", "Tamil": r"tamil|tam",
                 "Telugu": r"telugu|tel", "Malayalam": r"malayalam|mal", "Kannada": r"kannada|kan",
                 "Multi Audio": r"multi[\s._-]?audio", "Dual Audio": r"dual[\s._-]?audio"}

_SEP = r"(?<![a-z0-9])"
_END = r"(?![a-z0-9])"
_SEASON = re.compile(_SEP + r"(?:s(\d{1,2})(?=e\d|" + r"[^a-z0-9]|$)|season[\s._-]*(\d{1,2}))", re.I)
_PART = re.compile(_SEP + r"(?:part|pt|vol(?:ume)?|chapter)[\s._-]*(\d{1,2})" + _END, re.I)


def _label(file):
    return f"{getattr(file, 'file_name', '') or ''} {getattr(file, 'caption', '') or ''}"


def file_qualities(file):
    text = _label(file).lower()
    found = {q for q in QUALITY_ORDER if re.search(_SEP + q + _END, text)}
    if re.search(_SEP + r"(?:4k|uhd)" + _END, text):
        found.add("2160p")
    return found


def file_languages(file):
    text = _label(file).lower()
    found = set()
    for name in LANGUAGE_NAMES:
        pattern = _LANG_ALIASES.get(name, re.escape(name.lower()))
        if re.search(_SEP + r"(?:" + pattern + r")" + _END, text):
            found.add(name)
    return found


def file_seasons(file):
    """Season and part numbers, as ('s', n) / ('p', n)."""
    text = _label(file)
    found = set()
    for m in _SEASON.finditer(text):
        num = int(m.group(1) or m.group(2))
        if 0 < num < 100:
            found.add(("s", num))
    for m in _PART.finditer(text):
        num = int(m.group(1))
        if 0 < num < 100:
            found.add(("p", num))
    return found


def available(files, kind):
    """Sorted (value, label) options that actually exist in `files`."""
    if kind == "q":
        values = set().union(*(file_qualities(f) for f in files)) if files else set()
        return [(q, f"🎞️ {q.upper()}") for q in QUALITY_ORDER if q in values]
    if kind == "l":
        values = set().union(*(file_languages(f) for f in files)) if files else set()
        return [(l.lower().replace(" ", ""), f"🗣️ {l}") for l in LANGUAGE_NAMES if l in values]
    values = set().union(*(file_seasons(f) for f in files)) if files else set()
    out = [(f"s{n}", f"📺 Season {n}") for t, n in sorted(values) if t == "s"]
    out += [(f"p{n}", f"🧩 Part {n}") for t, n in sorted(values) if t == "p"]
    return out


def matches(file, kind, value):
    if kind == "q":
        return value in file_qualities(file)
    if kind == "l":
        return value in {l.lower().replace(" ", "") for l in file_languages(file)}
    return (value[0], int(value[1:])) in file_seasons(file)


def apply_filters(files, active):
    return [f for f in files if all(matches(f, k, v) for k, v in active.items())]


def option_label(kind, value):
    if kind == "q":
        return value.upper()
    if kind == "l":
        return next((l for l in LANGUAGE_NAMES if l.lower().replace(" ", "") == value), value.title())
    return ("Season " if value[0] == "s" else "Part ") + value[1:]


_YEAR = re.compile(r"(?<!\d)(19\d{2}|20\d{2})(?!\d)")


def file_year(file):
    """Extract the release year from a file's name/caption (None if absent)."""
    years = [int(y) for y in _YEAR.findall(_label(file))]
    return max(years) if years else None


def sort_files_by_year(files):
    """Latest year first, oldest last; files without a year go at the end.
    Within the same year, bigger files first."""
    def key(f):
        y = file_year(f)
        return (y is not None, y or 0, getattr(f, 'file_size', 0) or 0)
    return sorted(files, key=key, reverse=True)
