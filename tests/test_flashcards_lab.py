import unittest
import shutil
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch
from datetime import datetime, timedelta

from shared.flashcards_lab import FlashcardsManager, Flashcard


class TestFlashcardsManager(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.manager = FlashcardsManager(self.test_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_save_and_load_cards(self):
        card = Flashcard(
            id="1",
            question="Q",
            answer="A",
            source_file="test.py"
        )
        self.manager.cards = [card]
        self.manager.save_cards()

        # Check file exists
        self.assertTrue((self.test_dir / ".flashcards.json").exists())

        # Reload
        new_manager = FlashcardsManager(self.test_dir)
        self.assertEqual(len(new_manager.cards), 1)
        self.assertEqual(new_manager.cards[0].question, "Q")
        self.assertEqual(new_manager.cards[0].id, "1")

    def test_review_card_sm2_algorithm(self):
        card = Flashcard(
            id="1",
            question="Q",
            answer="A",
            source_file="test.py",
            interval=0,
            repetitions=0,
            ease_factor=2.5
        )
        self.manager.cards = [card]

        # First review (Quality 4 - Pass)
        # Reps: 0 -> 1
        # Interval: 0 -> 1
        self.manager.review_card("1", 4)
        self.assertEqual(card.repetitions, 1)
        self.assertEqual(card.interval, 1)
        self.assertEqual(card.ease_factor, 2.5)  # q=4 keeps EF same (0.1 - (1)*(0.08+0.02) = 0)

        # Second review (Quality 5 - Perfect)
        # Reps: 1 -> 2
        # Interval: 1 -> 6
        self.manager.review_card("1", 5)
        self.assertEqual(card.repetitions, 2)
        self.assertEqual(card.interval, 6)

        # Third review (Quality 4)
        # Reps: 2 -> 3
        # Interval: 6 * EF
        prev_interval = card.interval
        prev_ef = card.ease_factor
        self.manager.review_card("1", 4)
        self.assertEqual(card.repetitions, 3)
        expected_interval = int(prev_interval * prev_ef)
        self.assertEqual(card.interval, expected_interval)

        # Fail (Quality 1)
        # Reps -> 0
        # Interval -> 1
        self.manager.review_card("1", 1)
        self.assertEqual(card.repetitions, 0)
        self.assertEqual(card.interval, 1)
        # EF should decrease but not below 1.3
        self.assertTrue(card.ease_factor < prev_ef)

    def test_get_due_cards(self):
        past = (datetime.now() - timedelta(days=1)).isoformat()
        future = (datetime.now() + timedelta(days=1)).isoformat()

        card1 = Flashcard(id="1", question="Q1", answer="A", source_file="a", due_date=past)
        card2 = Flashcard(id="2", question="Q2", answer="A", source_file="a", due_date=future)

        self.manager.cards = [card1, card2]
        due = self.manager.get_due_cards()

        self.assertEqual(len(due), 1)
        self.assertEqual(due[0].id, "1")

    def test_delete_card(self):
        card = Flashcard(id="1", question="Q", answer="A", source_file="a")
        self.manager.cards = [card]

        self.assertTrue(self.manager.delete_card("1"))
        self.assertEqual(len(self.manager.cards), 0)
        self.assertFalse(self.manager.delete_card("999"))


class TestFlashcardsGeneration(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.manager = FlashcardsManager(self.test_dir)

        self.dummy_file = self.test_dir / "test_code.py"
        self.dummy_file.write_text("def hello(): pass")

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    @patch('shared.flashcards_lab.GeminiAgent')
    async def test_generate_flashcards(self, MockAgent):
        # Mock the agent instance and its run_agent_session method
        mock_agent_instance = MockAgent.return_value

        # Mock response: valid JSON
        mock_response = '[{"question": "What does hello do?", "answer": "Nothing"}]'
        mock_agent_instance.run_agent_session = AsyncMock(return_value=(True, mock_response, []))

        cards = await self.manager.generate_flashcards(self.dummy_file, agent_type="gemini")

        self.assertEqual(len(cards), 1)
        self.assertEqual(cards[0].question, "What does hello do?")
        self.assertEqual(cards[0].source_file, "test_code.py")

        # Verify saved
        self.assertEqual(len(self.manager.cards), 1)

    @patch('shared.flashcards_lab.GeminiAgent')
    async def test_generate_flashcards_with_markdown_block(self, MockAgent):
        # Mock the agent instance
        mock_agent_instance = MockAgent.return_value

        # Mock response: JSON in markdown block
        mock_response = 'Here are the cards:\n```json\n[{"question": "Q", "answer": "A"}]\n```'
        mock_agent_instance.run_agent_session = AsyncMock(return_value=(True, mock_response, []))

        cards = await self.manager.generate_flashcards(self.dummy_file, agent_type="gemini")

        self.assertEqual(len(cards), 1)
        self.assertEqual(cards[0].question, "Q")


if __name__ == '__main__':
    unittest.main()
