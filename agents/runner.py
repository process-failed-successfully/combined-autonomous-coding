import os
from pathlib import Path
from typing import Optional

from shared.config import Config, JiraConfig
from shared.logger import setup_logger
from shared.git import ensure_git_safe
from shared.config_loader import load_config_from_file, ensure_config_exists
from shared.utils import generate_agent_id
from shared.agent_client import AgentClient

# Import agent runners
from agents.gemini import run_autonomous_agent as run_gemini
from agents.shared.sprint import run_sprint as run_sprint
from agents.cursor import run_autonomous_agent as run_cursor


async def run_agent(
    project_dir: Path = Path("."),
    agent_type: str = "gemini",
    model: Optional[str] = None,
    max_iterations: Optional[int] = None,
    spec_file: Optional[Path] = None,
    verbose: bool = False,
    jira_ticket: Optional[str] = None,
    jira_label: Optional[str] = None,
    detached: bool = False,
    name: Optional[str] = None,
):
    # Initialize Configuration
    ensure_config_exists()
    file_config = load_config_from_file()

    def resolve(cli_arg, config_key, default_val):
        if cli_arg is not None:
            return cli_arg
        if config_key in file_config:
            return file_config[config_key]
        return default_val

    project_name = os.environ.get("PROJECT_NAME")
    if not project_name:
        project_name = project_dir.resolve().name

    config = Config(
        project_dir=project_dir,
        agent_id=None,
        agent_type=agent_type,
        model=resolve(model, "model", None),
        max_iterations=resolve(max_iterations, "max_iterations", None),
        verbose=verbose,
        stream_output=not detached,
        spec_file=spec_file,

        # Defaults
        manager_frequency=resolve(None, "manager_frequency", 10),
        manager_model=resolve(None, "manager_model", None),
        run_manager_first=False,
        login_mode=file_config.get("login_mode", False),
        timeout=resolve(None, "timeout", 600.0),
        sprint_mode=file_config.get("sprint_mode", False),
        max_agents=resolve(None, "max_agents", 1),
    )

    # Jira Logic
    jira_cfg_data = file_config.get("jira", {{}})
    jira_env_url = os.environ.get("JIRA_URL")
    jira_env_email = os.environ.get("JIRA_EMAIL")
    jira_env_token = os.environ.get("JIRA_TOKEN")

    if jira_env_url:
        jira_cfg_data["url"] = jira_env_url
    if jira_env_email:
        jira_cfg_data["email"] = jira_env_email
    if jira_env_token:
        jira_cfg_data["token"] = jira_env_token

    jira_spec_content = ""
    if jira_ticket or jira_label:
        if not jira_cfg_data:
            raise ValueError("Jira configuration missing.")
        config.jira = JiraConfig(**jira_cfg_data)

        from shared.jira_client import JiraClient
        jira_client = JiraClient(config.jira)

        issue = None
        if jira_ticket:
            issue = jira_client.get_issue(jira_ticket)
        elif jira_label:
            issue = jira_client.get_first_todo_by_label(jira_label)

        if issue:
            config.jira_ticket_key = issue.key
            jira_spec_content = f"JIRA TICKET {issue.key}\nSUMMARY: {issue.fields.summary}\nDESCRIPTION:\n{issue.fields.description or ''}"
            config.jira_spec_content = jira_spec_content
            project_name = issue.key

            start_status = config.jira.status_map.get("start", "In Progress") if config.jira.status_map else "In Progress"
            jira_client.transition_issue(issue.key, start_status)
        else:
            print("No suitable Jira ticket found.")
            return

    # ID Generation
    spec_content = jira_spec_content
    if not spec_content and spec_file and spec_file.exists():
        spec_content = spec_file.read_text()

    agent_id = generate_agent_id(project_name, spec_content, agent_type)
    config.agent_id = agent_id

    # Logging
    repo_root = Path(__file__).parent.parent
    agents_log_dir = repo_root / "agents/logs"
    agents_log_dir.mkdir(parents=True, exist_ok=True)
    log_file = agents_log_dir / f"{agent_id}.log"
    logger = setup_logger(name="", log_file=log_file, verbose=verbose)

    logger.info(f"Starting {agent_type} Agent. ID: {agent_id}")

    client = AgentClient(agent_id=agent_id, dashboard_url=file_config.get("dashboard_url", "http://localhost:7654"))

    # Git Safety
    ensure_git_safe(project_dir, ticket_key=config.jira_ticket_key)

    # Run
    try:
        if config.sprint_mode:
            await run_sprint(config, agent_client=client)
        elif agent_type == "gemini":
            await run_gemini(config, agent_client=client)
        elif agent_type == "cursor":
            await run_cursor(config, agent_client=client)
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        raise

    # Cleanup
    if (project_dir / "PROJECT_SIGNED_OFF").exists():
        if config.jira and config.jira_ticket_key:
            from shared.workflow import complete_jira_ticket
            await complete_jira_ticket(config)

        from agents.cleaner import run_cleaner_agent
        await run_cleaner_agent(config, agent_client=client)
