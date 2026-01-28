import asyncio
from pathlib import Path
from typing import List, Dict, Optional

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from shared.config import Config
from shared.utils import get_file_tree, process_response_blocks
from agents.gemini.client import GeminiClient
from agents.cursor.client import CursorClient

class ChatManager:
    """
    Manages an interactive chat session with the agent.
    """

    def __init__(self, project_dir: Path, agent_type: str = "gemini", model: Optional[str] = None):
        self.project_dir = project_dir.resolve()
        self.config = Config(
            project_dir=self.project_dir,
            agent_type=agent_type,
            model=model,
            verbose=False # Keep CLI clean
        )
        self.agent_type = agent_type

        if agent_type == "cursor":
            self.client = CursorClient(self.config)
        else:
            self.client = GeminiClient(self.config)

        self.console = Console()
        self.history: List[Dict[str, str]] = []

    def _build_prompt(self, user_input: str) -> str:
        """Constructs the prompt with context and history."""
        file_tree = get_file_tree(self.project_dir)

        system_prompt = f"""
You are an interactive coding assistant working in: {self.project_dir}
Your goal is to help the user with their coding tasks, questions, and debugging.

Capabilities:
- You can execute bash commands using ```bash ... ``` blocks.
- You can read files using ```read:filename```.
- You can write files using ```write:filename``` (content in block).
- You can search using ```search:query```.

Current File Structure:
{file_tree}

Instructions:
- Be concise and helpful.
- If you execute a command, I will show you the output in the next turn.
- Maintain the conversation flow.
"""

        # Format history
        history_text = ""
        for turn in self.history:
            role = turn['role'].upper()
            content = turn['content']
            history_text += f"\n[{role}]:\n{content}\n"

        full_prompt = f"{system_prompt}\n\nCONVERSATION HISTORY:{history_text}\n\n[USER]:\n{user_input}\n\n[AGENT]:"
        return full_prompt

    async def _process_turn(self, user_input: str) -> str:
        """Process a single turn of conversation."""
        prompt = self._build_prompt(user_input)

        # Call Agent
        with self.console.status(f"[{self.agent_type}] Thinking...", spinner="dots"):
            response_data = await self.client.run_command(prompt, self.project_dir)

        # Parse Response
        response_text = ""
        if "content" in response_data:
            response_text = response_data["content"]
        elif "candidates" in response_data:
             # Handle raw Gemini response if run_command returns it
             for candidate in response_data["candidates"]:
                for part in candidate.get("content", {}).get("parts", []):
                    if "text" in part:
                        response_text += part["text"]
        elif "response" in response_data:
            response_text = response_data["response"]

        # Display Agent Response
        self.console.print(Panel(Markdown(response_text), title=f"{self.agent_type.capitalize()}", border_style="blue"))

        # Add to history (User)
        self.history.append({"role": "user", "content": user_input})

        # Process Blocks
        log, actions = await process_response_blocks(
            response_text,
            self.project_dir,
            self.config.bash_timeout
        )

        final_agent_content = response_text
        if log:
            # If tools ran, append output to the agent's content in history so it "sees" it next time
            final_agent_content += f"\n\n[TOOL OUTPUT]:\n{log}"
            self.console.print(Panel(log, title="Tool Output", border_style="yellow"))

        self.history.append({"role": "agent", "content": final_agent_content})

        return response_text

    async def run(self):
        """Starts the interactive loop."""
        self.console.print(f"[bold green]Starting Chat Session in {self.project_dir}[/bold green]")
        self.console.print("Type 'exit' or 'quit' to end. Type '/clear' to reset history.")

        while True:
            try:
                user_input = self.console.input("[bold green]You > [/bold green]").strip()

                if not user_input:
                    continue

                if user_input.lower() in ["exit", "quit", "/exit", "/quit"]:
                    self.console.print("Goodbye!")
                    break

                if user_input.lower() == "/clear":
                    self.history = []
                    self.console.print("[yellow]History cleared.[/yellow]")
                    continue

                if user_input.lower() == "/history":
                    self.console.print(self.history)
                    continue

                await self._process_turn(user_input)

            except KeyboardInterrupt:
                self.console.print("\n[yellow]Interrupted. Type 'exit' to quit.[/yellow]")
            except Exception as e:
                self.console.print(f"[bold red]Error:[/bold red] {e}")
