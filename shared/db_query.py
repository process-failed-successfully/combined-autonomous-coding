"""
DB Query Logic
==============

Logic for the 'db query' command to query the database using natural language.
"""

import sys
import logging
import sqlite3
from pathlib import Path
from typing import Optional, Tuple, List, Any

from shared.config import Config
from agents.gemini import GeminiAgent
from agents.cursor import CursorAgent
from agents.local import LocalAgent
from agents.openrouter import OpenRouterAgent
from shared.database_manager import DatabaseManager, DatabaseFramework

logger = logging.getLogger(__name__)


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


def is_read_only_query(sql: str) -> bool:
    """Checks if a SQL query is read-only (SELECT, PRAGMA, EXPLAIN)."""
    sql = sql.strip().lower()
    # Note: 'WITH' is excluded because CTEs can be used with DELETE/UPDATE/INSERT
    return sql.startswith(("select", "pragma", "explain"))


def get_schema_info(project_dir: Path) -> Tuple[str, Optional[Path]]:
    """
    Detects the database and retrieves schema information.
    Returns (schema_string, db_path).
    """
    db_manager = DatabaseManager(project_dir)
    framework = db_manager.detect_framework()

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

    return schema_info, db_path


async def generate_sql(
    query: str,
    schema_info: str,
    project_dir: Path,
    agent_type: str = "gemini",
    model: Optional[str] = None,
    verbose: bool = False
) -> str:
    """
    Uses the agent to translate natural language query to SQL.
    """
    config = Config(
        project_dir=project_dir,
        agent_type=agent_type,
        model=model,
        verbose=verbose,
        max_iterations=1,
        stream_output=False,  # We want the SQL cleanly
    )

    agent_class_map = {
        "gemini": GeminiAgent,
        "cursor": CursorAgent,
        "local": LocalAgent,
        "openrouter": OpenRouterAgent,
    }

    agent_class = agent_class_map.get(agent_type)
    if not agent_class:
        raise ValueError(f"Unknown agent type: {agent_type}")

    agent = agent_class(config)  # type: ignore[abstract]

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

    try:
        status, response, actions = await agent.run_agent_session(prompt)
        sql_query = response.strip().replace("```sql", "").replace("```", "").strip()
        return sql_query
    except Exception as e:
        logger.error(f"Error generating SQL: {e}")
        return f"ERROR: {e}"


def execute_sqlite(db_path: Path, sql: str) -> Tuple[List[str], List[Tuple[Any, ...]], int]:
    """
    Executes SQL on a SQLite DB.
    Returns (columns, rows, rowcount).
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(sql)

        columns = []
        rows = []
        rowcount = cursor.rowcount

        if cursor.description:
            columns = [description[0] for description in cursor.description]
            rows = cursor.fetchall()
        else:
            conn.commit()

        conn.close()
        return columns, rows, rowcount
    except Exception as e:
        raise e


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
    """
    # 1. Detect Database and Schema
    schema_info, db_path = get_schema_info(project_dir)

    if not schema_info:
        print("❌ No SQLite database found and generic introspection not yet implemented for this framework.", file=sys.stderr)
        return False

    # 2. Get SQL from Agent
    print(f"Analyzing schema and generating SQL for: '{query}'...")
    sql_query = await generate_sql(query, schema_info, project_dir, agent_type, model, verbose)

    if sql_query.startswith("ERROR:"):
        print(f"❌ {sql_query}")
        return False

    print(f"\nGenerated SQL: \033[1m{sql_query}\033[0m")

    # 3. Confirm Execution
    if not is_read_only_query(sql_query) and not yes:
        print("⚠️  This query may modify data.")
        confirm = input("Execute this query? [y/N]: ").strip().lower()
        if confirm != 'y':
            print("Aborted.")
            return True

    # 4. Execute SQL
    if db_path:
        try:
            columns, rows, rowcount = execute_sqlite(db_path, sql_query)

            if columns:
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
                print(f"✅ Executed successfully. Rows affected: {rowcount}")

        except Exception as e:
            print(f"❌ SQL Execution Error: {e}")
            return False
    else:
        print("❌ Database connection logic for non-SQLite not fully implemented in this prototype.")
        return False

    return True
