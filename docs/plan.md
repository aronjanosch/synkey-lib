# synkey-lib — implementation plan

CLI tool that turns a folder of MIDI files into a publishable **SynKey remote
library**: a set of `.synkey` archives plus a `manifest.json` that the SynKey
app fetches over plain HTTP (GitHub raw / Pages / any static host).

Separate public repo from the SynKey Flutter app. Distributable via `pipx`.

## Goals

- One command: folder of `*.mid` in → `.synkey` files + `manifest.json` out.
- Output is byte-compatible with what the app expects (verified against the
  app's `synkey_archive.dart` and `remote_library.dart`).
- Usable by other people on their own MIDI libraries, not just internal tooling.
- Clean human metadata (title/artist/difficulty) with an override path for the
  filenames that can't be parsed.

## Non-goals (v1)

- Synthesia fingering conversion — **deferred to a follow-up** (see below).
- Quantize-to-MusicXML (`musicxml.xml` slot). App generates that on import.
- Hosting/upload automation. User pushes the output dir to a git repo manually.
- GUI.

## Decisions (locked)

- Repo: `~/Projects/synkey-lib`, console command `synkey-lib`.
- Packaging: `pyproject.toml` + `console_scripts` (hatchling), `pipx install`.
- v1 scope: MIDI-only. Synthesia conversion is a phase 2.
- Python ≥ 3.10. Only runtime dep: `PyYAML` (metadata override file).

## Target formats (authoritative source: the app)

### `.synkey` archive

ZIP with **`ZIP_STORED`** (no deflate). Entry names must match exactly:

| entry           | required | v1   |
|-----------------|----------|------|
| `song.mid`      | yes      | yes  |
| `meta.json`     | yes      | yes  |
| `fingering.json`| no       | phase 2 |
| `musicxml.xml`  | no       | never (app-generated) |

`meta.json`:

```json
{
  "version": 3,
  "contentHash": "<md5 hex of song.mid bytes>",
  "title": "...",
  "artist": "...",
  "difficulty": 0,
  "description": ""
}
```

- `contentHash` = `md5(midi_bytes)` hex — must equal Dart `hashMidiBytes`
  (`crypto.md5`). The app re-derives it on download and **rejects on mismatch**
  (`_verifyHash` in `remote_library_controller.dart`).
- `version` = 3 (current `_formatVersion`). Tool hardcodes this; bump
  deliberately when the app's format version changes.

### `manifest.json`

```json
{
  "version": 1,
  "songs": [
    {
      "title": "...",
      "artist": "...",
      "difficulty": 0,
      "contentHash": "<same md5 as in meta.json>",
      "url": "<base-url>/<file>.synkey",
      "size": 12345
    }
  ]
}
```

- `size` = **byte length of the `.synkey` archive** (not the MIDI). App checks
  `bytes.length != size` in `downloadSong` and throws on mismatch.
- `url` = `--base-url` joined with the archive filename.
- Fields that may be empty default safely in the app
  (`RemoteManifest.fromJson`), but we always emit them.

## CLI surface

```
synkey-lib build <src_dir> <out_dir> --base-url <URL> [--metadata <file.yaml>]
                 [--clean] [--dry-run] [-v]
```

- `build` — scan `<src_dir>` for `*.mid`, write `.synkey` files + `manifest.json`
  into `<out_dir>`.
- `--base-url` — host prefix the songs will be served from; used to build each
  `url`. Trailing slash normalized.
- `--metadata` — optional YAML overrides (see below).
- `--clean` — wipe stale `*.synkey` in `<out_dir>` not produced this run.
- `--dry-run` — print planned manifest, write nothing.
- `-v` — verbose per-file log.

Output layout (flat — manifest and songs served from the same dir):

```
<out_dir>/
  manifest.json
  <slug>.synkey
  ...
```

## Metadata resolution

Per source file, fields resolved in priority order:

1. **Override file** (`--metadata`), keyed by source filename.
2. **Filename heuristic.**
3. Defaults (`difficulty: 0`, `description: ""`).

Override YAML shape:

```yaml
"Stairway_to_Heaven_-_Led_Zeppelin.mid":
  title: "Stairway to Heaven"
  artist: "Led Zeppelin"
  difficulty: 4
"Avicii - Levels.mid":
  difficulty: 2
```

Filename heuristic (best-effort, documented as imperfect):

- Drop extension.
- Strip bracket/paren junk: `[MIDICollection.net]`, `(Easy Piano)`,
  `(hands are divided)` → removed from title.
- `_` → space, collapse whitespace.
- Split on ` - `: **left = artist, right = title** (matches the majority:
  "Avicii - Levels", "Linkin Park - Numb", "Coldplay - The Scientist").
  - Known exception: "Title - Artist" files (e.g. Stairway) → fix via override.
- No ` - ` → whole thing is title, artist empty.

`slug` for the output filename: lowercase, non-alphanumeric → `-`, collapsed
(e.g. `coldplay-the-scientist.synkey`). Keeps URLs clean; display name comes
from `meta.json`, not the filename, so an ugly-safe slug is fine. Collisions
get a numeric suffix.

## Module layout

```
src/synkey_lib/
  __init__.py
  archive.py    # pack_synkey(midi_bytes, meta) -> bytes; md5; ZIP_STORED writer
  metadata.py   # SongMeta dataclass; filename heuristic; YAML override merge
  manifest.py   # build manifest dict from built entries; JSON writer
  cli.py        # argparse, build command, orchestration, logging
tests/
  test_archive.py   # round-trip: pack -> unzip, entries present, md5 stable
  test_metadata.py  # heuristic + override precedence + slug/collision
  test_manifest.py  # size/url/contentHash wiring
  fixtures/         # one tiny .mid
```

## Correctness checks the tool enforces

- `meta.contentHash == md5(song.mid)` — the value the app re-verifies.
- `manifest.size == len(synkey_bytes)` — the value the app re-verifies.
- ZIP is `ZIP_STORED`; entry names exact.
- Skip non-MIDI files; warn on `.mid` that fails to read.
- `--clean` only removes `*.synkey`, never touches unknown files.

## Validation before trusting a batch

1. Build the library from `~/Music/synkey`.
2. Serve `<out_dir>` (push to a GitHub repo; use raw URL as `--base-url`, or
   `python -m http.server` for a quick local check).
3. In the app: add the manifest URL, download one song, confirm it imports and
   plays. This exercises both app-side verifications (size + hash).

## Phase 2 — Synthesia fingering (separate task)

Source: `.synthesia` XML (`SynthesiaMetadata`) sibling to a `.mid`, e.g.
`Final_Fantasy_VII_Main_Theme.synthesia`. `FingerHints` attribute:

```
t0: m1: 767 m2: 060 ...   t1: m1: 531 m2: 521 ...
```

- `tN:` = track N, `mK:` = measure K (markers only, for readability), digits =
  one finger (1–5) per note, `0` = no hint.
- Target: `.synkey` `fingering.json` →
  `{ "version": 1, "byTrack": { "0": [..], "1": [..] } }`.

**Alignment rules (from the app's `midi_parser.dart`):**

- App keeps **only note-bearing tracks**, remapped to 0-based, sorted by
  original MIDI track index. Synthesia `t0`/`t1` should map to these same
  indices — must verify per file.
- Within a track, notes are sorted by `startTick`; finger `i` binds to the
  `i`-th note in that order.
- **Invariant:** concatenated digit count for `tN` must equal note count in
  track `N`. Mismatch → warn loudly, skip fingering for that file.
- **Fragile spot:** chords (same `startTick`). Dart `List.sort` is not stable,
  so within-chord order is undefined app-side. Tool will sort `(startTick,
  pitch asc)`; chords may still mis-bind. Validate FF7 in-app first.

Phase 2 adds a MIDI parser dep (e.g. `mido`) to count/order notes per track.
Keep it out of v1 so the core tool stays dependency-light.

## Open questions

- `--base-url` for GitHub raw has caching lag; GitHub Pages or a release asset
  is cleaner long-term. Doc both, pick at publish time.
- Whether to emit a `library.json`-style name/description header for the library
  itself (app currently only consumes `manifest.json` song list). Defer until
  the app supports it.
