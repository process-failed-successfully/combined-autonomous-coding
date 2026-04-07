import pytest
from shared.endian_lab import EndianManager

def test_hex_swap():
    manager = EndianManager()

    assert manager.hex_swap("12345678") == "78563412"
    assert manager.hex_swap("0x12345678") == "0x78563412"
    assert manager.hex_swap("AABBCCDD") == "DDCCBBAA"
    assert manager.hex_swap("0xAABBCCDD") == "0xDDCCBBAA"

    # Odd length test
    assert manager.hex_swap("123") == "2301"

def test_int_swap():
    manager = EndianManager()

    # 16 bit
    assert manager.int_swap(0x1234, 16) == 0x3412
    # 32 bit
    assert manager.int_swap(0x12345678, 32) == 0x78563412
    # 64 bit
    assert manager.int_swap(0x1122334455667788, 64) == 0x8877665544332211

    with pytest.raises(ValueError):
        manager.int_swap(0x1234, 24)
