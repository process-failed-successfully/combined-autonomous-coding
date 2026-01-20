import json
from pathlib import Path
from typing import List, Dict, Union

def load_feature_list(path: Path) -> List[Dict]:
    """
    Loads the feature list from a JSON file.
    Handles both legacy list format and new dict format {"features": [...]}.
    """
    if not path.exists():
        return []

    try:
        content = path.read_text().strip()
        if not content:
            return []

        data = json.loads(content)

        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            return data.get("features", [])
        else:
            return []
    except (json.JSONDecodeError, IOError):
        return []

def save_feature_list(path: Path, features: List[Dict]):
    """
    Saves the feature list to a JSON file in the standard dict format.
    """
    data = {"features": features}
    path.write_text(json.dumps(data, indent=2))
