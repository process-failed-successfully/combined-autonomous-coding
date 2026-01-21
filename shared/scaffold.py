"""
Scaffold Manager
================

Provides project templating and scaffolding capabilities.
"""

import os
from pathlib import Path
import subprocess
import shutil

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
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir.resolve()

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
        files = template["files"]

        # Check for existing files
        if not force:
            existing = [f for f in files if (self.project_dir / f).exists()]
            if existing:
                print(f"❌ Error: The following files already exist in {self.project_dir}:")
                for f in existing:
                    print(f"  - {f}")
                print("Use --force to overwrite.")
                return False

        print(f"--- Scaffolding project with template: {template_name} ---")
        self.project_dir.mkdir(parents=True, exist_ok=True)

        try:
            for filename, content in files.items():
                file_path = self.project_dir / filename
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(content.strip() + "\n")
                print(f"✅ Created {filename}")

            # Initialize git if not present
            if shutil.which("git") and not (self.project_dir / ".git").exists():
                subprocess.run(["git", "init"], cwd=self.project_dir, check=True, capture_output=True)
                print("✅ Initialized git repository.")

            # Create a default app_spec.txt if not provided by template
            if "app_spec.txt" not in files:
                spec_content = f"Application based on {template_name} template.\n"
                (self.project_dir / "app_spec.txt").write_text(spec_content)
                print("✅ Created app_spec.txt")

            return True

        except Exception as e:
            print(f"❌ Error during scaffolding: {e}")
            return False
