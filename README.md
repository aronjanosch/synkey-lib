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
- `<out_dir>` — output folder (`manifest.json` + `<slug>.synkey`), served flat.
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

## Output format

Each `.synkey` is a `ZIP_STORED` archive of `song.mid` + `meta.json`
(`version: 3`, `contentHash` = MD5 of the MIDI bytes). `manifest.json`
(`version: 1`) lists each song with its `contentHash`, `url`, and `size` (byte
length of the archive). The app re-verifies hash and size on download.

## Development

```sh
uv run pytest
```

MIDI-only in v1. Synthesia fingering conversion is a planned phase 2.
