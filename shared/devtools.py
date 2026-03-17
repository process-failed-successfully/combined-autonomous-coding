import base64
import hashlib
import json
import uuid
from datetime import datetime

class DevTools:
    """Utility collection for developers."""

    @staticmethod
    def epoch_to_date(timestamp: float) -> str:
        """Converts epoch timestamp to ISO 8601 date string."""
        try:
            dt = datetime.fromtimestamp(timestamp)
            return dt.isoformat()
        except Exception as e:
            return f"Error: {e}"

    @staticmethod
    def date_to_epoch(date_str: str) -> float:
        """Converts ISO 8601 date string to epoch timestamp."""
        try:
            # Handles '2023-01-01T12:00:00' and '2023-01-01 12:00:00'
            date_str = date_str.replace("T", " ")
            dt = datetime.fromisoformat(date_str)
            return dt.timestamp()
        except Exception as e:
            raise ValueError(f"Invalid date format: {e}")

    @staticmethod
    def base64_encode(text: str) -> str:
        """Encodes text to Base64."""
        try:
            return base64.b64encode(text.encode("utf-8")).decode("utf-8")
        except Exception as e:
            return f"Error: {e}"

    @staticmethod
    def base64_decode(text: str) -> str:
        """Decodes Base64 text."""
        try:
            return base64.b64decode(text).decode("utf-8")
        except Exception as e:
            return f"Error: {e}"

    @staticmethod
    def base64url_encode(text: str) -> str:
        """Encodes text to Base64URL."""
        try:
            return base64.urlsafe_b64encode(text.encode("utf-8")).decode("utf-8").rstrip('=')
        except Exception as e:
            return f"Error encoding to Base64URL: {e}"

    @staticmethod
    def base64url_decode(text: str) -> str:
        """Decodes text from Base64URL."""
        try:
            padding_needed = len(text) % 4
            padded_string = text + ('=' * ((4 - padding_needed) % 4))
            return base64.urlsafe_b64decode(padded_string).decode("utf-8")
        except Exception as e:
            return f"Error decoding from Base64URL: {e}"

    @staticmethod
    def generate_uuid() -> str:
        """Generates a random UUID v4."""
        return str(uuid.uuid4())

    @staticmethod
    def calculate_hash(text: str, algo: str = "sha256") -> str:
        """Calculates hash of text using specified algorithm."""
        try:
            if algo not in hashlib.algorithms_available:
                return f"Error: Algorithm '{algo}' not available."

            h = hashlib.new(algo)
            h.update(text.encode("utf-8"))
            return h.hexdigest()
        except Exception as e:
            return f"Error: {e}"

    @staticmethod
    def format_json(text: str) -> str:
        """Formats and validates JSON string."""
        try:
            obj = json.loads(text)
            return json.dumps(obj, indent=2)
        except json.JSONDecodeError as e:
            return f"Error: Invalid JSON - {e}"
