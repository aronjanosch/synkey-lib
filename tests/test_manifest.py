from synkey_lib.archive import md5_hex, pack_synkey
from synkey_lib.manifest import (
    build_manifest,
    normalize_base_url,
    song_entry,
)
from synkey_lib.metadata import SongMeta


def test_normalize_base_url():
    assert normalize_base_url("https://host/lib/") == "https://host/lib"
    assert normalize_base_url("https://host/lib") == "https://host/lib"


def test_song_entry_wiring(midi_bytes):
    meta = SongMeta(title="Levels", artist="Avicii", difficulty=2)
    data = pack_synkey(midi_bytes, meta)
    entry = song_entry(meta, md5_hex(midi_bytes), "https://host/lib/avicii-levels.synkey", len(data))

    assert entry == {
        "title": "Levels",
        "artist": "Avicii",
        "difficulty": 2,
        "contentHash": md5_hex(midi_bytes),
        "url": "https://host/lib/avicii-levels.synkey",
        "size": len(data),
    }


def test_size_is_archive_length(midi_bytes):
    meta = SongMeta(title="x")
    data = pack_synkey(midi_bytes, meta)
    entry = song_entry(meta, md5_hex(midi_bytes), "u", len(data))
    assert entry["size"] == len(data)
    assert entry["size"] != len(midi_bytes)


def test_build_manifest_shape():
    manifest = build_manifest([{"title": "a"}])
    assert manifest["version"] == 1
    assert manifest["songs"] == [{"title": "a"}]
