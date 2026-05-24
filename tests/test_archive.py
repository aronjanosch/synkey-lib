import hashlib
import io
import json
import zipfile

from synkey_lib.archive import md5_hex, pack_synkey
from synkey_lib.metadata import SongMeta


def test_md5_matches_hashlib(midi_bytes):
    assert md5_hex(midi_bytes) == hashlib.md5(midi_bytes).hexdigest()


def test_archive_entries_and_storage(midi_bytes):
    song = SongMeta(title="Levels", artist="Avicii", difficulty=2)
    data = pack_synkey(midi_bytes, song)

    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        assert sorted(zf.namelist()) == ["meta.json", "song.mid"]
        for info in zf.infolist():
            assert info.compress_type == zipfile.ZIP_STORED
        assert zf.read("song.mid") == midi_bytes
        meta = json.loads(zf.read("meta.json"))

    assert meta == {
        "version": 3,
        "contentHash": md5_hex(midi_bytes),
        "title": "Levels",
        "artist": "Avicii",
        "difficulty": 2,
        "description": "",
    }


def test_content_hash_is_midi_hash(midi_bytes):
    data = pack_synkey(midi_bytes, SongMeta(title="x"))
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        meta = json.loads(zf.read("meta.json"))
    assert meta["contentHash"] == md5_hex(midi_bytes)


def test_pack_is_deterministic(midi_bytes):
    song = SongMeta(title="x")
    assert pack_synkey(midi_bytes, song) == pack_synkey(midi_bytes, song)
