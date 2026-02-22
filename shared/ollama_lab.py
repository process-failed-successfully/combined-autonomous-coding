import os
import requests
import json
import sys
from typing import List, Dict, Any, Optional, Callable, Generator

class OllamaLabManager:
    """
    Manages interactions with the local Ollama instance.
    """
    def __init__(self):
        self.base_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
        # Ensure no trailing slash
        if self.base_url.endswith("/"):
            self.base_url = self.base_url[:-1]

    def _get_url(self, endpoint: str) -> str:
        return f"{self.base_url}{endpoint}"

    def check_connection(self) -> bool:
        """Checks if Ollama is reachable."""
        try:
            # Listing models is a cheap way to check
            response = requests.get(self._get_url("/api/tags"), timeout=2)
            return response.status_code == 200
        except requests.RequestException:
            return False

    def list_models(self) -> List[Dict[str, Any]]:
        """Lists installed models."""
        try:
            response = requests.get(self._get_url("/api/tags"), timeout=5)
            if response.status_code == 200:
                data = response.json()
                return data.get("models", [])
            return []
        except requests.RequestException:
            return []

    def show_model_info(self, name: str) -> Dict[str, Any]:
        """Gets details about a model."""
        try:
            response = requests.post(
                self._get_url("/api/show"),
                json={"name": name},
                timeout=5
            )
            if response.status_code == 200:
                return response.json()
            return {"error": f"Status {response.status_code}: {response.text}"}
        except requests.RequestException as e:
            return {"error": str(e)}

    def delete_model(self, name: str) -> bool:
        """Deletes a model."""
        try:
            response = requests.delete(
                self._get_url("/api/delete"),
                json={"name": name},
                timeout=10
            )
            return response.status_code == 200
        except requests.RequestException:
            return False

    def pull_model(self, name: str) -> Generator[Dict[str, Any], None, None]:
        """
        Pulls a model, yielding status updates.
        """
        try:
            with requests.post(
                self._get_url("/api/pull"),
                json={"name": name},
                stream=True,
                # Connect timeout 10s, Read timeout 300s (5 min) for potentially slow chunks
                timeout=(10, 300)
            ) as response:
                if response.status_code != 200:
                    yield {"error": f"Status {response.status_code}: {response.text}"}
                    return

                for line in response.iter_lines():
                    if line:
                        try:
                            data = json.loads(line.decode('utf-8'))
                            yield data
                        except json.JSONDecodeError:
                            pass
        except requests.RequestException as e:
            yield {"error": str(e)}

    def chat(self, model: str, message: str) -> Generator[str, None, None]:
        """
        Sends a chat message and yields response chunks.
        """
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": message}],
            "stream": True
        }
        try:
            with requests.post(
                self._get_url("/api/chat"),
                json=payload,
                stream=True,
                timeout=(10, 120)
            ) as response:
                if response.status_code != 200:
                    yield f"Error: Status {response.status_code}"
                    return

                for line in response.iter_lines():
                    if line:
                        try:
                            data = json.loads(line.decode('utf-8'))
                            content = data.get("message", {}).get("content", "")
                            if content:
                                yield content
                            if data.get("done"):
                                break
                        except json.JSONDecodeError:
                            pass
        except requests.RequestException as e:
            yield f"Error: {e}"


def run_ollama_lab_logic(args):
    """CLI logic for Ollama Lab."""
    manager = OllamaLabManager()

    if not manager.check_connection():
        print(f"❌ Error: Could not connect to Ollama at {manager.base_url}", file=sys.stderr)
        print("Please ensure Ollama is running.", file=sys.stderr)
        sys.exit(1)

    if args.action == "list":
        models = manager.list_models()
        if not models:
            print("No models found.")
        else:
            print(f"{'Name':<30} | {'Size':<10} | {'Modified'}")
            print("-" * 60)
            for m in models:
                size_gb = m.get('size', 0) / (1024**3)
                modified = m.get('modified_at', '')[:19] # Truncate ISO time
                print(f"{m['name']:<30} | {size_gb:.2f} GB    | {modified}")

    elif args.action == "show":
        if not args.name:
            print("Error: --name required for show.", file=sys.stderr)
            sys.exit(1)
        info = manager.show_model_info(args.name)
        print(json.dumps(info, indent=2))

    elif args.action == "pull":
        if not args.name:
            print("Error: --name required for pull.", file=sys.stderr)
            sys.exit(1)
        print(f"Pulling {args.name}...")
        for update in manager.pull_model(args.name):
            if "error" in update:
                print(f"\n❌ {update['error']}")
                sys.exit(1)
            status = update.get("status", "")
            completed = update.get("completed", 0)
            total = update.get("total", 0)

            if total > 0:
                percent = (completed / total) * 100
                print(f"\r{status}: {percent:.1f}%", end="")
            else:
                print(f"\r{status}", end="")
        print("\n✅ Pull complete.")

    elif args.action == "delete":
        if not args.name:
            print("Error: --name required for delete.", file=sys.stderr)
            sys.exit(1)
        if manager.delete_model(args.name):
            print(f"✅ Deleted {args.name}")
        else:
            print(f"❌ Failed to delete {args.name}", file=sys.stderr)
            sys.exit(1)

    elif args.action == "chat":
        if not args.name:
            print("Error: --name (model) required for chat.", file=sys.stderr)
            sys.exit(1)
        if not args.message:
            print("Error: --message required for chat.", file=sys.stderr)
            sys.exit(1)

        print(f"[{args.name}]: ", end="", flush=True)
        for chunk in manager.chat(args.name, args.message):
            print(chunk, end="", flush=True)
        print()

    else:
        print(f"Unknown action: {args.action}", file=sys.stderr)
        sys.exit(1)
