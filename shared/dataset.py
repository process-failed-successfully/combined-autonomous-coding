"""
Dataset Generator
=================

Generates a fine-tuning dataset from agent interaction logs.
"""

import re
import json
import logging
from pathlib import Path
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class LogParser:
    """Parses agent logs to extract Prompt-Response pairs."""

    def parse(self, log_path: Path) -> List[Dict[str, str]]:
        """Parses a log file and returns a list of interactions."""
        interactions = []
        if not log_path.exists():
            return []

        try:
            content = log_path.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            logger.error(f"Error reading log {log_path}: {e}")
            return []

        # Split into blocks based on log headers (HH:MM:SS - LEVEL - )
        # This regex looks for a newline followed by the timestamp pattern
        blocks = re.split(r'\n(?=\d{2}:\d{2}:\d{2} - [A-Z]+ - )', content)

        current_prompt = None

        for block in blocks:
            # Clean up the block (remove header line if possible, or just search in it)
            # The prompt follows "Sending Augmented Prompt:"
            if "Sending Augmented Prompt:" in block:
                parts = block.split("Sending Augmented Prompt:\n", 1)
                if len(parts) > 1:
                    # Strip to remove trailing newlines or log artifacts
                    current_prompt = parts[1].strip()

            # The response follows "Response:"
            # Note: We rely on the fact that Response usually comes after Prompt.
            elif "Response:\n" in block:
                parts = block.split("Response:\n", 1)
                if len(parts) > 1 and current_prompt:
                    response_text = parts[1].strip()
                    interactions.append({
                        "prompt": current_prompt,
                        "response": response_text
                    })
                    # We don't reset current_prompt immediately because one prompt
                    # might generate multiple responses/actions?
                    # Usually it's 1-to-1 in the loop.
                    # Resetting is safer to avoid mismatch.
                    current_prompt = None

        return interactions

class DatasetGenerator:
    """Generates a fine-tuning dataset from agent history."""

    def __init__(self, project_dir: Path, logs_dir: Optional[Path] = None):
        self.project_dir = project_dir
        self.parser = LogParser()
        if logs_dir:
            self.logs_dir = logs_dir
        else:
            self.logs_dir = Path(__file__).parent.parent / "agents/logs"

    def generate(self, output_file: Path, run_id: Optional[str] = None, all_runs: bool = False) -> int:
        """
        Generates the dataset.
        Returns the number of examples generated.
        """
        logs_to_process = []

        if run_id:
            # Run ID provided
            if run_id == "last":
                from shared.cli_utils import get_latest_log_file
                # This util might use default logs dir, careful.
                # Ideally we should reimplement or pass logs_dir if supported.
                # For now, let's assume get_latest_log_file works if we are in normal context,
                # but for testing we avoid "last" if we want to use custom logs_dir.
                last = get_latest_log_file()
                if last:
                    logs_to_process.append(last)
            else:
                log_file = self.logs_dir / f"{run_id}.log"
                if log_file.exists():
                    logs_to_process.append(log_file)
                else:
                    print(f"❌ Log file not found for run ID: {run_id}")
                    return 0
        elif all_runs:
            # Process all logs in history
            history_file = self.project_dir / ".agent_history"
            processed_ids = set()

            if history_file.exists():
                run_ids = history_file.read_text().splitlines()
                for rid in run_ids:
                    rid = rid.strip()
                    if rid and rid not in processed_ids:
                        log_file = self.logs_dir / f"{rid}.log"
                        if log_file.exists():
                            logs_to_process.append(log_file)
                            processed_ids.add(rid)

            # Also check for any loose log files in directory not in history
            if self.logs_dir.exists():
                for log_file in self.logs_dir.glob("*.log"):
                    if log_file not in logs_to_process:
                        logs_to_process.append(log_file)
        else:
            # Default: Last run
            from shared.cli_utils import get_latest_log_file
            last = get_latest_log_file()
            if last:
                logs_to_process.append(last)

        if not logs_to_process:
            print("No logs found to process.")
            return 0

        print(f"Processing {len(logs_to_process)} log file(s)...")

        all_examples = []

        for log_file in logs_to_process:
            interactions = self.parser.parse(log_file)
            for itr in interactions:
                # Format for Chat Fine-tuning (JSONL with messages)
                example = {
                    "messages": [
                        {"role": "user", "content": itr["prompt"]},
                        {"role": "assistant", "content": itr["response"]}
                    ]
                }
                all_examples.append(example)

        if not all_examples:
            print("No interactions extracted. Ensure logs contain 'Sending Augmented Prompt' and 'Response'.")
            return 0

        # Save to JSONL
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                for ex in all_examples:
                    f.write(json.dumps(ex) + "\n")
            print(f"✅ Dataset saved to {output_file} ({len(all_examples)} examples).")
            return len(all_examples)
        except Exception as e:
            print(f"❌ Error saving dataset: {e}")
            return 0
