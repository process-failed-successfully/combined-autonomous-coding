import wave
import math
import struct
import random
import sys
from pathlib import Path
from typing import Optional, List

class SoundLabManager:
    """
    Manages audio generation tasks (tones, noise, DTMF, Morse).
    """

    def __init__(self, project_dir: Optional[Path] = None):
        self.project_dir = project_dir or Path(".")

    def _write_wav(self, output_path: Path, samples: List[float], sample_rate: int = 44100):
        """Writes normalized float samples (-1.0 to 1.0) to a WAV file."""
        with wave.open(str(output_path), 'w') as wav_file:
            n_channels = 1
            sampwidth = 2  # 2 bytes (16-bit)
            n_frames = len(samples)

            wav_file.setparams((n_channels, sampwidth, sample_rate, n_frames, 'NONE', 'not compressed'))

            # Convert float samples to 16-bit integers
            # Max amplitude for 16-bit is 32767
            int_samples = []
            for s in samples:
                # Clip to -1.0 to 1.0
                s = max(min(s, 1.0), -1.0)
                int_samples.append(int(s * 32767.0))

            # Pack data
            data = struct.pack('<' + 'h' * len(int_samples), *int_samples)
            wav_file.writeframes(data)

    def generate_tone(self, frequency: float, duration: float, waveform: str = "sine", output_path: str = "tone.wav", sample_rate: int = 44100, amplitude: float = 0.5):
        """Generates a tone."""
        num_samples = int(duration * sample_rate)
        samples = []

        for i in range(num_samples):
            t = float(i) / sample_rate
            value = 0.0

            if waveform == "sine":
                value = math.sin(2 * math.pi * frequency * t)
            elif waveform == "square":
                value = 1.0 if math.sin(2 * math.pi * frequency * t) > 0 else -1.0
            elif waveform == "sawtooth":
                # 2 * (t * f - floor(t * f + 0.5))
                value = 2.0 * (t * frequency - math.floor(t * frequency + 0.5))
            elif waveform == "triangle":
                # 2 * abs(2 * (t * f - floor(t * f + 0.5))) - 1
                value = 2.0 * abs(2.0 * (t * frequency - math.floor(t * frequency + 0.5))) - 1.0

            samples.append(value * amplitude)

        out = Path(output_path)
        self._write_wav(out, samples, sample_rate)
        return out

    def generate_noise(self, noise_type: str = "white", duration: float = 1.0, output_path: str = "noise.wav", sample_rate: int = 44100, amplitude: float = 0.5):
        """Generates noise."""
        num_samples = int(duration * sample_rate)
        samples = []

        if noise_type == "white":
            for _ in range(num_samples):
                value = random.uniform(-1.0, 1.0)
                samples.append(value * amplitude)
        else:
            # Fallback to white for now
            for _ in range(num_samples):
                value = random.uniform(-1.0, 1.0)
                samples.append(value * amplitude)

        out = Path(output_path)
        self._write_wav(out, samples, sample_rate)
        return out

    def generate_dtmf(self, sequence: str, output_path: str = "dtmf.wav", tone_duration: float = 0.2, space_duration: float = 0.1, sample_rate: int = 44100, amplitude: float = 0.5):
        """Generates DTMF tones for a sequence of characters."""
        dtmf_freqs = {
            '1': (697, 1209), '2': (697, 1336), '3': (697, 1477), 'A': (697, 1633),
            '4': (770, 1209), '5': (770, 1336), '6': (770, 1477), 'B': (770, 1633),
            '7': (852, 1209), '8': (852, 1336), '9': (852, 1477), 'C': (852, 1633),
            '*': (941, 1209), '0': (941, 1336), '#': (941, 1477), 'D': (941, 1633)
        }

        samples = []

        # Helper for silence
        def add_silence(dur):
            num_s = int(dur * sample_rate)
            samples.extend([0.0] * num_s)

        for char in sequence.upper():
            if char in dtmf_freqs:
                f1, f2 = dtmf_freqs[char]
                num_s = int(tone_duration * sample_rate)
                for i in range(num_s):
                    t = float(i) / sample_rate
                    # Mix two sines
                    val = (math.sin(2 * math.pi * f1 * t) + math.sin(2 * math.pi * f2 * t)) / 2.0
                    samples.append(val * amplitude)

                # Space after tone
                add_silence(space_duration)
            elif char == ' ':
                # Pause
                add_silence(tone_duration)
            else:
                # Ignore unknown chars or treat as pause
                pass

        out = Path(output_path)
        self._write_wav(out, samples, sample_rate)
        return out

    def generate_morse(self, text: str, output_path: str = "morse.wav", wpm: int = 20, frequency: float = 600.0, sample_rate: int = 44100, amplitude: float = 0.5):
        """Generates Morse code audio."""
        # Standard timing:
        # Dot = 1 unit
        # Dash = 3 units
        # Intra-character space = 1 unit
        # Inter-character space = 3 units
        # Word space = 7 units

        # WPM calculation: Standard word is "PARIS" (50 units).
        # Time for 1 unit = 60 / (50 * WPM) seconds
        unit_time = 60.0 / (50.0 * wpm)

        morse_code = {
            'A': '.-', 'B': '-...', 'C': '-.-.', 'D': '-..', 'E': '.', 'F': '..-.',
            'G': '--.', 'H': '....', 'I': '..', 'J': '.---', 'K': '-.-', 'L': '.-..',
            'M': '--', 'N': '-.', 'O': '---', 'P': '.--.', 'Q': '--.-', 'R': '.-.',
            'S': '...', 'T': '-', 'U': '..-', 'V': '...-', 'W': '.--', 'X': '-..-',
            'Y': '-.--', 'Z': '--..',
            '1': '.----', '2': '..---', '3': '...--', '4': '....-', '5': '.....',
            '6': '-....', '7': '--...', '8': '---..', '9': '----.', '0': '-----',
            '.': '.-.-.-', ',': '--..--', '?': '..--..', "'": '.----.', '!': '-.-.--',
            '/': '-..-.'
        }

        samples = []

        def add_tone(duration_units):
            duration = duration_units * unit_time
            num_s = int(duration * sample_rate)
            # Ramp envelope to avoid clicking (5ms)
            ramp_s = int(0.005 * sample_rate)

            for i in range(num_s):
                t = float(i) / sample_rate
                val = math.sin(2 * math.pi * frequency * t)

                # Apply envelope
                env = 1.0
                if i < ramp_s:
                    env = float(i) / ramp_s
                elif i > num_s - ramp_s:
                    env = float(num_s - i) / ramp_s

                samples.append(val * amplitude * env)

        def add_silence(duration_units):
            duration = duration_units * unit_time
            num_s = int(duration * sample_rate)
            samples.extend([0.0] * num_s)

        words = text.upper().split()
        for i, word in enumerate(words):
            for j, char in enumerate(word):
                if char in morse_code:
                    code = morse_code[char]
                    for k, symbol in enumerate(code):
                        if symbol == '.':
                            add_tone(1)
                        elif symbol == '-':
                            add_tone(3)

                        # Space between symbols (unless last)
                        if k < len(code) - 1:
                            add_silence(1)

                    # Space between letters (unless last in word)
                    if j < len(word) - 1:
                        add_silence(3)

            # Space between words
            if i < len(words) - 1:
                add_silence(7)

        out = Path(output_path)
        self._write_wav(out, samples, sample_rate)
        return out

def run_sound_lab_logic(args):
    """CLI logic for Sound Lab."""
    manager = SoundLabManager(args.project_dir)

    try:
        if args.action == "tone":
            path = manager.generate_tone(
                frequency=args.freq,
                duration=args.duration,
                waveform=args.wave,
                output_path=args.output
            )
            print(f"✅ Tone generated: {path}")

        elif args.action == "noise":
            path = manager.generate_noise(
                noise_type=args.type,
                duration=args.duration,
                output_path=args.output
            )
            print(f"✅ Noise generated: {path}")

        elif args.action == "dtmf":
            path = manager.generate_dtmf(
                sequence=args.sequence,
                output_path=args.output
            )
            print(f"✅ DTMF generated: {path}")

        elif args.action == "morse":
            path = manager.generate_morse(
                text=args.text,
                output_path=args.output,
                wpm=args.wpm,
                frequency=args.freq
            )
            print(f"✅ Morse generated: {path}")

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)
