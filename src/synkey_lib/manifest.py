"""Build the `manifest.json` the SynKey app fetches over HTTP."""

from __future__ import annotations

import json
from pathlib import Path

from .metadata import SongMeta

MANIFEST_VERSION = 1


def normalize_base_url(url: str) -> str:
    return url.rstrip("/")


def song_entry(meta: SongMeta, content_hash: str, url: str, size: int) -> dict:
    return {
        "title": meta.title,
        "artist": meta.artist,
        "difficulty": meta.difficulty,
        "contentHash": content_hash,
        "url": url,
        "size": size,
    }


def build_manifest(songs: list[dict]) -> dict:
    return {"version": MANIFEST_VERSION, "songs": songs}


def write_manifest(out_dir: Path, manifest: dict) -> None:
    text = json.dumps(manifest, ensure_ascii=False, indent=2)
    (out_dir / "manifest.json").write_text(text, encoding="utf-8")
