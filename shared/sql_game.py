import sqlite3
import sys
import io
import contextlib
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from shared.ask import run_ask_logic

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.syntax import Syntax
    console = Console()
    HAS_RICH = True
except ImportError:
    HAS_RICH = False
    console = None

@dataclass
class SqlGameLevel:
    name: str
    description: str
    setup_sql: str
    solution_sql: str
    hint: str = ""

class SqlGameEngine:
    """
    Engine for running the SQL Game.
    """
    def __init__(self):
        pass

    def validate(self, user_sql: str, level: SqlGameLevel) -> Dict[str, Any]:
        """
        Validates the user's SQL query against the level's solution.
        """
        # Create an in-memory database for this validation run
        conn = sqlite3.connect(":memory:")
        cursor = conn.cursor()

        try:
            # 1. Setup the database
            cursor.executescript(level.setup_sql)
            conn.commit()

            # 2. Run the solution query to get expected results
            try:
                cursor.execute(level.solution_sql)
                expected_rows = cursor.fetchall()
                expected_cols = [description[0] for description in cursor.description]
            except sqlite3.Error as e:
                return {"success": False, "error": f"Error in solution query (internal error): {e}"}

            # 3. Run the user's query
            try:
                cursor.execute(user_sql)
                user_rows = cursor.fetchall()
                if cursor.description:
                    user_cols = [description[0] for description in cursor.description]
                else:
                    user_cols = []
            except sqlite3.Error as e:
                return {"success": False, "error": f"SQL Error: {e}"}

            # 4. Compare results
            # Check row count
            if len(user_rows) != len(expected_rows):
                return {
                    "success": False,
                    "error": f"Row count mismatch. Expected {len(expected_rows)}, got {len(user_rows)}."
                }

            # Check column count
            if len(user_cols) != len(expected_cols):
                return {
                    "success": False,
                    "error": f"Column count mismatch. Expected {len(expected_cols)} columns, got {len(user_cols)}."
                }

            # Check content (order matters if the level requires ordering, otherwise we might sort)
            # For simplicity, we assume order matters if ORDER BY is likely involved,
            # but strict comparison is usually best for games.
            if user_rows != expected_rows:
                return {
                    "success": False,
                    "error": "Result mismatch. The data returned does not match the expected output."
                }

            return {
                "success": True,
                "rows": user_rows,
                "columns": user_cols
            }

        except Exception as e:
            return {"success": False, "error": f"Unexpected error: {e}"}
        finally:
            conn.close()

class SqlGameGenerator:
    """
    Generates levels for the SQL Game.
    """
    def generate_levels(self) -> List[SqlGameLevel]:
        return [
            SqlGameLevel(
                name="Level 1: The SELECT Statement",
                description="Select all columns from the `employees` table.",
                setup_sql="""
                    CREATE TABLE employees (id INTEGER PRIMARY KEY, name TEXT, role TEXT, salary INTEGER);
                    INSERT INTO employees VALUES (1, 'Alice', 'Engineer', 70000);
                    INSERT INTO employees VALUES (2, 'Bob', 'Manager', 90000);
                    INSERT INTO employees VALUES (3, 'Charlie', 'Intern', 30000);
                """,
                solution_sql="SELECT * FROM employees;",
                hint="Use `SELECT *` to retrieve all columns."
            ),
            SqlGameLevel(
                name="Level 2: Specific Columns",
                description="Select only the `name` and `role` of all employees.",
                setup_sql="""
                    CREATE TABLE employees (id INTEGER PRIMARY KEY, name TEXT, role TEXT, salary INTEGER);
                    INSERT INTO employees VALUES (1, 'Alice', 'Engineer', 70000);
                    INSERT INTO employees VALUES (2, 'Bob', 'Manager', 90000);
                    INSERT INTO employees VALUES (3, 'Charlie', 'Intern', 30000);
                """,
                solution_sql="SELECT name, role FROM employees;",
                hint="Specify the column names separated by commas after SELECT."
            ),
            SqlGameLevel(
                name="Level 3: Filtering with WHERE",
                description="Select all employees who are 'Engineer's.",
                setup_sql="""
                    CREATE TABLE employees (id INTEGER PRIMARY KEY, name TEXT, role TEXT, salary INTEGER);
                    INSERT INTO employees VALUES (1, 'Alice', 'Engineer', 70000);
                    INSERT INTO employees VALUES (2, 'Bob', 'Manager', 90000);
                    INSERT INTO employees VALUES (3, 'Charlie', 'Intern', 30000);
                    INSERT INTO employees VALUES (4, 'David', 'Engineer', 72000);
                """,
                solution_sql="SELECT * FROM employees WHERE role = 'Engineer';",
                hint="Use the `WHERE` clause to filter rows based on a condition."
            ),
            SqlGameLevel(
                name="Level 4: Ordering Results",
                description="Select all employees ordered by `salary` in descending order.",
                setup_sql="""
                    CREATE TABLE employees (id INTEGER PRIMARY KEY, name TEXT, role TEXT, salary INTEGER);
                    INSERT INTO employees VALUES (1, 'Alice', 'Engineer', 70000);
                    INSERT INTO employees VALUES (2, 'Bob', 'Manager', 90000);
                    INSERT INTO employees VALUES (3, 'Charlie', 'Intern', 30000);
                    INSERT INTO employees VALUES (4, 'David', 'Engineer', 72000);
                """,
                solution_sql="SELECT * FROM employees ORDER BY salary DESC;",
                hint="Use `ORDER BY` followed by the column name and `DESC` for descending."
            ),
            SqlGameLevel(
                name="Level 5: Aggregation (COUNT)",
                description="Count the total number of employees.",
                setup_sql="""
                    CREATE TABLE employees (id INTEGER PRIMARY KEY, name TEXT, role TEXT, salary INTEGER);
                    INSERT INTO employees VALUES (1, 'Alice', 'Engineer', 70000);
                    INSERT INTO employees VALUES (2, 'Bob', 'Manager', 90000);
                    INSERT INTO employees VALUES (3, 'Charlie', 'Intern', 30000);
                """,
                solution_sql="SELECT COUNT(*) FROM employees;",
                hint="Use the `COUNT()` aggregate function."
            ),
            SqlGameLevel(
                name="Level 6: Simple JOIN",
                description="Select employee `name` and their `department_name`. Join `employees` and `departments` on `dept_id`.",
                setup_sql="""
                    CREATE TABLE departments (id INTEGER PRIMARY KEY, department_name TEXT);
                    INSERT INTO departments VALUES (101, 'Engineering');
                    INSERT INTO departments VALUES (102, 'HR');

                    CREATE TABLE employees (id INTEGER PRIMARY KEY, name TEXT, dept_id INTEGER);
                    INSERT INTO employees VALUES (1, 'Alice', 101);
                    INSERT INTO employees VALUES (2, 'Bob', 102);
                    INSERT INTO employees VALUES (3, 'Charlie', 101);
                """,
                solution_sql="SELECT employees.name, departments.department_name FROM employees JOIN departments ON employees.dept_id = departments.id;",
                hint="Use `JOIN` (or `INNER JOIN`) and specify the matching condition with `ON`."
            )
        ]

