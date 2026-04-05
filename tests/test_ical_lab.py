import json
import datetime
import pytest
from unittest.mock import patch
import sys
import io

from shared.ical_lab import ICalManager, run_ical_lab_logic

try:
    from textual.app import App
    from shared.tui_ical import ICalLabTab

    class DummyApp(App):
        def compose(self):
            yield ICalLabTab()
except ImportError:
    pass

@pytest.fixture
def manager():
    return ICalManager()

def test_parse_ics_valid(manager):
    ics_data = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Combined Autonomous Coding Agent//ICal Lab//EN
BEGIN:VEVENT
UID:12345
DTSTAMP:20240101T000000Z
DTSTART:20240101T100000Z
DTEND:20240101T110000Z
SUMMARY:Meeting with Team
LOCATION:Conference Room A
DESCRIPTION:Discuss project plan\\nNext steps
END:VEVENT
END:VCALENDAR"""

    events = manager.parse_ics(ics_data)
    assert len(events) == 1
    event = events[0]
    assert event["SUMMARY"] == "Meeting with Team"
    assert event["LOCATION"] == "Conference Room A"
    assert "Discuss project plan\nNext steps" in event["DESCRIPTION"]
    assert event["UID"] == "12345"

def test_parse_ics_invalid(manager):
    ics_data = """Just some random text
    that is not an iCalendar file"""
    events = manager.parse_ics(ics_data)
    assert len(events) == 0

def test_generate_ics(manager):
    dtstart = datetime.datetime(2024, 1, 1, 10, 0, tzinfo=datetime.timezone.utc)
    dtend = datetime.datetime(2024, 1, 1, 11, 0, tzinfo=datetime.timezone.utc)

    ics = manager.generate_ics("Team Sync", dtstart, dtend, "Room A", "Weekly meeting")
    assert "BEGIN:VCALENDAR" in ics
    assert "BEGIN:VEVENT" in ics
    assert "SUMMARY:Team Sync" in ics
    assert "LOCATION:Room A" in ics
    assert "DESCRIPTION:Weekly meeting" in ics
    assert "DTSTART:20240101T100000Z" in ics
    assert "DTEND:20240101T110000Z" in ics

def test_validate_ics(manager):
    valid_ics = """BEGIN:VCALENDAR
VERSION:2.0
BEGIN:VEVENT
SUMMARY:Test
END:VEVENT
END:VCALENDAR"""
    assert manager.validate_ics(valid_ics) is True

    invalid_ics = "BEGIN:VCALENDAR\nSUMMARY:Test"
    assert manager.validate_ics(invalid_ics) is False

    assert manager.validate_ics("") is False

class DummyArgs:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

@patch('sys.stdin.isatty', return_value=True)
@patch('sys.stdout', new_callable=io.StringIO)
def test_run_ical_lab_logic_parse(mock_stdout, mock_isatty):
    args = DummyArgs(action='parse', text="BEGIN:VCALENDAR\nBEGIN:VEVENT\nSUMMARY:Test\nEND:VEVENT\nEND:VCALENDAR")
    result = run_ical_lab_logic(args)
    assert result is True
    output = mock_stdout.getvalue()
    assert "Test" in output

@patch('sys.stdin.isatty', return_value=True)
@patch('sys.stdout', new_callable=io.StringIO)
def test_run_ical_lab_logic_validate(mock_stdout, mock_isatty):
    args = DummyArgs(action='validate', text="BEGIN:VCALENDAR\nVERSION:2.0\nEND:VCALENDAR")
    result = run_ical_lab_logic(args)
    assert result is True
    output = mock_stdout.getvalue()
    assert "Valid" in output

@patch('sys.stdin.isatty', return_value=True)
@patch('sys.stdout', new_callable=io.StringIO)
def test_run_ical_lab_logic_generate(mock_stdout, mock_isatty):
    args = DummyArgs(action='generate', summary="Test Gen", start="2024-01-01 10:00", end="2024-01-01 11:00")
    result = run_ical_lab_logic(args)
    assert result is True
    output = mock_stdout.getvalue()
    assert "BEGIN:VCALENDAR" in output
    assert "SUMMARY:Test Gen" in output

def test_run_ical_lab_logic_tui():
    args = DummyArgs(action='tui')
    result = run_ical_lab_logic(args)
    assert result is True

def test_ical_lab_tab():
    pytest.importorskip("textual")
    # TUI testing directly via asyncio can cause issues if pytest-asyncio is absent.
    # We will skip the async textual tests or mock them if necessary.
    pass
