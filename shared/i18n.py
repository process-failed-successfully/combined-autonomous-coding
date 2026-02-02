import json
import logging
from pathlib import Path
from typing import List, Dict, Optional, Any
import re

from shared.config import Config
from agents.gemini import GeminiAgent
from agents.cursor import CursorAgent
from agents.local import LocalAgent
from agents.openrouter import OpenRouterAgent

logger = logging.getLogger(__name__)

class I18nManager:
    """
    Manages Internationalization (i18n) tasks: translation and verification.
    """
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir

    async def translate(
        self,
        source_file: Path,
        target_langs: List[str],
        agent_type: str = "gemini",
        model: Optional[str] = None
    ) -> bool:
        """
        Translates a source JSON file to target languages using an AI agent.
        """
        if not source_file.exists():
            logger.error(f"Source file not found: {source_file}")
            print(f"❌ Source file not found: {source_file}")
            return False

        try:
            source_content = json.loads(source_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in source file: {source_file}")
            print(f"❌ Invalid JSON in source file: {source_file}")
            return False

        # Setup Config for Agent
        config = Config(
            project_dir=self.project_dir,
            agent_type=agent_type,
            model=model,
            max_iterations=1,
            stream_output=False, # We want clean output
        )

        agent_class_map = {
            "gemini": GeminiAgent,
            "cursor": CursorAgent,
            "local": LocalAgent,
            "openrouter": OpenRouterAgent,
        }
        agent_class = agent_class_map.get(agent_type)
        if not agent_class:
            logger.error(f"Unknown agent type: {agent_type}")
            return False

        agent = agent_class(config)

        success = True
        for lang in target_langs:
            print(f"Translating to {lang}...")
            prompt = f"""
You are an expert translator. Translate the following JSON content from the source language to {lang}.
Return ONLY the translated JSON object. Do not wrap it in markdown code blocks. Do not add any explanation.
Keep the keys exactly the same. Only translate the values.

Source JSON:
{json.dumps(source_content, indent=2)}
"""
            try:
                # We use the agent to generate the translation
                # run_agent_session returns (status, response, actions)
                status, response, _ = await agent.run_agent_session(prompt)

                # Clean up response (remove code blocks if present despite instructions)
                cleaned_response = self._clean_json_response(response)

                translated_data = json.loads(cleaned_response)

                output_file = source_file.parent / f"{lang}.json"
                output_file.write_text(json.dumps(translated_data, indent=2, ensure_ascii=False), encoding="utf-8")
                print(f"✅ Generated {output_file.name}")

            except Exception as e:
                logger.error(f"Failed to translate to {lang}: {e}")
                print(f"❌ Failed to translate to {lang}: {e}")
                success = False

        return success

    def verify(self, source_file: Path, target_langs: List[str]) -> Dict[str, List[str]]:
        """
        Verifies that target language files have the same keys as the source file.
        """
        if not source_file.exists():
            return {"error": [f"Source file not found: {source_file}"]}

        try:
            source_content = json.loads(source_file.read_text(encoding="utf-8"))
            source_keys = set(self.flatten_keys(source_content))
        except Exception as e:
            return {"error": [f"Error reading source file: {e}"]}

        report = {}

        for lang in target_langs:
            target_file = source_file.parent / f"{lang}.json"
            if not target_file.exists():
                report[lang] = ["File missing"]
                continue

            try:
                target_content = json.loads(target_file.read_text(encoding="utf-8"))
                target_keys = set(self.flatten_keys(target_content))

                missing = list(source_keys - target_keys)
                extra = list(target_keys - source_keys)

                issues = []
                if missing:
                    issues.append(f"Missing keys: {', '.join(missing[:5])}" + ("..." if len(missing) > 5 else ""))
                if extra:
                    issues.append(f"Extra keys: {', '.join(extra[:5])}" + ("..." if len(extra) > 5 else ""))

                if issues:
                    report[lang] = issues
            except Exception as e:
                report[lang] = [f"Invalid JSON: {e}"]

        return report

    def _clean_json_response(self, response: str) -> str:
        # Remove markdown code blocks if present
        response = re.sub(r"^```json\s*", "", response, flags=re.MULTILINE)
        response = re.sub(r"^```\s*", "", response, flags=re.MULTILINE)
        response = re.sub(r"```$", "", response, flags=re.MULTILINE)
        return response.strip()

    def flatten_keys(self, d: Dict[str, Any], parent_key: str = '') -> List[str]:
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}.{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self.flatten_keys(v, new_key))
            else:
                items.append(new_key)
        return items

async def run_i18n_logic(
    action: str,
    project_dir: Path,
    source: str = "locales/en.json",
    langs: Optional[str] = None,
    agent_type: str = "gemini",
    model: Optional[str] = None
) -> bool:
    """
    Entry point for i18n command logic.
    """
    manager = I18nManager(project_dir)
    source_file = project_dir / source

    if not langs:
        print("Error: Target languages required (e.g. --langs es,fr)")
        return False

    target_langs = [l.strip() for l in langs.split(",")]

    if action == "translate":
        return await manager.translate(source_file, target_langs, agent_type, model)
    elif action == "verify":
        report = manager.verify(source_file, target_langs)
        if not report:
            print("✅ All translations valid.")
            return True
        else:
            print("Issues found:")
            for lang, issues in report.items():
                print(f"  {lang}:")
                for issue in issues:
                    print(f"    - {issue}")
            return False

    return False
