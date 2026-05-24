# synkey-lib

CLI that turns a folder of MIDI files into a publishable **SynKey remote
library**: a set of `.synkey` archives plus a `manifest.json` that the SynKey
app fetches over plain HTTP (GitHub raw / Pages / any static host).

## Install

```sh
pipx install .
# or, from a checkout:
uv run synkey-lib --help
```

## Usage

```sh
synkey-lib build <src_dir> <out_dir> --base-url <URL> \
    [--metadata meta.yaml] [--clean] [--dry-run] [-v]
```

- `<src_dir>` — folder of `*.mid` files.
- `<out_dir>` — output folder: `manifest.json` at the root, `<slug>.synkey`
  archives under `songs/`.
- `--base-url` — host prefix the songs are served from; used to build each `url`.
- `--metadata` — YAML overrides keyed by source filename.
- `--clean` — remove stale `*.synkey` not produced this run.
- `--dry-run` — print the planned manifest, write nothing.

Example serving from a GitHub repo via raw URLs:

```sh
synkey-lib build ~/Music/synkey out \
    --base-url https://raw.githubusercontent.com/<user>/<repo>/main
```

### Metadata overrides

The filename heuristic guesses `artist - title`. Fix exceptions in a YAML file:

```yaml
"Stairway_to_Heaven_-_Led_Zeppelin.mid":
  title: "Stairway to Heaven"
  artist: "Led Zeppelin"
  difficulty: 4
```

## Synthesia fingering

If a `.mid` has a sibling `<name>.synthesia` file, its `FingerHints` are
converted to a `fingering.json` entry inside the archive
(`{"version": 1, "byTrack": {"0": [...], ...}}`). Per-track hint counts must
equal the MIDI's per-track note counts; on any mismatch the fingering is
skipped (with a warning) and the rest of the archive is built normally.

## Output format

Each `.synkey` is a `ZIP_STORED` archive of `song.mid` + `meta.json`
(`version: 3`, `contentHash` = MD5 of the MIDI bytes), plus an optional
`fingering.json`. `manifest.json` (`version: 1`) lists each song with its
`contentHash`, `url`, and `size` (byte length of the archive). The app
re-verifies hash and size on download.

## Development

```sh
uv run pytest
```
