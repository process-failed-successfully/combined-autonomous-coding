import shutil
import subprocess
import sys
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional

class MediaLabManager:
    """
    Manages media processing using ffmpeg.
    """

    def __init__(self, project_dir: Optional[Path] = None):
        self.project_dir = project_dir or Path(".")
        self.ffmpeg_bin = shutil.which("ffmpeg")
        self.ffprobe_bin = shutil.which("ffprobe")

    def _check_ffmpeg(self):
        if not self.ffmpeg_bin:
            print("❌ Error: 'ffmpeg' not found. Please install ffmpeg.", file=sys.stderr)
            sys.exit(1)

    def _check_ffprobe(self):
        if not self.ffprobe_bin:
            print("❌ Error: 'ffprobe' not found. Please install ffmpeg.", file=sys.stderr)
            sys.exit(1)

    def get_info(self, filepath: Path) -> Dict[str, Any]:
        """
        Returns metadata about a media file using ffprobe.
        """
        self._check_ffprobe()
        if not filepath.exists():
            raise FileNotFoundError(f"File not found: {filepath}")

        cmd = [
            self.ffprobe_bin,
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            str(filepath)
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return json.loads(result.stdout)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"ffprobe failed: {e.stderr}")
        except json.JSONDecodeError:
            raise RuntimeError("Failed to parse ffprobe output.")

    def convert(self, input_path: Path, output_path: Path, **kwargs) -> Path:
        """
        Converts media to a different format.
        """
        self._check_ffmpeg()
        if not input_path.exists():
            raise FileNotFoundError(f"File not found: {input_path}")

        cmd = [self.ffmpeg_bin, "-y", "-i", str(input_path)]

        # Add extra args if any (simple implementation)
        for k, v in kwargs.items():
            if v is not None:
                cmd.extend([f"-{k}", str(v)])

        cmd.append(str(output_path))

        try:
            subprocess.run(cmd, check=True, capture_output=False) # Let ffmpeg print progress
            return output_path
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"ffmpeg failed: {e}")

    def resize(self, input_path: Path, output_path: Path, width: int, height: int) -> Path:
        """
        Resizes video.
        """
        self._check_ffmpeg()
        if not input_path.exists():
            raise FileNotFoundError(f"File not found: {input_path}")

        # Scale filter
        # scale=w:h
        # If one is -1, it maintains aspect ratio
        w = width if width is not None else -1
        h = height if height is not None else -1

        if w == -1 and h == -1:
             raise ValueError("At least one dimension must be specified.")

        filter_arg = f"scale={w}:{h}"

        cmd = [
            self.ffmpeg_bin, "-y",
            "-i", str(input_path),
            "-vf", filter_arg,
            "-c:a", "copy", # Copy audio
            str(output_path)
        ]

        try:
            subprocess.run(cmd, check=True)
            return output_path
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"ffmpeg resize failed: {e}")

    def extract_audio(self, input_path: Path, output_path: Path) -> Path:
        """
        Extracts audio from video.
        """
        self._check_ffmpeg()
        if not input_path.exists():
            raise FileNotFoundError(f"File not found: {input_path}")

        cmd = [
            self.ffmpeg_bin, "-y",
            "-i", str(input_path),
            "-vn", # No video
            "-acodec", "libmp3lame" if output_path.suffix == ".mp3" else "copy",
            str(output_path)
        ]

        try:
            subprocess.run(cmd, check=True)
            return output_path
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"ffmpeg extract audio failed: {e}")

    def trim(self, input_path: Path, output_path: Path, start: str, end: Optional[str] = None, duration: Optional[str] = None) -> Path:
        """
        Trims media file.
        """
        self._check_ffmpeg()
        if not input_path.exists():
            raise FileNotFoundError(f"File not found: {input_path}")

        cmd = [self.ffmpeg_bin, "-y", "-i", str(input_path), "-ss", start]

        if end:
            cmd.extend(["-to", end])
        if duration:
            cmd.extend(["-t", duration])

        cmd.append(str(output_path)) # IMPORTANT: re-encoding is often safer for accuracy than -c copy for cut points

        try:
            subprocess.run(cmd, check=True)
            return output_path
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"ffmpeg trim failed: {e}")


def run_media_lab_logic(args):
    """
    CLI entry point for Media Lab.
    """
    manager = MediaLabManager(args.project_dir)

    try:
        if args.action == "info":
            info = manager.get_info(Path(args.file))
            print(json.dumps(info, indent=2))

        elif args.action == "convert":
            output = Path(args.output)
            manager.convert(Path(args.input), output)
            print(f"✅ Converted file saved to {output}")

        elif args.action == "resize":
            output = Path(args.output)
            manager.resize(
                Path(args.input),
                output,
                width=args.width,
                height=args.height
            )
            print(f"✅ Resized video saved to {output}")

        elif args.action == "extract-audio":
            output = Path(args.output)
            manager.extract_audio(Path(args.input), output)
            print(f"✅ Audio extracted to {output}")

        elif args.action == "trim":
            output = Path(args.output)
            manager.trim(
                Path(args.input),
                output,
                start=args.start,
                end=args.end,
                duration=args.duration
            )
            print(f"✅ Trimmed media saved to {output}")

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)
