import pytest

from synkey_lib.metadata import (
    heuristic_from_filename,
    resolve,
    slugify,
    unique_slug,
)


@pytest.mark.parametrize(
    "filename, artist, title",
    [
        ("Avicii - Levels.mid", "Avicii", "Levels"),
        ("Linkin Park - Numb.mid", "Linkin Park", "Numb"),
        ("Coldplay_-_The_Scientist.mid", "Coldplay", "The Scientist"),
        ("He's a Pirate - Pirates [MIDICollection.net].mid", "He's a Pirate", "Pirates"),
        ("Billie Eilish - No Time To Die (hands are divided).mid", "Billie Eilish", "No Time To Die"),
        ("Zelda's Lullaby.mid", "", "Zelda's Lullaby"),
    ],
)
def test_heuristic(filename, artist, title):
    meta = heuristic_from_filename(filename)
    assert meta.artist == artist
    assert meta.title == title


def test_override_precedence():
    overrides = {
        "Stairway_to_Heaven_-_Led_Zeppelin.mid": {
            "title": "Stairway to Heaven",
            "artist": "Led Zeppelin",
            "difficulty": 4,
        }
    }
    meta = resolve("Stairway_to_Heaven_-_Led_Zeppelin.mid", overrides)
    assert meta.title == "Stairway to Heaven"
    assert meta.artist == "Led Zeppelin"
    assert meta.difficulty == 4


def test_partial_override_keeps_heuristic():
    meta = resolve("Avicii - Levels.mid", {"Avicii - Levels.mid": {"difficulty": 2}})
    assert meta.artist == "Avicii"
    assert meta.title == "Levels"
    assert meta.difficulty == 2


def test_defaults_without_override():
    meta = resolve("Avicii - Levels.mid", {})
    assert meta.difficulty == 0
    assert meta.description == ""


def test_slugify():
    assert slugify("Coldplay The Scientist") == "coldplay-the-scientist"
    assert slugify("He's a Pirate!") == "he-s-a-pirate"


def test_unique_slug_collision():
    used: set[str] = set()
    assert unique_slug("numb", used) == "numb"
    assert unique_slug("numb", used) == "numb-2"
    assert unique_slug("numb", used) == "numb-3"
