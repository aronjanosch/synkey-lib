from pathlib import Path

from synkey_lib.fingering import (
    build_fingering,
    midi_note_counts,
    parse_finger_hints,
)

FIXTURES = Path(__file__).parent / "fixtures"


def test_parse_finger_hints_drops_markers():
    tracks = parse_finger_hints("t0: m1: 767 m2: 060 t1: m1: 5")
    assert tracks == {0: [7, 6, 7, 0, 6, 0], 1: [5]}


def test_ff7_note_counts():
    counts = midi_note_counts((FIXTURES / "ff7.mid").read_bytes())
    assert counts == [158, 299]


def test_build_fingering_ff7():
    fingering = build_fingering(
        (FIXTURES / "ff7.mid").read_bytes(), FIXTURES / "ff7.synthesia", "ff7"
    )
    assert fingering["version"] == 1
    assert set(fingering["byTrack"]) == {"0", "1"}
    assert len(fingering["byTrack"]["0"]) == 158
    assert len(fingering["byTrack"]["1"]) == 299


def test_build_fingering_count_mismatch_returns_none(tmp_path):
    # tiny.mid has no notes; any synthesia track count won't match -> skip
    bad = tmp_path / "x.synthesia"
    bad.write_text('<SynthesiaMetadata><Songs><Song FingerHints="t0: 12345"/></Songs></SynthesiaMetadata>')
    result = build_fingering((FIXTURES / "ff7.mid").read_bytes(), bad, "x")
    assert result is None
