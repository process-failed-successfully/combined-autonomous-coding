# Combined Autonomous Coding Agent

[![Robust CI](https://github.com/process-failed-successfully/combined-autonomous-coding/actions/workflows/ci.yml/badge.svg)](https://github.com/process-failed-successfully/combined-autonomous-coding/actions/workflows/ci.yml)

This project provides a unified interface for running autonomous coding agents using either the **Gemini CLI** or the **Cursor Agent**. It runs securely within a Docker container to ensure isolation and safety.

## 🚀 Quick Start

1.  **Prerequisites**: Ensure you have [Docker](https://www.docker.com/) and `docker compose` installed.
2.  **Prepare your spec**: Create a file named `app_spec.txt` in your current directory describing the application you want to build.

### Running with Default Settings (Gemini)

```bash
./safe_run.sh --spec app_spec.txt
```

This will:

- Build the Docker container (if needed).
- Mount your current directory as the project workspace.
- Start the **Gemini** agent to build the app described in `app_spec.txt`.

## 🤖 Selecting an Agent

You can choose between the `gemini` (default) and `cursor` agents using the `--agent` flag.

### Using Gemini Agent

```bash
./safe_run.sh --agent gemini --spec app_spec.txt
```

### Using Cursor Agent

```bash
./safe_run.sh --agent cursor --spec app_spec.txt
```

## ⚙️ Common Options

The `safe_run.sh` script passes arguments directly to the agent runner. Here are the most useful options:

| Flag                       | Description                                                                 | Default                 |
| :------------------------- | :-------------------------------------------------------------------------- | :---------------------- |
| `--agent [gemini\|cursor]` | Select the AI agent to use.                                                 | `gemini`                |
| `--spec [path]`            | Path to your application specification file. Required for new projects.     | `app_spec.txt`          |
| `--project-dir [path]`     | Target directory for the project.                                           | Current Directory (`.`) |
| `--model [name]`           | Override the default model (e.g., `gemini-1.5-pro` or `claude-3-5-sonnet`). | Agent Default           |
| `--max-iterations [N]`     | Limit the number of agent loops.                                            | Unlimited               |
| `--no-stream`              | **Disable** real-time streaming output (useful for logs).                   | Streaming Enabled       |
| `--verbose`                | Enable debug logging.                                                       | `False`                 |

### Example: Custom Project Directory and Model

```bash
./safe_run.sh \
  --agent cursor \
  --project-dir ./my-new-app \
  --spec ./specs/todo-app.txt \
  --model claude-3-5-sonnet \
  --max-iterations 20
```

## 🛠️ Development & Troubleshooting

- **Rebuild Container**: If you modify the agent code, force a rebuild:
  ```bash
  ./safe_run.sh --build ...
  ```
- **Git Issues**: The container is configured to handle git ownership issues automatically.
- **Streaming**: By default, the agent streams its "thought process" capability. Use `--no-stream` if you prefer a cleaner, buffered output.

## 🧪 Quality Assurance & CI

This repository uses **GitHub Actions** for robust Continuous Integration.

### Local Testing

You can run the same checks locally using the test script:

```bash
./run_tests.sh
```

This runs:

1. **Flake8** (Linting)
2. **Mypy** (Type Checking)
3. **Bandit** (Security Scan)
4. **Unit Tests**

### Automated Checks

On every push and PR, the CI pipeline performs:

- Python checks (Lint, Type, Security, Test)
- Docker Build verification
- **Trivy** Container Security Scanning

## 🏗️ Architecture

- **`main.py`**: Entry point that dispatches to the selected agent.
- **`agents/`**: Contains the logic for `gemini` and `cursor` agents.
- **`shared/`**: Common utilities (logging, config, file ops) shared between agents.
- **`Dockerfile`**: Defines the secure execution environment with necessary tools (`git`, `node`, `python`, `chromium` for browser tests).
