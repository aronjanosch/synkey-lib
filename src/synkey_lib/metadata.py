"""Resolve song metadata from filenames and an optional override file."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import yaml

_BRACKET_JUNK = re.compile(r"\s*[\[(][^\])]*[\])]")
_NON_ALNUM = re.compile(r"[^a-z0-9]+")


@dataclass
class SongMeta:
    title: str
    artist: str = ""
    difficulty: int = 0
    description: str = ""


def heuristic_from_filename(filename: str) -> SongMeta:
    """Best-effort title/artist guess. Imperfect — overridable via the metadata file."""
    stem = Path(filename).stem
    stem = _BRACKET_JUNK.sub("", stem)
    text = re.sub(r"\s+", " ", stem.replace("_", " ")).strip()

    artist, sep, title = text.partition(" - ")
    if not sep:
        return SongMeta(title=text)
    return SongMeta(title=title.strip(), artist=artist.strip())


def load_overrides(path: Path) -> dict[str, dict]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected a mapping of filename -> fields")
    return data


def resolve(filename: str, overrides: dict[str, dict]) -> SongMeta:
    """Merge filename heuristic with overrides; overrides win field-by-field."""
    meta = heuristic_from_filename(filename)
    override = overrides.get(filename)
    if override:
        for field in ("title", "artist", "difficulty", "description"):
            if field in override:
                setattr(meta, field, override[field])
    return meta


def slugify(text: str) -> str:
    return _NON_ALNUM.sub("-", text.lower()).strip("-")


def unique_slug(base: str, used: set[str]) -> str:
    slug = base or "song"
    candidate = slug
    n = 2
    while candidate in used:
        candidate = f"{slug}-{n}"
        n += 1
    used.add(candidate)
    return candidate
