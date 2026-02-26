import json
import logging
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Dict, Any

from shared.config import Config
from agents.gemini import GeminiAgent
from agents.cursor import CursorAgent
from agents.local import LocalAgent
from agents.openrouter import OpenRouterAgent

logger = logging.getLogger(__name__)

@dataclass
class Flashcard:
    id: str
    question: str
    answer: str
    source_file: str
    interval: int = 0
    repetitions: int = 0
    ease_factor: float = 2.5
    due_date: str = ""  # ISO format

    def __post_init__(self):
        if not self.due_date:
            self.due_date = datetime.now().isoformat()

class FlashcardsManager:
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.cards_file = project_dir / ".flashcards.json"
        self.cards: List[Flashcard] = []
        self.load_cards()

    def load_cards(self) -> None:
        if self.cards_file.exists():
            try:
                data = json.loads(self.cards_file.read_text(encoding="utf-8"))
                self.cards = [Flashcard(**item) for item in data]
            except Exception as e:
                logger.error(f"Error loading flashcards: {e}")
                self.cards = []

    def save_cards(self) -> None:
        try:
            data = [asdict(card) for card in self.cards]
            self.cards_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except Exception as e:
            logger.error(f"Error saving flashcards: {e}")

    async def generate_flashcards(self, file_path: Path, agent_type: str = "gemini", model: Optional[str] = None) -> List[Flashcard]:
        """
        Generates flashcards from a file using AI.
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        content = file_path.read_text(encoding="utf-8", errors="replace")

        # Setup Config and Agent
        config = Config(
            project_dir=self.project_dir,
            agent_type=agent_type,
            model=model,
            verbose=False,
            max_iterations=1,
            stream_output=False,
        )

        agent_class_map = {
            "gemini": GeminiAgent,
            "cursor": CursorAgent,
            "local": LocalAgent,
            "openrouter": OpenRouterAgent,
        }

        agent_class = agent_class_map.get(agent_type)
        if not agent_class:
            raise ValueError(f"Unknown agent type: {agent_type}")

        agent = agent_class(config)

        prompt = f"""
        Analyze the following code file and generate 3-5 conceptual flashcards to help a developer learn the key concepts, patterns, or logic in this file.

        File: {file_path.name}
        Content:
        ```
        {content[:10000]}  # Limit context size
        ```

        Output ONLY a JSON array of objects with 'question' and 'answer' keys.
        Example:
        [
            {{"question": "What is the purpose of class X?", "answer": "It handles Y..."}},
            {{"question": "How does function Z handle errors?", "answer": "It raises W..."}}
        ]
        """

        try:
            status, response, actions = await agent.run_agent_session(prompt)

            # Simple parsing attempt (extract JSON from potential markdown blocks)
            json_str = response
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0]

            data = json.loads(json_str.strip())

            new_cards = []
            for item in data:
                card = Flashcard(
                    id=str(uuid.uuid4()),
                    question=item.get("question", "Unknown"),
                    answer=item.get("answer", "Unknown"),
                    source_file=file_path.name
                )
                new_cards.append(card)

            self.cards.extend(new_cards)
            self.save_cards()
            return new_cards

        except Exception as e:
            logger.error(f"Error generating flashcards: {e}")
            raise

    def review_card(self, card_id: str, quality: int) -> None:
        """
        Updates the card schedule based on SM-2 algorithm.
        quality: 0-5 (0=blackout, 5=perfect)
        """
        card = next((c for c in self.cards if c.id == card_id), None)
        if not card:
            return

        # Update Ease Factor
        # EF' = EF + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
        card.ease_factor = card.ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
        if card.ease_factor < 1.3:
            card.ease_factor = 1.3

        if quality < 3:
            card.repetitions = 0
            card.interval = 1
        else:
            if card.repetitions == 0:
                card.interval = 1
            elif card.repetitions == 1:
                card.interval = 6
            else:
                card.interval = int(card.interval * card.ease_factor)

            card.repetitions += 1

        # Update Due Date
        next_due = datetime.now() + timedelta(days=card.interval)
        card.due_date = next_due.isoformat()
        self.save_cards()

    def get_due_cards(self) -> List[Flashcard]:
        now = datetime.now().isoformat()
        return [c for c in self.cards if c.due_date <= now]

    def delete_card(self, card_id: str) -> bool:
        initial_len = len(self.cards)
        self.cards = [c for c in self.cards if c.id != card_id]
        if len(self.cards) < initial_len:
            self.save_cards()
            return True
        return False
