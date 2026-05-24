"""Build `.synkey` archives byte-compatible with the SynKey app."""

from __future__ import annotations

import hashlib
import io
import json
import zipfile

from .metadata import SongMeta

# Matches the app's `_formatVersion`. Bump deliberately when the app's format changes.
META_VERSION = 3


def md5_hex(data: bytes) -> str:
    """Hex MD5 of MIDI bytes — must equal the app's `hashMidiBytes`."""
    return hashlib.md5(data).hexdigest()


def build_meta(midi_bytes: bytes, song: SongMeta) -> dict:
    return {
        "version": META_VERSION,
        "contentHash": md5_hex(midi_bytes),
        "title": song.title,
        "artist": song.artist,
        "difficulty": song.difficulty,
        "description": song.description,
    }


# Fixed timestamp keeps archive bytes reproducible across runs.
_EPOCH = (1980, 1, 1, 0, 0, 0)


def _add(zf: zipfile.ZipFile, name: str, data: bytes) -> None:
    info = zipfile.ZipInfo(name, date_time=_EPOCH)
    info.compress_type = zipfile.ZIP_STORED
    zf.writestr(info, data)


def pack_synkey(midi_bytes: bytes, song: SongMeta) -> bytes:
    """Pack a `.synkey` archive: `song.mid` + `meta.json`, stored uncompressed."""
    meta = build_meta(midi_bytes, song)
    meta_bytes = json.dumps(meta, ensure_ascii=False, indent=2).encode("utf-8")

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        _add(zf, "song.mid", midi_bytes)
        _add(zf, "meta.json", meta_bytes)
    return buf.getvalue()
