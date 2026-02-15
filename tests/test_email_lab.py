import unittest
import asyncio
import shutil
import json
import smtplib
from pathlib import Path
from email.message import EmailMessage
from shared.email_lab import EmailLabManager

class TestEmailLab(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.test_dir = Path("tests/temp_email_lab")
        self.test_dir.mkdir(parents=True, exist_ok=True)
        self.manager = EmailLabManager(self.test_dir)
        self.port = 1026 # Use a different port for testing

    def tearDown(self):
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def _send_mail(self, msg):
        with smtplib.SMTP('127.0.0.1', self.port) as s:
            s.send_message(msg)

    async def test_server_and_send(self):
        # Start server in background task
        # We need to catch the CancelledError inside start_server or here
        server_task = asyncio.create_task(self.manager.start_server(self.port))

        # Give it a moment to start
        await asyncio.sleep(0.5)

        # Send email using smtplib
        try:
            msg = EmailMessage()
            msg.set_content("This is a test email body.")
            msg['Subject'] = "Test Subject"
            msg['From'] = "sender@example.com"
            msg['To'] = "recipient@example.com"

            # Use run_in_executor for blocking smtplib call
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, self._send_mail, msg)

        finally:
            server_task.cancel()
            try:
                await server_task
            except asyncio.CancelledError:
                pass

        # Verify history
        history_file = self.test_dir / ".email_history.jsonl"
        self.assertTrue(history_file.exists())

        with open(history_file, 'r') as f:
            lines = f.readlines()
            self.assertEqual(len(lines), 1)
            entry = json.loads(lines[0])
            self.assertEqual(entry['sender'], "sender@example.com")
            self.assertEqual(entry['recipients'], ["recipient@example.com"])
            self.assertEqual(entry['subject'], "Test Subject")
            self.assertIn("This is a test email body.", entry['content'])

    def test_list_emails(self):
        # Create dummy history
        history_file = self.test_dir / ".email_history.jsonl"
        with open(history_file, 'w') as f:
            entry = {
                "id": "123",
                "timestamp": "2023-01-01 12:00:00",
                "sender": "a@b.c",
                "recipients": ["x@y.z"],
                "subject": "Test",
                "content": "Body"
            }
            f.write(json.dumps(entry) + "\n")

        # Capture stdout?
        # For now just ensure it doesn't crash
        self.manager.list_emails()

    def test_clear_history(self):
        history_file = self.test_dir / ".email_history.jsonl"
        history_file.touch()
        self.manager.clear_history()
        self.assertFalse(history_file.exists())

if __name__ == '__main__':
    unittest.main()
