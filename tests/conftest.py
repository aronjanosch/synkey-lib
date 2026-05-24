from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def midi_bytes() -> bytes:
    return (FIXTURES / "tiny.mid").read_bytes()
