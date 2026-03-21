import sys
from pathlib import Path
from shared.image_lab import ImageLabManager

try:
    manager = ImageLabManager()
    print(f"Has read_exif: {hasattr(manager, 'read_exif')}")
    print(f"Has remove_exif: {hasattr(manager, 'remove_exif')}")
except Exception as e:
    print(f"Error: {e}")
