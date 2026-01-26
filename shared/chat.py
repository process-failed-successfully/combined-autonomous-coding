"""
Chat Logic
==========

Interactive chat session with the agent.
"""

import sys
import logging
from pathlib import Path
from typing import Optional, List, Dict
from datetime import datetime

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from shared.config import Config
from agents.gemini import GeminiAgent
from agents.cursor import CursorAgent
from agents.local import LocalAgent
from agents.openrouter import OpenRouterAgent
from agents.shared.prompts import get_chat_prompt
from shared.utils import get_file_tree

logger = logging.getLogger(__name__)

class ChatSession:
    def __init__(self, project_dir: Path, agent_type: str = "gemini", model: Optional[str] = None):
        self.project_dir = project_dir
        self.agent_type = agent_type
        self.model = model
        self.history: List[Dict[str, str]] = [] # [{"role": "user", "content": "..."}]
        self.context_files: List[Path] = []
        self.console = Console()

        # Initialize Agent
        self.config = Config(
            project_dir=project_dir,
            agent_type=agent_type,
            model=model,
            max_iterations=1,
            stream_output=True,
            verbose=False
        )

        agent_class_map = {
            "gemini": GeminiAgent,
            "cursor": CursorAgent,
            "local": LocalAgent,
            "openrouter": OpenRouterAgent,
        }

        self.agent_class = agent_class_map.get(agent_type)
        if not self.agent_class:
            raise ValueError(f"Unknown agent type: {agent_type}")

        self.agent = self.agent_class(self.config)

    def add_user_message(self, message: str):
        self.history.append({"role": "user", "content": message})

    def add_agent_message(self, message: str):
        self.history.append({"role": "agent", "content": message})

    def add_context_file(self, filepath: str):
        path = self.project_dir / filepath
        if path.exists() and path.is_file():
            if path not in self.context_files:
                self.context_files.append(path)
                self.console.print(f"[green]Added {filepath} to context.[/green]")
            else:
                self.console.print(f"[yellow]{filepath} is already in context.[/yellow]")
        else:
            self.console.print(f"[red]File not found: {filepath}[/red]")

    def clear_history(self):
        self.history = []
        self.console.print("[yellow]Conversation history cleared.[/yellow]")

    def save_transcript(self, filename: Optional[str] = None):
        if not filename:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = f"chat_transcript_{timestamp}.md"

        path = self.project_dir / filename

        content = "# Chat Transcript\n\n"
        for msg in self.history:
            role = msg["role"].upper()
            text = msg["content"]
            content += f"## {role}\n\n{text}\n\n"

        try:
            path.write_text(content, encoding="utf-8")
            self.console.print(f"[green]Transcript saved to {filename}[/green]")
        except Exception as e:
            self.console.print(f"[red]Error saving transcript: {e}[/red]")

    async def run_turn(self):
        if not self.history or self.history[-1]["role"] != "user":
            return

        user_message = self.history[-1]["content"]

        # Construct Prompt
        base_prompt = get_chat_prompt()

        # Format History
        history_text = ""
        for msg in self.history[:-1]: # Exclude current message
            role = "User" if msg["role"] == "user" else "Agent"
            history_text += f"**{role}**: {msg['content']}\n\n"

        if not history_text:
            history_text = "(No previous conversation)"

        # Prepare Context Files
        files_content = ""
        for path in self.context_files:
            try:
                content = path.read_text(encoding="utf-8", errors="ignore")
                files_content += f"\n--- File: {path.name} ---\n{content}\n"
            except Exception:
                pass

        # File Tree
        file_tree = get_file_tree(self.project_dir)

        # Assemble Full Prompt
        # We manually replace placeholders because we are managing the full context structure
        full_prompt = base_prompt.replace("{history}", history_text)
        full_prompt = full_prompt.replace("{user_message}", user_message)

        full_prompt += f"\n\n### PROJECT CONTEXT\n\nFile Tree:\n{file_tree}\n"

        if files_content:
            full_prompt += f"\nSelected Files Content:\n{files_content}"

        self.console.print("[bold blue]Agent is thinking...[/bold blue]")

        try:
            # Run Agent
            # Note: We capture stdout/stderr to suppress some internal logging if needed,
            # but since we want streaming, we let it flow to stdout mostly.
            # However, run_agent_session usually prints actions.
            # For chat, the response is text.

            status, response, actions = await self.agent.run_agent_session(full_prompt)

            if status == "error":
                self.console.print(f"[red]Error: {response}[/red]")
                return

            # Display Response
            self.console.print(Panel(Markdown(response), title="Agent", border_style="green"))

            self.add_agent_message(response)

        except Exception as e:
            logger.error(f"Error in chat turn: {e}")
            self.console.print(f"[red]An error occurred: {e}[/red]")

async def run_chat_logic(
    project_dir: Path,
    agent_type: str = "gemini",
    model: Optional[str] = None,
):
    session = ChatSession(project_dir, agent_type, model)

    console = session.console
    console.print(f"[bold green]Starting Chat Session with {agent_type.capitalize()}[/bold green]")
    console.print("Type your message below. Commands: /add <file>, /clear, /save, /exit")

    while True:
        try:
            user_input = console.input("[bold yellow]You > [/bold yellow]").strip()

            if not user_input:
                continue

            if user_input.lower() in ["/exit", "/quit", "/q"]:
                console.print("Goodbye!")
                break

            if user_input.lower().startswith("/add "):
                filepath = user_input[5:].strip()
                session.add_context_file(filepath)
                continue

            if user_input.lower() == "/clear":
                session.clear_history()
                continue

            if user_input.lower().startswith("/save"):
                filename = user_input[6:].strip() or None
                session.save_transcript(filename)
                continue

            # Normal message
            session.add_user_message(user_input)
            await session.run_turn()

        except KeyboardInterrupt:
            console.print("\n[yellow]Interrupted. Type /exit to quit.[/yellow]")
        except EOFError:
            break
