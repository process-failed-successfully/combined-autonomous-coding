import sys
import requests
import json
from typing import Dict, Any, List, Optional

class DictLabManager:
    """
    Manages dictionary lookups using the Free Dictionary API.
    """
    API_URL = "https://api.dictionaryapi.dev/api/v2/entries/en/{word}"

    def lookup(self, word: str) -> Dict[str, Any]:
        """
        Fetches dictionary data for a word.
        """
        try:
            response = requests.get(self.API_URL.format(word=word), timeout=10)
            if response.status_code == 200:
                return {"success": True, "data": response.json()}
            elif response.status_code == 404:
                return {"success": False, "error": f"Word '{word}' not found."}
            else:
                return {"success": False, "error": f"API Error: {response.status_code}"}
        except requests.RequestException as e:
            return {"success": False, "error": f"Network Error: {e}"}

    def get_definitions(self, data: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """
        Extracts definitions from the API response.
        """
        definitions = []
        for entry in data:
            word = entry.get("word", "")
            phonetic = entry.get("phonetic", "")
            for meaning in entry.get("meanings", []):
                part_of_speech = meaning.get("partOfSpeech", "")
                for definition in meaning.get("definitions", []):
                    defi = definition.get("definition", "")
                    example = definition.get("example", "")
                    definitions.append({
                        "word": word,
                        "phonetic": phonetic,
                        "part_of_speech": part_of_speech,
                        "definition": defi,
                        "example": example
                    })
        return definitions

    def get_synonyms(self, data: List[Dict[str, Any]]) -> List[str]:
        """
        Extracts synonyms from the API response.
        """
        synonyms = set()
        for entry in data:
            for meaning in entry.get("meanings", []):
                synonyms.update(meaning.get("synonyms", []))
                for definition in meaning.get("definitions", []):
                    synonyms.update(definition.get("synonyms", []))
        return sorted(list(synonyms))

    def get_antonyms(self, data: List[Dict[str, Any]]) -> List[str]:
        """
        Extracts antonyms from the API response.
        """
        antonyms = set()
        for entry in data:
            for meaning in entry.get("meanings", []):
                antonyms.update(meaning.get("antonyms", []))
                for definition in meaning.get("definitions", []):
                    antonyms.update(definition.get("antonyms", []))
        return sorted(list(antonyms))

def run_dict_lab_logic(args):
    """
    CLI logic for Dict Lab.
    """
    manager = DictLabManager()

    # Check if word is provided
    if not args.word:
        print("Error: Word argument is required.", file=sys.stderr)
        sys.exit(1)

    result = manager.lookup(args.word)

    if not result["success"]:
        print(f"❌ {result['error']}", file=sys.stderr)
        sys.exit(1)

    data = result["data"]

    if args.action == "define":
        definitions = manager.get_definitions(data)
        if not definitions:
            print(f"No definitions found for '{args.word}'.")
            sys.exit(0)

        print(f"--- Definitions for: {args.word} ---")

        # Group by part of speech for cleaner output
        # Or simpler list

        for i, d in enumerate(definitions):
            phonetic = f" ({d['phonetic']})" if d['phonetic'] else ""
            print(f"[{d['part_of_speech']}]{phonetic} {d['definition']}")
            if d['example']:
                print(f"  Example: \"{d['example']}\"")

    elif args.action == "synonym":
        synonyms = manager.get_synonyms(data)
        if synonyms:
            print(f"--- Synonyms for: {args.word} ---")
            print(", ".join(synonyms))
        else:
            print(f"No synonyms found for '{args.word}'.")

    elif args.action == "antonym":
        antonyms = manager.get_antonyms(data)
        if antonyms:
            print(f"--- Antonyms for: {args.word} ---")
            print(", ".join(antonyms))
        else:
            print(f"No antonyms found for '{args.word}'.")

    sys.exit(0)
