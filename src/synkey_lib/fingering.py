"""Convert Synthesia `FingerHints` into a `.synkey` `fingering.json`."""

from __future__ import annotations

import io
import logging
import re
import xml.etree.ElementTree as ET
from pathlib import Path

import mido

log = logging.getLogger("synkey_lib")

FINGERING_VERSION = 1

_TRACK_TOK = re.compile(r"t(\d+):")
_MEASURE_TOK = re.compile(r"m(\d+):")


def synthesia_path_for(midi_path: Path) -> Path:
    return midi_path.with_suffix(".synthesia")


def parse_finger_hints(text: str) -> dict[int, list[int]]:
    """Flatten `FingerHints` into {track: [finger, ...]}.

    `t0:`/`t1:` open a track, `mK:` markers are readability-only and dropped,
    each remaining token is a run of per-note digits (1-5, or 0 = no hint).
    """
    tracks: dict[int, list[int]] = {}
    current: int | None = None
    for tok in text.split():
        if m := _TRACK_TOK.fullmatch(tok):
            current = int(m.group(1))
            tracks[current] = []
        elif _MEASURE_TOK.fullmatch(tok):
            continue
        elif current is not None:
            tracks[current].extend(int(c) for c in tok)
    return tracks


def read_finger_hints(synthesia_path: Path) -> str | None:
    root = ET.fromstring(synthesia_path.read_text(encoding="utf-8"))
    song = root.find(".//Song")
    if song is None:
        return None
    return song.get("FingerHints")


def midi_note_counts(midi_bytes: bytes) -> list[int]:
    """Note count per *note-bearing* track, remapped 0-based in track order.

    Mirrors the app's `midi_parser.dart`, which keeps only tracks that contain
    notes and re-indexes them by original MIDI track order.
    """
    mid = mido.MidiFile(file=io.BytesIO(midi_bytes))
    counts = []
    for track in mid.tracks:
        n = sum(1 for msg in track if msg.type == "note_on" and msg.velocity > 0)
        if n:
            counts.append(n)
    return counts


def build_fingering(midi_bytes: bytes, synthesia_path: Path, label: str) -> dict | None:
    """Build the `fingering.json` payload, or None if it can't be trusted.

    The per-track digit count must equal the track's note count; any mismatch
    means the hints won't bind correctly, so the whole file is skipped.
    """
    hints = read_finger_hints(synthesia_path)
    if not hints:
        log.warning("skip fingering for %s: no FingerHints in %s", label, synthesia_path.name)
        return None

    tracks = parse_finger_hints(hints)
    counts = midi_note_counts(midi_bytes)

    for track, fingers in sorted(tracks.items()):
        if track >= len(counts):
            log.warning(
                "skip fingering for %s: synthesia references track %d but MIDI has %d note tracks",
                label, track, len(counts),
            )
            return None
        if len(fingers) != counts[track]:
            log.warning(
                "skip fingering for %s: track %d has %d hints but %d notes",
                label, track, len(fingers), counts[track],
            )
            return None

    by_track = {str(track): fingers for track, fingers in sorted(tracks.items())}
    return {"version": FINGERING_VERSION, "byTrack": by_track}
