"""
Chat Logic
==========

Interactive chat interface for the autonomous coding agent.
"""

import logging
import asyncio
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field

from rich.console import Console
from rich.prompt import Prompt
from rich.markdown import Markdown

from shared.config import Config
from agents.gemini import GeminiAgent
from agents.cursor import CursorAgent
from agents.local import LocalAgent
from agents.openrouter import OpenRouterAgent
from agents.shared.prompts import get_ask_prompt
from shared.utils import get_file_tree

logger = logging.getLogger(__name__)

@dataclass
class ChatTurn:
    role: str # "user" or "agent"
    content: str

class ChatSession:
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.history: List[ChatTurn] = []
        self.files_context: Dict[str, str] = {} # path -> content

    def add_turn(self, role: str, content: str):
        self.history.append(ChatTurn(role, content))

    def clear_history(self):
        self.history = []

    def add_file(self, file_path: str) -> bool:
        path = self.project_dir / file_path
        if not path.exists() or not path.is_file():
            return False
        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
            self.files_context[file_path] = content
            return True
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            return False

    def remove_file(self, file_path: str) -> bool:
        if file_path in self.files_context:
            del self.files_context[file_path]
            return True
        return False

    def list_files(self) -> List[str]:
        return list(self.files_context.keys())

class ChatManager:
    def __init__(
        self,
        project_dir: Path,
        agent_type: str = "gemini",
        model: Optional[str] = None,
        verbose: bool = False
    ):
        self.session = ChatSession(project_dir)
        self.console = Console()
        self.config = Config(
            project_dir=project_dir,
            agent_type=agent_type,
            model=model,
            verbose=verbose,
            max_iterations=1,
            stream_output=True,
        )
        self.agent = self._init_agent(agent_type)

    def _init_agent(self, agent_type: str):
        agent_class_map = {
            "gemini": GeminiAgent,
            "cursor": CursorAgent,
            "local": LocalAgent,
            "openrouter": OpenRouterAgent,
        }
        agent_class = agent_class_map.get(agent_type)
        if not agent_class:
            raise ValueError(f"Unknown agent type: {agent_type}")
        return agent_class(self.config)

    def _build_prompt(self, user_input: str) -> str:
        # Base prompt
        base_prompt = get_ask_prompt()

        # File Tree
        file_tree = get_file_tree(self.session.project_dir)

        # Context Files
        files_content = ""
        for path, content in self.session.files_context.items():
            files_content += f"\n--- File: {path} ---\n{content}\n"

        # History
        history_text = ""
        if self.session.history:
            history_text = "CONVERSATION HISTORY:\n"
            for turn in self.session.history:
                role = "User" if turn.role == "user" else "Agent"
                history_text += f"{role}: {turn.content}\n"
            history_text += "\n"

        # Combine
        full_prompt = f"{base_prompt}\n\n### PROJECT CONTEXT\n\nFile Tree:\n{file_tree}\n"

        if files_content:
            full_prompt += f"\nSelected Files Content:\n{files_content}\n"

        if history_text:
            full_prompt += f"\n{history_text}"

        # Current Question (replacing placeholder in base prompt if exists, otherwise appending)
        if "{user_question}" in full_prompt:
             full_prompt = full_prompt.replace("{user_question}", user_input)
        else:
             full_prompt += f"\nUSER QUESTION: {user_input}"

        return full_prompt

    async def run(self):
        self.console.print(f"[bold green]Starting Chat with {self.config.agent_type.capitalize()} Agent[/bold green]")
        self.console.print("Commands: /add <file>, /remove <file>, /files, /clear, /exit")

        while True:
            try:
                user_input = Prompt.ask("[bold cyan](chat)[/bold cyan]").strip()
                if not user_input:
                    continue

                if user_input.startswith("/"):
                    if await self._handle_command(user_input):
                        continue
                    if user_input in ["/exit", "/quit"]:
                        break

                # Add user turn
                self.session.add_turn("user", user_input)

                # Generate response
                prompt = self._build_prompt(user_input)

                self.console.print(f"[dim]Thinking...[/dim]")
                status, response, actions = await self.agent.run_agent_session(prompt)

                self.console.print("\n[bold magenta]Agent:[/bold magenta]")
                self.console.print(Markdown(response))
                self.console.print("")

                self.session.add_turn("agent", response)

            except (KeyboardInterrupt, EOFError):
                self.console.print("\nExiting chat.")
                break
            except Exception as e:
                self.console.print(f"[bold red]Error: {e}[/bold red]")
                logger.error(f"Chat error: {e}", exc_info=True)

    async def _handle_command(self, command: str) -> bool:
        parts = command.split()
        cmd = parts[0]
        args = parts[1:]

        if cmd == "/exit" or cmd == "/quit":
            return False # Will be handled in loop to break

        if cmd == "/clear":
            self.session.clear_history()
            self.console.print("[yellow]History cleared.[/yellow]")
            return True

        if cmd == "/files":
            files = self.session.list_files()
            if files:
                self.console.print("[bold]Context Files:[/bold]")
                for f in files:
                    self.console.print(f" - {f}")
            else:
                self.console.print("No files in context.")
            return True

        if cmd == "/add":
            if not args:
                self.console.print("[red]Usage: /add <file>[/red]")
                return True
            file_path = args[0]
            if self.session.add_file(file_path):
                self.console.print(f"[green]Added {file_path}[/green]")
            else:
                self.console.print(f"[red]Could not add {file_path}[/red]")
            return True

        if cmd == "/remove":
            if not args:
                self.console.print("[red]Usage: /remove <file>[/red]")
                return True
            file_path = args[0]
            if self.session.remove_file(file_path):
                self.console.print(f"[green]Removed {file_path}[/green]")
            else:
                self.console.print(f"[red]File {file_path} not found in context.[/red]")
            return True

        self.console.print(f"[red]Unknown command: {cmd}[/red]")
        return True

async def run_chat_logic(
    project_dir: Path,
    agent_type: str = "gemini",
    model: Optional[str] = None,
    verbose: bool = False
):
    manager = ChatManager(project_dir, agent_type, model, verbose)
    await manager.run()
