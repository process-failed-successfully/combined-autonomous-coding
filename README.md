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

### 🏃 Sprint Mode (Concurrent)

For complex projects, you can run multiple agents concurrently. A "Lead Agent" creates a plan, and "Worker Agents" execute tasks in parallel.

```bash
./safe_run.sh --sprint --max-agents 3 --spec app_spec.txt
```

## ⚙️ Common Options

The `safe_run.sh` script passes arguments directly to the agent runner. Here are the most useful options:

| Flag                       | Description                                                                 | Default                 |
| :------------------------- | :-------------------------------------------------------------------------- | :---------------------- |
| `--agent [gemini\|cursor]` | Select the AI agent to use.                                                 | `gemini`                |
| `--spec [path]`            | Path to your application specification file. Required for new projects.     | `app_spec.txt`          |
| `--project-dir [path]`     | Target directory for the project.                                           | Current Directory (`.`) |
| `--model [name]`           | Override the default model (e.g., `gemini-1.5-pro` or `claude-3-5-sonnet`). | `auto`                  |
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

## 🔔 Notifications

You can configure the agent to send notifications to **Slack** and **Discord** for key events (Iteration, Manager updates, Human-in-the-loop, Completion, Errors).

### Configuration

The agent looks for configuration in the following order:
1.  Current Directory: `./agent_config.yaml`
2.  XDG Config Home: `~/.config/combined-autonomous-coding/agent_config.yaml` (Linux/Mac) or `%LOCALAPPDATA%\combined-autonomous-coding\agent_config.yaml` (Windows)
3.  Legacy Path: `~/.gemini/agent_config.yaml`

Create a file named `agent_config.yaml` in any of these locations.

```yaml
# Webhook URLs
slack_webhook_url: "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
discord_webhook_url: "https://discord.com/api/webhooks/YOUR/WEBHOOK/URL"

# Notification Preferences
notification_settings:
  iteration: false # Summary of every iteration
  manager: true # Manager agent updates (Recommended)
  human_in_loop: true # When human intervention is requested (Recommended)
  project_completion: true # When the project is signed off (Recommended)
  error: true # On agent errors or crashes
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

## 🔄 Process Workflow

The system follows a rigorous **"Agent-Manager"** workflow to ensure high-quality output. The Manager acts as both a periodic reviewer and a final gatekeeper.

```mermaid
flowchart TD
    Start[Start Project] --> Init[Initialize Project & Spec]
    Init --> AgentLoop

    subgraph Agent Process
        AgentLoop[Agent Analysis & Execution]
        AgentLoop --> CheckTrigger{Manager Triggered?}
        CheckTrigger -- "No" --> CheckDone{Is work done?}
        CheckDone -- No --> AgentLoop
        CheckDone -- Yes (Creates COMPLETED) --> CheckSignOff{Is Signed Off?}
    end

    CheckTrigger -- "Yes (Periodic/Manual)" --> ManagerStart
    CheckSignOff -- Yes --> Finish[Project Verified & Complete]
    CheckSignOff -- No --> ManagerStart

    subgraph Manager Process
        ManagerStart[Manager Review]
        ManagerStart --> Validation{Validation}
        Validation -- "Directives / Correction" --> AgentLoop
        Validation -- "Approved (Sign-off)" --> SignOff[Create PROJECT_SIGNED_OFF]
        Validation -- "Rejected (Not Done)" --> Reject[Delete COMPLETED &\nWrite Directives]
    end

    SignOff --> AgentLoop
    Reject --> AgentLoop
```

### Manager Triggers

The Manager Agent is invoked in three ways:

1.  **Periodic Review**: Automatically runs every **X iterations** (configurable) to check progress, answer questions, and unblock the coding agent.
2.  **Manual Trigger**: The coding agent can explicitly request a review if it gets stuck.
3.  **Final Sign-off**: When the agent marks work as `COMPLETED`, the Manager **must** review and sign off (`PROJECT_SIGNED_OFF`) before the system accepts it as finished.

### 🧹 Cleaner Agent

Once the project is signed off, the **Cleaner Agent** runs to remove temporary files and artifacts, ensuring a clean repository state.

## 🏗️ Architecture

- **`main.py`**: Entry point that dispatches to the selected agent.
- **`agents/`**: Contains the logic for `gemini` and `cursor` agents.
- **`shared/`**: Common utilities (logging, config, file ops) shared between agents.
- **`Dockerfile`**: Defines the secure execution environment with necessary tools (`git`, `node`, `python`, `chromium` for browser tests).

## 🙏 Acknowledgements

This repository is based on and inspired by the [Anthropic Autonomous Coding Quickstart](https://github.com/anthropics/claude-quickstarts/tree/main/autonomous-coding).
