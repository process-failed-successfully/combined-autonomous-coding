import re
import sys
from pathlib import Path
from typing import List, Dict, Any, Union

class SubtitleLabManager:
    """
    Manages subtitle operations: parsing, converting, shifting, and cleaning.
    """

    def parse_file(self, path: Union[str, Path]) -> List[Dict[str, Any]]:
        """Parses a subtitle file based on extension."""
        path = Path(path).resolve()
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        content = path.read_text(encoding="utf-8", errors="replace")
        suffix = path.suffix.lower()

        if suffix == ".srt":
            return self.parse_srt(content)
        elif suffix == ".vtt":
            return self.parse_vtt(content)
        else:
            raise ValueError(f"Unsupported subtitle format: {suffix}")

    def parse_srt(self, content: str) -> List[Dict[str, Any]]:
        """Parses SRT format content."""
        # Normalize line endings
        content = content.replace("\r\n", "\n").replace("\r", "\n")
        blocks = re.split(r'\n\n+', content.strip())
        captions = []

        for block in blocks:
            lines = block.strip().splitlines()
            if len(lines) < 2:
                continue

            # Line 1: Index
            if not lines[0].isdigit():
                # Sometimes SRTs are malformed or have extra whitespace
                continue
            index = int(lines[0])

            # Line 2: Timestamp
            # 00:00:01,000 --> 00:00:04,000
            timing_line = lines[1]
            if "-->" not in timing_line:
                continue

            start_str, end_str = timing_line.split("-->", 1)
            start = self._timestamp_to_seconds(start_str.strip())
            end = self._timestamp_to_seconds(end_str.strip())

            # Line 3+: Text
            text = "\n".join(lines[2:])

            captions.append({
                "index": index,
                "start": start,
                "end": end,
                "text": text
            })

        return captions

    def parse_vtt(self, content: str) -> List[Dict[str, Any]]:
        """Parses WebVTT format content."""
        content = content.replace("\r\n", "\n").replace("\r", "\n")
        lines = content.strip().splitlines()

        # Check header
        if not lines or not lines[0].startswith("WEBVTT"):
            raise ValueError("Invalid WebVTT file (missing header).")

        captions = []
        current_caption = {}
        text_lines = []
        index = 1

        i = 1
        while i < len(lines):
            line = lines[i].strip()

            if not line:
                # Blank line usually ends a block
                if current_caption:
                    current_caption["text"] = "\n".join(text_lines)
                    captions.append(current_caption)
                    current_caption = {}
                    text_lines = []
                    index += 1
                i += 1
                continue

            if "-->" in line:
                # Timing line
                start_str, end_str = line.split("-->", 1)
                # Remove settings from end (e.g. align:start line:0%)
                end_str = end_str.split()[0]

                start = self._timestamp_to_seconds(start_str.strip())
                end = self._timestamp_to_seconds(end_str.strip())

                current_caption = {
                    "index": index,
                    "start": start,
                    "end": end
                }
            elif current_caption:
                # Text line inside a caption block
                text_lines.append(line)
            else:
                # Might be an ID line or comments (NOTE)
                pass

            i += 1

        # Add last one
        if current_caption:
            current_caption["text"] = "\n".join(text_lines)
            captions.append(current_caption)

        return captions

    def to_srt(self, captions: List[Dict[str, Any]]) -> str:
        """Generates SRT content."""
        output = []
        for i, cap in enumerate(captions):
            index = i + 1
            start = self._seconds_to_timestamp(cap["start"], separator=",")
            end = self._seconds_to_timestamp(cap["end"], separator=",")
            text = cap["text"]

            output.append(f"{index}")
            output.append(f"{start} --> {end}")
            output.append(text)
            output.append("") # Blank line

        return "\n".join(output)

    def to_vtt(self, captions: List[Dict[str, Any]]) -> str:
        """Generates WebVTT content."""
        output = ["WEBVTT", ""]
        for cap in captions:
            start = self._seconds_to_timestamp(cap["start"], separator=".")
            end = self._seconds_to_timestamp(cap["end"], separator=".")
            text = cap["text"]

            output.append(f"{start} --> {end}")
            output.append(text)
            output.append("")

        return "\n".join(output)

    def shift_timing(self, captions: List[Dict[str, Any]], seconds: float) -> List[Dict[str, Any]]:
        """Shifts timestamps by N seconds."""
        new_captions = []
        for cap in captions:
            new_cap = cap.copy()
            new_cap["start"] = max(0.0, cap["start"] + seconds)
            new_cap["end"] = max(0.0, cap["end"] + seconds)
            new_captions.append(new_cap)
        return new_captions

    def clean_text(self, captions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Removes HTML-like tags from text."""
        new_captions = []
        tag_re = re.compile(r'<[^>]+>')

        for cap in captions:
            new_cap = cap.copy()
            new_cap["text"] = tag_re.sub('', cap["text"])
            new_captions.append(new_cap)
        return new_captions

    def _timestamp_to_seconds(self, ts: str) -> float:
        """Converts HH:MM:SS,mmm or HH:MM:SS.mmm to seconds."""
        # Handle decimal comma/dot
        ts = ts.replace(",", ".")
        parts = ts.split(":")

        seconds = 0.0
        if len(parts) == 3:
            # HH:MM:SS.mmm
            h = float(parts[0])
            m = float(parts[1])
            s = float(parts[2])
            seconds = h * 3600 + m * 60 + s
        elif len(parts) == 2:
            # MM:SS.mmm
            m = float(parts[0])
            s = float(parts[1])
            seconds = m * 60 + s

        return seconds

    def _seconds_to_timestamp(self, seconds: float, separator: str = ",") -> str:
        """Converts seconds to HH:MM:SS,mmm string."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60

        # 06.3f -> 02d.03d effectively
        # separator handles , vs . for srt/vtt

        s_int = int(secs)
        s_frac = int(round((secs - s_int) * 1000))

        return f"{hours:02d}:{minutes:02d}:{s_int:02d}{separator}{s_frac:03d}"

def run_subtitle_lab_logic(args):
    """CLI entry point for Subtitle Lab."""
    manager = SubtitleLabManager()

    if not args.file:
        print("Error: --file required.", file=sys.stderr)
        sys.exit(1)

    try:
        captions = manager.parse_file(args.file)

        if args.action == "shift":
            if not args.shift:
                print("Error: --shift amount required (in seconds).", file=sys.stderr)
                sys.exit(1)
            captions = manager.shift_timing(captions, float(args.shift))
            print(f"Shifted {len(captions)} captions by {args.shift}s.")

        elif args.action == "clean":
            captions = manager.clean_text(captions)
            print(f"Cleaned HTML tags from {len(captions)} captions.")

        elif args.action == "convert":
            # Just parsing and re-exporting handles conversion
            pass

        # Export
        if args.output:
            out_path = Path(args.output)
            fmt = args.format or out_path.suffix.lstrip(".").lower() or "srt"

            content = ""
            if fmt == "srt":
                content = manager.to_srt(captions)
            elif fmt == "vtt":
                content = manager.to_vtt(captions)
            else:
                print(f"Error: Unknown output format '{fmt}'", file=sys.stderr)
                sys.exit(1)

            out_path.write_text(content, encoding="utf-8")
            print(f"✅ Saved to {out_path}")
        else:
            # Print to stdout
            # Default format matches input ext or SRT
            fmt = args.format or Path(args.file).suffix.lstrip(".").lower() or "srt"
            if fmt == "srt":
                print(manager.to_srt(captions))
            else:
                print(manager.to_vtt(captions))

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)
