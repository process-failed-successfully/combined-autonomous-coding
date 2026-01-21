import json
import random
import csv
import io
import datetime
import uuid
from typing import List, Dict, Any
from pathlib import Path


class MockDataGenerator:
    """Generates mock data based on a JSON specification."""

    def __init__(self):
        self.seq_counters = {}
        # Simple built-in datasets to avoid external deps for now
        self.names = ["Alice", "Bob", "Charlie", "David", "Eve", "Frank", "Grace", "Heidi", "Ivan", "Judy", "Mallory", "Niaj", "Oscar", "Peggy", "Sybil", "Trent", "Victor", "Walter"]
        self.surnames = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson"]
        self.domains = ["example.com", "test.org", "mock.net", "local.dev"]

    def generate(self, spec: Dict[str, str], count: int) -> List[Dict[str, Any]]:
        """Generates a list of records based on the spec."""
        results = []
        for _ in range(count):
            record = {}
            for field, type_def in spec.items():
                record[field] = self._generate_value(field, type_def)
            results.append(record)
        return results

    def _generate_value(self, field_name: str, type_def: str) -> Any:
        # Handle "choice:[a,b,c]"
        if type_def.startswith("choice:"):
            options_str = type_def[len("choice:"):]
            # simple parser for [a,b,c]
            options_str = options_str.strip("[]")
            options = [o.strip() for o in options_str.split(",")]
            return random.choice(options)  # nosec

        parts = type_def.split(":")
        base_type = parts[0]
        args = parts[1:] if len(parts) > 1 else []

        if base_type in ["int", "integer"]:
            return self._gen_int(field_name, args)
        elif base_type in ["float", "double"]:
            return self._gen_float(args)
        elif base_type in ["str", "string"]:
            return self._gen_string(args)
        elif base_type in ["bool", "boolean"]:
            return random.choice([True, False])  # nosec
        elif base_type == "date":
            return self._gen_date(args)
        elif base_type == "uuid":
            return str(uuid.uuid4())
        else:
            return f"UnknownType({type_def})"

    def _gen_int(self, field_name: str, args: List[str]) -> int:
        if not args:
            return random.randint(0, 100)  # nosec

        mode = args[0]
        if mode == "seq":
            start = int(args[1]) if len(args) > 1 else 1
            if field_name not in self.seq_counters:
                self.seq_counters[field_name] = start
            val = self.seq_counters[field_name]
            self.seq_counters[field_name] += 1
            return val

        # Range: 18-90
        if "-" in mode:
            try:
                min_val, max_val = map(int, mode.split("-"))
                return random.randint(min_val, max_val)  # nosec
            except ValueError:
                pass

        return random.randint(0, 100)  # nosec

    def _gen_float(self, args: List[str]) -> float:
        min_val, max_val = 0.0, 100.0
        precision = 2

        if args:
            range_str = args[0]
            if "-" in range_str:
                try:
                    min_val, max_val = map(float, range_str.split("-"))
                except ValueError:
                    pass
            if len(args) > 1:
                try:
                    precision = int(args[1])
                except ValueError:
                    pass

        val = random.uniform(min_val, max_val)  # nosec
        return round(val, precision)

    def _gen_string(self, args: List[str]) -> str:
        if not args:
            return self._random_word()

        mode = args[0]
        if mode == "name":
            return f"{random.choice(self.names)} {random.choice(self.surnames)}"  # nosec
        elif mode == "email":
            name = random.choice(self.names).lower()  # nosec
            surname = random.choice(self.surnames).lower()  # nosec
            domain = random.choice(self.domains)  # nosec
            return f"{name}.{surname}@{domain}"
        elif mode == "uuid":
            return str(uuid.uuid4())
        elif mode == "alpha":
            length = int(args[1]) if len(args) > 1 else 10
            chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
            return "".join(random.choice(chars) for _ in range(length))  # nosec

        return self._random_word()

    def _random_word(self) -> str:
        words = ["lorem", "ipsum", "dolor", "sit", "amet", "consectetur", "adipiscing", "elit"]
        return random.choice(words)  # nosec

    def _gen_date(self, args: List[str]) -> str:
        if not args or args[0] == "now":
            return datetime.datetime.now().isoformat()

        if "-" in args[0]:  # Start-End year? Or full date?
            # Supporting YYYY-MM-DD:YYYY-MM-DD
            parts = args[0].split(":")  # Split range by : if possible, else - is confusing with date separator
            if len(parts) == 2:
                try:
                    start_date = datetime.datetime.strptime(parts[0], "%Y-%m-%d")
                    end_date = datetime.datetime.strptime(parts[1], "%Y-%m-%d")
                    delta = end_date - start_date
                    random_days = random.randrange(delta.days + 1)  # nosec
                    return (start_date + datetime.timedelta(days=random_days)).date().isoformat()
                except ValueError:
                    pass
        return datetime.datetime.now().date().isoformat()


def format_json(data: List[Dict[str, Any]]) -> str:
    return json.dumps(data, indent=2)


def format_csv(data: List[Dict[str, Any]]) -> str:
    if not data:
        return ""
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=data[0].keys())
    writer.writeheader()
    writer.writerows(data)
    return output.getvalue()


def format_sql(data: List[Dict[str, Any]], table_name: str) -> str:
    if not data:
        return ""

    if not table_name.isidentifier():
        raise ValueError(f"Invalid table name: {table_name}")

    statements = []
    for record in data:
        columns = ", ".join(record.keys())
        values = []
        for v in record.values():
            if isinstance(v, str):
                safe_v = v.replace("'", "''")
                values.append(f"'{safe_v}'")
            elif isinstance(v, bool):
                values.append("TRUE" if v else "FALSE")
            elif v is None:
                values.append("NULL")
            else:
                values.append(str(v))
        values_str = ", ".join(values)
        statements.append(f"INSERT INTO {table_name} ({columns}) VALUES ({values_str});")  # nosec

    return "\n".join(statements)


def run_mock_logic(
    spec_path: Path,
    count: int = 10,
    output_format: str = "json",
    output_file: Path = None,
    table_name: str = "table"
) -> bool:
    try:
        spec_content = spec_path.read_text()
        spec = json.loads(spec_content)
    except Exception as e:
        print(f"Error reading spec file: {e}")
        return False

    generator = MockDataGenerator()
    data = generator.generate(spec, count)

    if output_format == "json":
        result = format_json(data)
    elif output_format == "csv":
        result = format_csv(data)
    elif output_format == "sql":
        result = format_sql(data, table_name)
    else:
        print(f"Unknown format: {output_format}")
        return False

    if output_file:
        try:
            output_file.write_text(result, encoding="utf-8")
            print(f"✅ Generated {count} records to {output_file}")
        except Exception as e:
            print(f"Error writing output file: {e}")
            return False
    else:
        print(result)

    return True