class SqlGameLabManager:
    """Helper for AI interactions in the SQL Game."""
    async def get_ai_hint(self, description: str, setup_sql: str, project_dir: Path, agent_type: str = "gemini", model: Optional[str] = None) -> str:
        prompt = f"""
I am playing a SQL game and I am stuck.
Goal: {description}
Database Schema (Setup SQL):
{setup_sql}

Give me a hint about what SQL concepts or constructs I should use to solve this.
Do NOT give me the exact SQL query. Keep it brief and helpful.
"""
        # Capture stdout because run_ask_logic prints to stdout
        output_capture = io.StringIO()
        try:
            with contextlib.redirect_stdout(output_capture):
                await run_ask_logic(
                    query=prompt,
                    project_dir=project_dir,
                    agent_type=agent_type,
                    model=model,
                    verbose=False
                )
            return output_capture.getvalue()
        except Exception as e:
            return f"Error getting hint: {e}"

async def run_sql_game_cli(project_dir: Path, agent_type: str = "gemini", model: Optional[str] = None):
    """
    Runs the interactive SQL Game in the CLI.
    """
    generator = SqlGameGenerator()
    engine = SqlGameEngine()
    manager = SqlGameLabManager()
    levels = generator.generate_levels()

    print("\n🎮 Welcome to the SQL Learning Game! 🎮\n")
    print("Commands:")
    print("  <sql query> : Execute a query (e.g., SELECT * FROM ...)")
    print("  hint        : Get an AI hint")
    print("  schema      : Show the setup SQL")
    print("  skip        : Skip to next level")
    print("  quit        : Exit game\n")

    for i, level in enumerate(levels):
        title = f"Level {i+1}: {level.name}"
        if HAS_RICH and console:
            console.rule(f"[bold cyan]{title}[/bold cyan]")
            console.print(f"[italic]{level.description}[/italic]\n")
        else:
            print(f"--- {title} ---")
            print(f"Goal: {level.description}")
            print("-" * 30)

        while True:
            try:
                # Basic multi-line input handling
                # We'll treat a line ending with ';' as the end of the query
                # or just take single line for simplicity first version
                user_input = input("\nSQL > ").strip()
                while user_input and not user_input.endswith(';') and user_input.lower() not in ['quit', 'skip', 'hint', 'schema']:
                     # Continuation
                     line = input("... ").strip()
                     if line:
                         user_input += " " + line
                     else:
                         break
            except (EOFError, KeyboardInterrupt):
                print("\nExiting game.")
                return

            if not user_input:
                continue

            cmd = user_input.lower().strip().strip(';')

            if cmd == "quit":
                print("Thanks for playing!")
                return

            if cmd == "skip":
                print("Skipping level...")
                break

            if cmd == "schema":
                if HAS_RICH and console:
                    console.print(Syntax(level.setup_sql, "sql", theme="monokai", line_numbers=True))
                else:
                    print(level.setup_sql)
                continue

            if cmd == "hint":
                print("\nThinking... 🤖")
                hint = await manager.get_ai_hint(
                    level.description,
                    level.setup_sql,
                    project_dir,
                    agent_type,
                    model
                )
                if HAS_RICH and console:
                    console.print(Panel(hint, title="AI Hint", border_style="yellow"))
                else:
                    print(f"\n--- Hint ---\n{hint}\n------------")
                continue

            # Validate
            result = engine.validate(user_input, level)

            if result["success"]:
                if HAS_RICH and console and "rows" in result:
                    table = Table(show_header=True, header_style="bold green")
                    for col in result["columns"]:
                        table.add_column(col)
                    for row in result["rows"]:
                        table.add_row(*[str(cell) for cell in row])
                    console.print(table)
                elif "rows" in result:
                    print("Results:")
                    for row in result["rows"]:
                        print(row)

                print("\n🎉 Level Cleared! 🎉")
                break
            else:
                print(f"❌ {result['error']}")
                print("Try again.")

    print("\n🏆 Congratulations! You have completed all levels! 🏆")
