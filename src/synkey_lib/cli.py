"""Command-line entry point: build a SynKey remote library from MIDI files."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from .archive import md5_hex, pack_synkey
from .fingering import build_fingering, synthesia_path_for
from .manifest import build_manifest, normalize_base_url, song_entry, write_manifest
from .metadata import SongMeta, load_overrides, resolve, slugify, unique_slug

log = logging.getLogger("synkey_lib")

MIDI_SUFFIXES = {".mid", ".midi"}

# Archives live in a subfolder; manifest.json stays at the output root.
SONGS_DIR = "songs"


def find_midis(src_dir: Path) -> list[Path]:
    return sorted(
        p for p in src_dir.iterdir() if p.is_file() and p.suffix.lower() in MIDI_SUFFIXES
    )


def read_midi(path: Path) -> bytes | None:
    try:
        data = path.read_bytes()
    except OSError as exc:
        log.warning("skip %s: cannot read (%s)", path.name, exc)
        return None
    if not data.startswith(b"MThd"):
        log.warning("skip %s: not a MIDI file (missing MThd header)", path.name)
        return None
    return data


def build(args: argparse.Namespace) -> int:
    src_dir: Path = args.src_dir
    out_dir: Path = args.out_dir
    base_url = normalize_base_url(args.base_url)

    if not src_dir.is_dir():
        log.error("source is not a directory: %s", src_dir)
        return 1

    overrides = load_overrides(args.metadata) if args.metadata else {}

    midis = find_midis(src_dir)
    if not midis:
        log.error("no MIDI files found in %s", src_dir)
        return 1

    songs_dir = out_dir / SONGS_DIR
    if not args.dry_run:
        songs_dir.mkdir(parents=True, exist_ok=True)

    used_slugs: set[str] = set()
    produced: set[str] = set()
    songs: list[dict] = []

    for path in midis:
        midi_bytes = read_midi(path)
        if midi_bytes is None:
            continue

        meta = resolve(path.name, overrides)
        slug = unique_slug(slugify(f"{meta.artist} {meta.title}"), used_slugs)
        filename = f"{slug}.synkey"

        fingering = None
        synthesia = synthesia_path_for(path)
        if synthesia.is_file():
            fingering = build_fingering(midi_bytes, synthesia, path.name)

        synkey_bytes = pack_synkey(midi_bytes, meta, fingering)
        url = f"{base_url}/{SONGS_DIR}/{filename}"
        songs.append(song_entry(meta, md5_hex(midi_bytes), url, len(synkey_bytes)))
        produced.add(filename)

        if not args.dry_run:
            (songs_dir / filename).write_bytes(synkey_bytes)
        fp = " +fingering" if fingering else ""
        log.info("%s -> %s (%s, %d bytes%s)", path.name, filename, meta.title, len(synkey_bytes), fp)

    manifest = build_manifest(songs)

    if args.dry_run:
        print(json.dumps(manifest, ensure_ascii=False, indent=2))
        return 0

    write_manifest(out_dir, manifest)
    if args.clean:
        clean_stale(songs_dir, produced)

    log.info("wrote %d songs + manifest.json to %s", len(songs), out_dir)
    return 0


def clean_stale(songs_dir: Path, produced: set[str]) -> None:
    for path in songs_dir.glob("*.synkey"):
        if path.name not in produced:
            log.info("remove stale %s", path.name)
            path.unlink()


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="synkey-lib")
    sub = parser.add_subparsers(dest="command", required=True)

    b = sub.add_parser("build", help="build .synkey files + manifest.json from a MIDI folder")
    b.add_argument("src_dir", type=Path, help="folder containing *.mid files")
    b.add_argument("out_dir", type=Path, help="output folder for the library")
    b.add_argument("--base-url", required=True, help="host prefix the songs will be served from")
    b.add_argument("--metadata", type=Path, help="YAML file of per-filename metadata overrides")
    b.add_argument("--clean", action="store_true", help="remove *.synkey not produced this run")
    b.add_argument("--dry-run", action="store_true", help="print planned manifest, write nothing")
    b.add_argument("-v", "--verbose", action="store_true", help="verbose per-file log")
    b.set_defaults(func=build)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = make_parser().parse_args(argv)
    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(message)s",
    )
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
