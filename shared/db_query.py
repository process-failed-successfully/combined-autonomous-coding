"""
DB Query Logic
==============

Logic for the 'db query' command to query the database using natural language.
"""

import sys
import logging
import sqlite3
import subprocess
from pathlib import Path
from typing import Optional

from shared.config import Config
from agents.gemini import GeminiAgent
from agents.cursor import CursorAgent
from agents.local import LocalAgent
from agents.openrouter import OpenRouterAgent
from shared.database_manager import DatabaseManager, DatabaseFramework

logger = logging.getLogger(__name__)

async def run_db_query_logic(
    query: str,
    project_dir: Path,
    agent_type: str = "gemini",
    model: Optional[str] = None,
    yes: bool = False,
    verbose: bool = False,
) -> bool:
    """
    Executes the 'db query' logic.

    Args:
        query: The natural language query.
        project_dir: The project root directory.
        agent_type: The type of agent to use.
        model: The model to use.
        yes: Skip confirmation if True.
        verbose: Enable verbose logging.

    Returns:
        True if successful, False otherwise.
    """

    # 1. Detect Database and Schema
    db_manager = DatabaseManager(project_dir)
    framework = db_manager.detect_framework()

    # Introspect schema
    # For now, we support SQLite directly, and for others we might need a dump or generic introspection
    # Start with SQLite support as it's the agent's default

    schema_info = ""
    db_path = None

    # Try to find common SQLite files
    potential_dbs = list(project_dir.glob("*.sqlite")) + list(project_dir.glob("*.db")) + list(project_dir.glob("*.sqlite3"))
    if potential_dbs:
        db_path = potential_dbs[0]
        schema_info = _get_sqlite_schema(db_path)
    else:
        # TODO: Support other DBs via introspection commands
        if framework == DatabaseFramework.DJANGO:
             # Could use 'python manage.py inspectdb'
             pass

        if not schema_info:
            print("❌ No SQLite database found and generic introspection not yet implemented for this framework.", file=sys.stderr)
            return False

    # 2. Setup Agent
    config = Config(
        project_dir=project_dir,
        agent_type=agent_type,
        model=model,
        verbose=verbose,
        max_iterations=1,
        stream_output=False, # We want the SQL cleanly
    )

    agent_class_map = {
        "gemini": GeminiAgent,
        "cursor": CursorAgent,
        "local": LocalAgent,
        "openrouter": OpenRouterAgent,
    }

    agent_class = agent_class_map.get(agent_type)
    if not agent_class:
        logger.error(f"Unknown agent type: {agent_type}")
        return False

    agent = agent_class(config)

    # 3. Construct Prompt
    prompt = f"""
You are an expert SQL assistant.
Your task is to convert a natural language query into a valid SQL query based on the provided schema.

### Database Schema
{schema_info}

### User Query
{query}

### Instructions
1. Return ONLY the SQL query.
2. Do not include markdown formatting (like ```sql).
3. Do not include explanations.
4. If the query cannot be answered by the schema, return "ERROR: Cannot answer".
"""

    # 4. Get SQL from Agent
    print(f"Analyzing schema and generating SQL for: '{query}'...")
    try:
        # Using run_agent_session or equivalent to get text response
        # Since run_agent_session returns (status, response, actions), we use response.
        status, response, actions = await agent.run_agent_session(prompt)
        sql_query = response.strip().replace("```sql", "").replace("```", "").strip()

        if sql_query.startswith("ERROR:"):
            print(f"❌ {sql_query}")
            return False

    except Exception as e:
        logger.error(f"Error generating SQL: {e}")
        return False

    print(f"\nGenerated SQL: \033[1m{sql_query}\033[0m")

    # 5. Confirm Execution (unless --yes or read-only safe?)
    # Simple heuristic for read-only
    is_read_only = sql_query.lower().startswith("select")

    if not is_read_only and not yes:
        print("⚠️  This query may modify data.")
        confirm = input("Execute this query? [y/N]: ").strip().lower()
        if confirm != 'y':
            print("Aborted.")
            return True

    # 6. Execute SQL
    if db_path:
        _execute_sqlite(db_path, sql_query)
    else:
        print("❌ Database connection logic for non-SQLite not fully implemented in this prototype.")
        return False

    return True

def _get_sqlite_schema(db_path: Path) -> str:
    """Extracts CREATE TABLE statements from a SQLite DB."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        schema = "\n".join([t[0] for t in tables if t[0]])
        conn.close()
        return schema
    except Exception as e:
        return f"Error reading schema: {e}"

def _execute_sqlite(db_path: Path, sql: str):
    """Executes SQL on a SQLite DB and prints results."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(sql)

        if sql.lower().startswith("select"):
            columns = [description[0] for description in cursor.description]
            rows = cursor.fetchall()

            # Simple table print
            if not rows:
                print("No results found.")
            else:
                # Calculate widths
                widths = [len(c) for c in columns]
                for row in rows:
                    for i, val in enumerate(row):
                        widths[i] = max(widths[i], len(str(val)))

                # Print Header
                header = " | ".join(f"{c:<{w}}" for c, w in zip(columns, widths))
                print("-" * len(header))
                print(header)
                print("-" * len(header))

                # Print Rows
                for row in rows:
                    print(" | ".join(f"{str(val):<{w}}" for val, w in zip(row, widths)))
                print(f"\n({len(rows)} rows)")
        else:
            conn.commit()
            print(f"✅ Executed successfully. Rows affected: {cursor.rowcount}")

        conn.close()
    except Exception as e:
        print(f"❌ SQL Execution Error: {e}")
