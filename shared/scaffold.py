"""
Scaffold Manager
================

Provides project templating and scaffolding capabilities.
"""

import os
import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import Optional

from shared.config import Config
from agents.shared.prompts import get_scaffold_prompt

TEMPLATES = {
    "python-basic": {
        "description": "A minimal Python project structure.",
        "files": {
            "main.py": """def main():
    print("Hello, World!")

if __name__ == "__main__":
    main()
""",
            "requirements.txt": """# Add your dependencies here
""",
            "README.md": """# Python Project

This is a basic Python project.

## Usage

```bash
python main.py
```
""",
            ".gitignore": """__pycache__/
*.py[cod]
*$py.class
.venv/
venv/
env/
.env
"""
        }
    },
    "python-flask": {
        "description": "A Flask web application with Docker support.",
        "files": {
            "app.py": """from flask import Flask

app = Flask(__name__)

@app.route("/")
def hello():
    return "Hello from Flask!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
""",
            "requirements.txt": """flask
""",
            "Dockerfile": """FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "app.py"]
""",
            "README.md": """# Flask App

## Run Locally

```bash
pip install -r requirements.txt
python app.py
```

## Run with Docker

```bash
docker build -t flask-app .
docker run -p 5000:5000 flask-app
```
""",
            ".gitignore": """__pycache__/
*.py[cod]
*$py.class
.venv/
venv/
env/
.env
"""
        }
    },
    "node-express": {
        "description": "A minimal Node.js Express server.",
        "files": {
            "package.json": """{
  "name": "express-app",
  "version": "1.0.0",
  "description": "",
  "main": "index.js",
  "scripts": {
    "start": "node index.js"
  },
  "dependencies": {
    "express": "^4.18.2"
  }
}
""",
            "index.js": """const express = require('express');
const app = express();
const port = 3000;

app.get('/', (req, res) => {
  res.send('Hello from Express!');
});

app.listen(port, () => {
  console.log(`Example app listening on port ${port}`);
});
""",
            "README.md": """# Express App

## Run

```bash
npm install
npm start
```
""",
            ".gitignore": """node_modules/
.env
"""
        }
    },
    "html-static": {
        "description": "A simple static website.",
        "files": {
            "index.html": """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Static Site</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <h1>Hello, World!</h1>
    <script src="script.js"></script>
</body>
</html>
""",
            "style.css": """body {
    font-family: sans-serif;
    display: flex;
    justify-content: center;
    align-items: center;
    height: 100vh;
    margin: 0;
}
""",
            "script.js": """console.log('Hello from script.js');
""",
            "README.md": """# Static Site

Open `index.html` in your browser.
"""
        }
    }
}


class ScaffoldManager:
    def __init__(self, project_dir: Path, agent_type: str = "gemini"):
        self.project_dir = project_dir.resolve()
        self.agent_type = agent_type

    def list_templates(self) -> dict:
        """Returns a dictionary of available templates and their descriptions."""
        return {k: v["description"] for k, v in TEMPLATES.items()}

    def scaffold(self, template_name: str, force: bool = False) -> bool:
        """
        Creates the project structure based on the selected template.
        Returns True on success, False on failure.
        """
        if template_name not in TEMPLATES:
            print(f"❌ Template '{template_name}' not found.")
            return False

        template = TEMPLATES[template_name]
        return self.create_from_plan(template["files"], force=force)

    async def generate_ai_scaffold(
        self,
        description: str,
        agent_type: str = "gemini",
        model: Optional[str] = None
    ) -> dict:
        """
        Generates a file structure plan using AI based on the description.
        Returns a dict of {filename: content} or empty dict on error.
        """
        # Import inside method to avoid circular dependency
        from agents.gemini import GeminiAgent
        from agents.cursor import CursorAgent
        from agents.local import LocalAgent
        from agents.openrouter import OpenRouterAgent

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
            print(f"❌ Unknown agent type: {agent_type}")
            return {}

        agent = agent_class(config)
        prompt = get_scaffold_prompt().replace("{description}", description)

        print(f"Requesting scaffold plan from {agent_type}...")
        try:
            _, response, _ = await agent.run_agent_session(prompt)

            # Extract JSON block
            json_match = re.search(r"```(?:json)?\n(.*?)```", response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1).strip()
            else:
                # Try parsing raw response if it looks like JSON
                json_str = response.strip()

            try:
                files_dict = json.loads(json_str)
                if isinstance(files_dict, dict):
                    return files_dict
                else:
                    print("❌ Error: AI response is not a valid JSON object.")
                    return {}
            except json.JSONDecodeError as e:
                print(f"❌ Error decoding JSON from AI response: {e}")
                print(f"Response was: {response[:200]}...")
                return {}

        except Exception as e:
            print(f"❌ Error generating scaffold: {e}")
            return {}

    def create_from_plan(self, plan: dict, force: bool = False) -> bool:
        """
        Creates files based on the plan dictionary {filename: content}.
        """
        # Check for existing files
        if not force:
            existing = [f for f in plan.keys() if (self.project_dir / f).exists()]
            if existing:
                print(f"❌ Error: The following files already exist in {self.project_dir}:")
                for f in existing:
                    print(f"  - {f}")
                print("Use --force to overwrite.")
                return False

        print(f"--- Scaffolding {len(plan)} files ---")
        self.project_dir.mkdir(parents=True, exist_ok=True)

        try:
            for filename, content in plan.items():
                file_path = self.project_dir / filename

                # Sanitize path to prevent breaking out of project root
                try:
                    file_path.resolve().relative_to(self.project_dir)
                except ValueError:
                    print(f"❌ Error: Skipping {filename} (outside project directory)")
                    continue

                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(content.strip() + "\n", encoding="utf-8")
                print(f"✅ Created {filename}")

            # Initialize git if not present
            if shutil.which("git") and not (self.project_dir / ".git").exists():
                subprocess.run(["git", "init"], cwd=self.project_dir, check=True, capture_output=True)
                print("✅ Initialized git repository.")

            return True

        except Exception as e:
            print(f"❌ Error during scaffolding: {e}")
            return False
