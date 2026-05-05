import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))  # noqa: E402

import pytest
from shared.vin_lab import VinManager


@pytest.fixture
def manager():
    return VinManager()


def test_validate_valid_vin(manager):
    # A known valid VIN (e.g. a random real one)
    assert manager.validate("1HGCM82633A004352") is True


def test_validate_invalid_length(manager):
    assert manager.validate("1HGCM82633") is False


def test_validate_invalid_chars(manager):
    # 'O' is invalid
    assert manager.validate("1HGCM82633A00435O") is False
    # 'I' is invalid
    assert manager.validate("1HGCM82633A00435I") is False
    # 'Q' is invalid
    assert manager.validate("1HGCM82633A00435Q") is False


def test_validate_invalid_checksum(manager):
    # Valid is 1HGCM82633A004352, so change one char to break checksum
    assert manager.validate("1HGCM82633A004353") is False


def test_decode_valid_vin(manager):
    decoded = manager.decode("1HGCM82633A004352")

    assert decoded["vin"] == "1HGCM82633A004352"
    assert decoded["is_valid"] is True
    assert decoded["wmi"] == "1HG"
    assert decoded["vds"] == "CM8263"
    assert decoded["vis"] == "3A004352"
    assert decoded["region"] == "North America"
    # Year logic: '3' is 2003, and 7th char '8' is a digit -> base cycle (1980-2009)
    assert decoded["year"] == 2003
    assert decoded["plant_code"] == "A"
    assert decoded["serial_number"] == "004352"


def test_decode_invalid_length(manager):
    with pytest.raises(ValueError, match="Invalid VIN format or length."):
        manager.decode("1HGCM82633A0043")


def test_guess_year_pre_2010(manager):
    # 'Y' = 2000, 7th char = '1' (digit -> pre-2010 cycle)
    assert manager._guess_year('Y', '1') == 2000


def test_guess_year_post_2010(manager):
    # 'Y' = 2000, 7th char = 'A' (alpha -> post-2010 cycle)
    assert manager._guess_year('Y', 'A') == 2030
