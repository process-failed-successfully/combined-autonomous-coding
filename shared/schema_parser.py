import re
from typing import Dict, Any


class SchemaParser:
    """Parses SQL schema (SQLite) into a structured format and generates diagrams."""

    def parse(self, schema_text: str) -> Dict[str, Any]:
        """
        Parses CREATE TABLE statements.
        Returns: {'tables': [{'name': str, 'columns': list, 'fks': list}]}
        """
        tables = []
        # Regex to match CREATE TABLE statements
        # Matches: CREATE TABLE [IF NOT EXISTS] table_name ( ... );
        # We need to capture the table name and the content inside parentheses
        # Note: This is a simplified parser and might not handle all edge cases (nested parens in types, etc.)
        table_pattern = re.compile(
            r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?["`]?(\w+)["`]?\s*\((.*?)\);',
            re.IGNORECASE | re.DOTALL
        )

        for match in table_pattern.finditer(schema_text):
            table_name = match.group(1)

            # Skip internal tables
            if table_name.startswith("sqlite_"):
                continue

            body = match.group(2)
            columns = []
            fks = []

            # Clean body: remove comments
            body = re.sub(r'--.*', '', body)

            # Simple splitting by comma is risky if types contain commas (e.g. DECIMAL(5,2))
            # We'll split by newline first as that's common formatting
            lines = [line.strip() for line in body.split('\n')]

            # If multiple definitions on one line, we might miss them.
            # But get_schema_info usually returns formatted SQL from sqlite_master.

            for line in lines:
                line = line.strip().rstrip(',')
                if not line:
                    continue

                # Check for explicit FOREIGN KEY line constraint
                # FOREIGN KEY (col) REFERENCES table(col)
                fk_match = re.match(r'FOREIGN\s+KEY\s*\((["`]?\w+["`]?)\)\s*REFERENCES\s+["`]?(\w+)["`]?\s*\((["`]?\w+["`]?)\)', line, re.IGNORECASE)
                if fk_match:
                    fks.append({
                        "from_col": fk_match.group(1).strip('"').strip('`'),
                        "to_table": fk_match.group(2).strip('"').strip('`'),
                        "to_col": fk_match.group(3).strip('"').strip('`')
                    })
                    continue

                # Check for PRIMARY KEY line constraint
                if line.upper().startswith("PRIMARY KEY") or line.upper().startswith("CONSTRAINT"):
                    # We skip complex constraints parsing for now unless it's FK
                    if "FOREIGN KEY" in line.upper():
                        # Try to parse constraint line with FK
                        fk_match = re.search(r'FOREIGN\s+KEY\s*\((["`]?\w+["`]?)\)\s*REFERENCES\s+["`]?(\w+)["`]?\s*\((["`]?\w+["`]?)\)', line, re.IGNORECASE)
                        if fk_match:
                            fks.append({
                                "from_col": fk_match.group(1).strip('"').strip('`'),
                                "to_table": fk_match.group(2).strip('"').strip('`'),
                                "to_col": fk_match.group(3).strip('"').strip('`')
                            })
                    continue

                # Column definition
                # col_name TYPE [constraints]
                parts = line.split(maxsplit=1)
                col_name = parts[0].strip('"').strip('`')

                # Skip if it looks like a constraint keyword
                if col_name.upper() in ["UNIQUE", "CHECK", "INDEX"]:
                    continue

                col_type = "UNKNOWN"
                if len(parts) > 1:
                    # Type is usually the first word of the rest, but might have parens
                    rest = parts[1]
                    type_match = re.match(r'^(\w+(\(.*\))?)', rest)
                    if type_match:
                        col_type = type_match.group(1)

                # Inline FK check: REFERENCES table(col)
                ref_match = re.search(r'REFERENCES\s+["`]?(\w+)["`]?\s*\((["`]?\w+["`]?)\)', line, re.IGNORECASE)
                if ref_match:
                    fks.append({
                        "from_col": col_name,
                        "to_table": ref_match.group(1).strip('"').strip('`'),
                        "to_col": ref_match.group(2).strip('"').strip('`')
                    })

                columns.append({"name": col_name, "type": col_type})

            tables.append({
                "name": table_name,
                "columns": columns,
                "fks": fks
            })

        return {"tables": tables}

    def generate_mermaid(self, schema: Dict[str, Any]) -> str:
        """Generates a Mermaid ER diagram definition."""
        lines = ["erDiagram"]
        for table in schema["tables"]:
            t_name = table["name"]
            lines.append(f"    {t_name} {{")
            for col in table["columns"]:
                # Sanitize type for mermaid (remove spaces or parens if needed?)
                # Mermaid supports: type name
                c_type = col['type'].replace(" ", "_")
                lines.append(f"        {c_type} {col['name']}")
            lines.append("    }")

            for fk in table["fks"]:
                # Relationship: table }|..|| other_table : "fk"
                # Using 0..N relationship symbol generically for now
                lines.append(f"    {t_name} }}|..|| {fk['to_table']} : \"{fk['from_col']}->{fk['to_col']}\"")

        return "\n".join(lines)
