import os
from pathlib import Path
from typing import List, Dict, Optional
import logging
import shutil

logger = logging.getLogger(__name__)

try:
    from playwright.sync_api import sync_playwright, Error as PlaywrightError
except ImportError:
    sync_playwright = None
    PlaywrightError = None

try:
    from PIL import Image, ImageChops, ImageStat
except ImportError:
    Image = None
    ImageChops = None
    ImageStat = None

class FrontendVerifier:
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.snapshots_dir = self.project_dir / ".frontend_snapshots"
        self.snapshots_dir.mkdir(parents=True, exist_ok=True)

    def setup(self) -> bool:
        """Checks if dependencies are available."""
        if sync_playwright is None:
            print("Error: 'playwright' not installed. Please run 'pip install playwright'.")
            return False
        if Image is None:
            print("Error: 'pillow' not installed. Please run 'pip install pillow'.")
            return False
        return True

    def _get_paths(self, name: str):
        safe_name = "".join([c if c.isalnum() else "_" for c in name])
        return {
            "baseline": self.snapshots_dir / f"{safe_name}_baseline.png",
            "current": self.snapshots_dir / f"{safe_name}_current.png",
            "diff": self.snapshots_dir / f"{safe_name}_diff.png",
            "safe_name": safe_name
        }

    def capture_snapshot(self, url: str, name: str, is_baseline: bool = False) -> Optional[Path]:
        """
        Captures a screenshot.
        If is_baseline=True, saves as _baseline.png
        Else, saves as _current.png
        """
        if not self.setup():
            return None

        paths = self._get_paths(name)
        output_path = paths["baseline"] if is_baseline else paths["current"]

        print(f"Capturing {url} to {output_path.name}...")

        try:
            with sync_playwright() as p:
                # Launch arguments optimized for container environments
                browser = p.chromium.launch(
                    args=["--no-sandbox", "--disable-setuid-sandbox"]
                )
                page = browser.new_page()
                page.goto(url)
                # Wait for network idle to ensure content is loaded
                try:
                    page.wait_for_load_state("networkidle", timeout=10000)
                except Exception:
                    print("Warning: Network idle timeout, proceeding with snapshot.")

                page.screenshot(path=output_path, full_page=True)
                browser.close()

            return output_path
        except Exception as e:
            logger.error(f"Snapshot failed: {e}")
            print(f"Snapshot failed: {e}")
            return None

    def verify(self, name: str) -> Dict:
        """
        Compares current snapshot with baseline.
        Returns dict with match status and diff score.
        """
        if not self.setup():
            return {"success": False, "error": "Dependencies missing"}

        paths = self._get_paths(name)

        if not paths["current"].exists():
             return {"success": False, "error": f"No current snapshot found for '{name}'."}

        if not paths["baseline"].exists():
             # If no baseline, current becomes baseline
             shutil.copy(paths["current"], paths["baseline"])
             return {
                 "success": True,
                 "match": True,
                 "diff_score": 0.0,
                 "message": "No baseline found. Created baseline from current."
             }

        try:
            img1 = Image.open(paths["baseline"]).convert('RGB')
            img2 = Image.open(paths["current"]).convert('RGB')

            # Resize img2 to match img1 if dimensions differ
            if img1.size != img2.size:
                img2 = img2.resize(img1.size)

            diff = ImageChops.difference(img1, img2)

            # Calculate difference score using ImageStat
            stat = ImageStat.Stat(diff)
            # Average pixel difference (0-255)
            diff_score = sum(stat.mean) / len(stat.mean)

            # Save diff image
            diff.save(paths["diff"])

            # Tolerance threshold (e.g. 0.1 pixel difference average)
            is_match = diff_score < 0.1

            return {
                "success": True,
                "match": is_match,
                "diff_score": float(diff_score),
                "diff_path": paths["diff"],
                "baseline_path": paths["baseline"],
                "current_path": paths["current"]
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def approve_current(self, name: str) -> bool:
        """Promotes current snapshot to baseline."""
        paths = self._get_paths(name)
        if paths["current"].exists():
            shutil.copy(paths["current"], paths["baseline"])
            return True
        return False

    def list_baselines(self) -> List[str]:
        if not self.snapshots_dir.exists():
            return []
        files = self.snapshots_dir.glob("*_baseline.png")
        return sorted([f.name.replace("_baseline.png", "") for f in files])
