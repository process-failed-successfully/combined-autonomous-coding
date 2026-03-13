"""
Morse Code Lab
==============

Provides utilities for encoding, decoding, and generating audio for Morse Code.
"""

import sys
import math
import wave
import struct
from pathlib import Path
from typing import Dict, Tuple

MORSE_CODE_DICT: Dict[str, str] = {
    'A': '.-', 'B': '-...', 'C': '-.-.', 'D': '-..', 'E': '.', 'F': '..-.',
    'G': '--.', 'H': '....', 'I': '..', 'J': '.---', 'K': '-.-', 'L': '.-..',
    'M': '--', 'N': '-.', 'O': '---', 'P': '.--.', 'Q': '--.-', 'R': '.-.',
    'S': '...', 'T': '-', 'U': '..-', 'V': '...-', 'W': '.--', 'X': '-..-',
    'Y': '-.--', 'Z': '--..', '0': '-----', '1': '.----', '2': '..---',
    '3': '...--', '4': '....-', '5': '.....', '6': '-....', '7': '--...',
    '8': '---..', '9': '----.', '.': '.-.-.-', ',': '--..--', '?': '..--..',
    "'": '.----.', '!': '-.-.--', '/': '-..-.', '(': '-.--.', ')': '-.--.-',
    '&': '.-...', ':': '---...', ';': '-.-.-.', '=': '-...-', '+': '.-.-.',
    '-': '-....-', '_': '..--.-', '"': '.-..-.', '$': '...-..-', '@': '.--.-.',
    ' ': '/'
}

REVERSE_MORSE_DICT: Dict[str, str] = {value: key for key, value in MORSE_CODE_DICT.items()}


class MorseLabManager:
    """Manages Morse Code encoding, decoding, and audio generation."""

    def encode(self, text: str) -> str:
        """Encodes standard text into Morse Code."""
        if not text:
            return ""

        encoded_chars = []
        for char in text.upper():
            if char in MORSE_CODE_DICT:
                encoded_chars.append(MORSE_CODE_DICT[char])
            else:
                # Keep unknown characters as is or ignore? Let's ignore or replace with '?'
                pass

        return " ".join(encoded_chars)

    def decode(self, morse_text: str) -> str:
        """Decodes Morse Code into standard text. Words are separated by / or double spaces."""
        if not morse_text:
            return ""

        # Standardize separators. Sometimes multiple spaces represent a word break.
        # But we'll rely on the encoded output which uses '/' for space.
        # If user typed '.-   .-', we'll split by space.

        decoded_chars = []

        # Split by words first if '/' is used
        if '/' in morse_text:
            words = morse_text.split('/')
            for word in words:
                chars = word.strip().split()
                decoded_word = "".join(REVERSE_MORSE_DICT.get(c, '?') for c in chars if c)
                if decoded_word:
                    decoded_chars.append(decoded_word)
            return " ".join(decoded_chars)
        else:
            # Maybe just split by spaces. 3 spaces is a word break in some conventions.
            # Let's replace '   ' with ' / ' to simplify.
            standardized = morse_text.replace('   ', ' / ')
            words = standardized.split(' / ')
            for word in words:
                chars = word.strip().split()
                decoded_word = "".join(REVERSE_MORSE_DICT.get(c, '?') for c in chars if c)
                if decoded_word:
                    decoded_chars.append(decoded_word)
            return " ".join(decoded_chars)

    def generate_audio(self, morse_text: str, output_path: Path, wpm: int = 15, freq: int = 800) -> bool:
        """
        Generates a WAV file from the Morse code string.
        wpm: Words per minute (determines dot length. Standard PARIS word is 50 dots. Dot = 1.2 / wpm seconds)
        freq: Frequency of the tone in Hz.
        """
        if not morse_text:
            return False

        try:
            dot_duration = 1.2 / wpm
            sample_rate = 44100

            # Generate basic tones
            def generate_tone(duration_sec: float) -> bytes:
                num_samples = int(sample_rate * duration_sec)
                # Apply a slight envelope to prevent audio popping (fade in/out)
                fade_samples = int(sample_rate * 0.01) # 10ms fade

                samples = []
                for i in range(num_samples):
                    t = float(i) / sample_rate
                    val = math.sin(2.0 * math.pi * freq * t)

                    # Envelope
                    env = 1.0
                    if i < fade_samples:
                        env = i / fade_samples
                    elif i > num_samples - fade_samples:
                        env = (num_samples - i) / fade_samples

                    val *= env

                    # Convert to 16-bit signed integer
                    sample_int = int(val * 32767.0)
                    samples.append(struct.pack('<h', sample_int))
                return b''.join(samples)

            def generate_silence(duration_sec: float) -> bytes:
                num_samples = int(sample_rate * duration_sec)
                return b''.join([struct.pack('<h', 0) for _ in range(num_samples)])

            dot_tone = generate_tone(dot_duration)
            dash_tone = generate_tone(dot_duration * 3.0)
            intra_char_silence = generate_silence(dot_duration)
            inter_char_silence = generate_silence(dot_duration * 3.0)
            inter_word_silence = generate_silence(dot_duration * 7.0)

            audio_data = b''

            # Use standard parser for spaces
            standardized = morse_text.replace('   ', ' / ')
            words = standardized.split('/')

            for w_idx, word in enumerate(words):
                chars = word.strip().split()
                for c_idx, char in enumerate(chars):
                    for s_idx, symbol in enumerate(char):
                        if symbol == '.':
                            audio_data += dot_tone
                        elif symbol == '-':
                            audio_data += dash_tone
                        else:
                            continue # Ignore invalid symbols in audio

                        # Intra-character spacing (between dots and dashes)
                        if s_idx < len(char) - 1:
                            audio_data += intra_char_silence

                    # Inter-character spacing (between letters)
                    if c_idx < len(chars) - 1:
                        audio_data += inter_char_silence

                # Inter-word spacing
                if w_idx < len(words) - 1:
                    audio_data += inter_word_silence

            # Write to WAV
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with wave.open(str(output_path), 'w') as wav_file:
                wav_file.setnchannels(1) # Mono
                wav_file.setsampwidth(2) # 16-bit
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(audio_data)

            return True
        except Exception as e:
            print(f"Error generating audio: {e}", file=sys.stderr)
            return False


def run_morse_lab_logic(args) -> bool:
    """CLI logic for the Morse Lab."""
    manager = MorseLabManager()

    if getattr(args, "action", None) == "tui":
        # Launch handled in main.py, but just in case
        return True

    text = args.text
    if not text and not sys.stdin.isatty():
        text = sys.stdin.read().strip()

    if not text:
        print("Error: Input text required either via argument or stdin.", file=sys.stderr)
        return False

    try:
        # Auto-detect encode/decode based on character set
        is_morse = all(c in '.-/ \n\t' for c in text)

        if getattr(args, "decode", False):
            mode = "decode"
        elif getattr(args, "encode", False):
            mode = "encode"
        else:
            mode = "decode" if is_morse else "encode"

        if mode == "encode":
            result = manager.encode(text)
            print(result)
            morse_for_audio = result
        else:
            result = manager.decode(text)
            print(result)
            morse_for_audio = text

        if getattr(args, "audio", None):
            out_path = Path(args.audio).resolve()
            success = manager.generate_audio(morse_for_audio, out_path, wpm=getattr(args, 'wpm', 15), freq=getattr(args, 'freq', 800))
            if success:
                print(f"✅ Audio generated successfully to {out_path.name}")
            else:
                print(f"❌ Failed to generate audio.")
                return False

        return True
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        return False
