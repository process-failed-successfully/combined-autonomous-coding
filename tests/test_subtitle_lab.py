import unittest
from pathlib import Path
from unittest.mock import MagicMock
from shared.subtitle_lab import SubtitleLabManager

class TestSubtitleLab(unittest.TestCase):
    def setUp(self):
        self.manager = SubtitleLabManager()

    def test_timestamp_to_seconds(self):
        # SRT style
        self.assertAlmostEqual(self.manager._timestamp_to_seconds("00:00:01,500"), 1.5)
        self.assertAlmostEqual(self.manager._timestamp_to_seconds("01:00:00,000"), 3600.0)
        # VTT style
        self.assertAlmostEqual(self.manager._timestamp_to_seconds("00:00:01.500"), 1.5)
        # Short format
        self.assertAlmostEqual(self.manager._timestamp_to_seconds("00:01.500"), 1.5)

    def test_seconds_to_timestamp(self):
        self.assertEqual(self.manager._seconds_to_timestamp(1.5, ","), "00:00:01,500")
        self.assertEqual(self.manager._seconds_to_timestamp(3600.0, ","), "01:00:00,000")
        self.assertEqual(self.manager._seconds_to_timestamp(1.5, "."), "00:00:01.500")

    def test_parse_srt(self):
        content = """1
00:00:01,000 --> 00:00:04,000
Hello World

2
00:00:05,000 --> 00:00:09,000
Second Line
"""
        captions = self.manager.parse_srt(content)
        self.assertEqual(len(captions), 2)
        self.assertEqual(captions[0]["index"], 1)
        self.assertEqual(captions[0]["start"], 1.0)
        self.assertEqual(captions[0]["end"], 4.0)
        self.assertEqual(captions[0]["text"], "Hello World")

    def test_parse_vtt(self):
        content = """WEBVTT

1
00:00:01.000 --> 00:00:04.000 align:start
Hello World

00:00:05.000 --> 00:00:09.000
Second Line
"""
        captions = self.manager.parse_vtt(content)
        self.assertEqual(len(captions), 2)
        self.assertEqual(captions[0]["index"], 1)
        self.assertEqual(captions[0]["start"], 1.0)
        self.assertEqual(captions[0]["end"], 4.0)
        self.assertEqual(captions[0]["text"], "Hello World")
        # Check second one auto-indexed
        self.assertEqual(captions[1]["index"], 2)

    def test_shift_timing(self):
        captions = [{"index": 1, "start": 1.0, "end": 4.0, "text": "Test"}]
        shifted = self.manager.shift_timing(captions, 1.5)
        self.assertEqual(shifted[0]["start"], 2.5)
        self.assertEqual(shifted[0]["end"], 5.5)

        # Test negative shift clamping
        shifted_neg = self.manager.shift_timing(captions, -2.0)
        self.assertEqual(shifted_neg[0]["start"], 0.0) # Clamped
        self.assertEqual(shifted_neg[0]["end"], 2.0)

    def test_clean_text(self):
        captions = [{"index": 1, "start": 1.0, "end": 4.0, "text": "<b>Bold</b> and <i>Italic</i>"}]
        cleaned = self.manager.clean_text(captions)
        self.assertEqual(cleaned[0]["text"], "Bold and Italic")

    def test_to_srt(self):
        captions = [{"index": 1, "start": 1.0, "end": 4.0, "text": "Test"}]
        srt = self.manager.to_srt(captions)
        expected = "1\n00:00:01,000 --> 00:00:04,000\nTest\n"
        self.assertEqual(srt.strip(), expected.strip())

if __name__ == "__main__":
    unittest.main()
