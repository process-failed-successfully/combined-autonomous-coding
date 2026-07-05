import pytest
from unittest.mock import patch, MagicMock
from shared.ntp_lab import NtpLabManager, run_ntp_lab_logic
import struct
import argparse
import sys

@pytest.fixture
def manager():
    return NtpLabManager()

def test_ntp_to_system_time(manager):
    # Test with 0 timestamp
    assert manager._ntp_to_system_time(manager.NTP_TIMESTAMP_DELTA << 32) == 0.0

def test_unpack_timestamp(manager):
    data = struct.pack('!Q', manager.NTP_TIMESTAMP_DELTA << 32)
    assert manager._unpack_timestamp(data, 0) == 0.0

    data_zero = struct.pack('!Q', 0)
    assert manager._unpack_timestamp(data_zero, 0) == 0.0

@patch('socket.socket')
def test_query_success(mock_socket_class, manager):
    mock_socket = MagicMock()
    mock_socket_class.return_value = mock_socket

    # Construct a valid NTP packet response (48 bytes)
    # LI=0, VN=3, Mode=4 -> 0x1c
    # Stratum=2, Poll=10, Precision=-20
    # Ref ID: 127.0.0.1
    # 0x1c, 0x02, 0x0a, 0xec
    li_vn_mode = (0 << 6) | (3 << 3) | 4
    header = struct.pack('!B B B B I I 4s', li_vn_mode, 2, 10, 236, 0, 0, b'\x7f\x00\x00\x01')

    # Fake timestamps
    ts_bytes = struct.pack('!Q', manager.NTP_TIMESTAMP_DELTA << 32)

    packet = header + (ts_bytes * 4) # ref, orig, recv, tx

    mock_socket.recvfrom.return_value = (packet, ('127.0.0.1', 123))

    result = manager.query('127.0.0.1')

    assert result["valid"] is True
    assert result["server"] == "127.0.0.1"
    assert result["version"] == 3
    assert result["mode"] == 4
    assert result["stratum"] == 2
    assert result["reference_id"] == "127.0.0.1"

@patch('socket.socket')
def test_query_invalid_length(mock_socket_class, manager):
    mock_socket = MagicMock()
    mock_socket_class.return_value = mock_socket

    mock_socket.recvfrom.return_value = (b'short', ('127.0.0.1', 123))

    result = manager.query('127.0.0.1')
    assert result["valid"] is False
    assert "Invalid NTP packet" in result["error"]

@patch('socket.socket')
def test_query_timeout(mock_socket_class, manager):
    mock_socket = MagicMock()
    mock_socket_class.return_value = mock_socket

    import socket
    mock_socket.recvfrom.side_effect = socket.timeout("timed out")

    result = manager.query('127.0.0.1')
    assert result["valid"] is False
    assert "timed out" in result["error"]

@patch('shared.ntp_lab.NtpLabManager.query')
def test_run_ntp_lab_logic(mock_query, capsys):
    mock_query.return_value = {
        "valid": True,
        "server": "pool.ntp.org",
        "address": "1.2.3.4",
        "version": 4,
        "mode": 4,
        "leap_indicator": 0,
        "stratum": 2,
        "reference_id": "8.8.8.8",
        "precision": -20,
        "offset_ms": 1.5,
        "delay_ms": 10.0,
        "reference_timestamp": 0.0,
        "origin_timestamp": 0.0,
        "receive_timestamp": 0.0,
        "transmit_timestamp": 0.0
    }
    args = argparse.Namespace(action="query", server="pool.ntp.org", port=123, timeout=5)

    with pytest.raises(SystemExit) as e:
        run_ntp_lab_logic(args)

    assert e.value.code == 0
    captured = capsys.readouterr()
    assert "NTP Response from pool.ntp.org" in captured.out
    assert "Offset:          1.500 ms" in captured.out

@patch('shared.ntp_lab.NtpLabManager.query')
def test_run_ntp_lab_logic_error(mock_query, capsys):
    mock_query.return_value = {
        "valid": False,
        "error": "timed out"
    }
    args = argparse.Namespace(action="query", server="pool.ntp.org", port=123, timeout=5)

    with pytest.raises(SystemExit) as e:
        run_ntp_lab_logic(args)

    assert e.value.code == 1
    captured = capsys.readouterr()
    assert "NTP Error: timed out" in captured.err
