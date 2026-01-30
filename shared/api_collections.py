import json
import uuid
from pathlib import Path
from typing import List, Dict, Any, Optional

class ApiCollectionManager:
    """
    Manages saved API requests in collections.
    """

    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.file_path = self.project_dir / ".agent_api_collections.json"
        self.collections: Dict[str, Any] = {"collections": [{"name": "Default", "requests": []}]}
        self.load()

    def load(self) -> None:
        """Loads collections from the JSON file."""
        if self.file_path.exists():
            try:
                with open(self.file_path, "r") as f:
                    self.collections = json.load(f)
            except Exception as e:
                print(f"Error loading API collections: {e}")
                # Keep default state if load fails

    def save(self) -> None:
        """Saves collections to the JSON file."""
        try:
            with open(self.file_path, "w") as f:
                json.dump(self.collections, f, indent=2)
        except Exception as e:
            print(f"Error saving API collections: {e}")

    def save_request(self, name: str, method: str, url: str, headers: Dict[str, str], body: str) -> None:
        """Saves a request to the Default collection."""
        request_id = str(uuid.uuid4())
        new_request = {
            "id": request_id,
            "name": name,
            "method": method,
            "url": url,
            "headers": headers,
            "body": body
        }

        # For MVP, we just append to the first collection (Default)
        if not self.collections.get("collections"):
            self.collections["collections"] = [{"name": "Default", "requests": []}]

        self.collections["collections"][0]["requests"].append(new_request)
        self.save()

    def list_requests(self) -> List[Dict[str, Any]]:
        """Lists all requests from the Default collection."""
        if not self.collections.get("collections"):
            return []
        return self.collections["collections"][0]["requests"]

    def delete_request(self, request_id: str) -> bool:
        """Deletes a request by ID."""
        if not self.collections.get("collections"):
            return False

        requests = self.collections["collections"][0]["requests"]
        initial_len = len(requests)
        self.collections["collections"][0]["requests"] = [r for r in requests if r["id"] != request_id]

        if len(self.collections["collections"][0]["requests"]) < initial_len:
            self.save()
            return True
        return False

    def get_request(self, request_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a request by ID."""
        if not self.collections.get("collections"):
            return None

        requests = self.collections["collections"][0]["requests"]
        for r in requests:
            if r["id"] == request_id:
                return r
        return None
