import json
import csv
import random
import uuid
import datetime
import string
import io


class MockDataGenerator:
    """
    Generates mock data based on a provided schema using only standard library.
    Supported types: int, float, boolean, string, uuid, date, datetime, email, name, choice.
    """
    def __init__(self, schema):
        self.schema = schema

    def generate(self, count=1):
        """Generates a list of records based on schema."""
        data = [self._generate_record() for _ in range(count)]
        return data

    def _generate_record(self):
        record = {}
        for field, spec in self.schema.items():
            record[field] = self._generate_value(spec)
        return record

    def _generate_value(self, spec):
        # Normalize spec
        if isinstance(spec, str):
            spec_type = spec
            options = {}
        elif isinstance(spec, dict):
            spec_type = spec.get("type", "string")
            options = spec
        else:
            spec_type = "string"
            options = {}

        if spec_type == "int" or spec_type == "integer":
            return random.randint(options.get("min", 0), options.get("max", 100))  # nosec B311

        elif spec_type == "float" or spec_type == "number":
            return random.uniform(options.get("min", 0.0), options.get("max", 100.0))  # nosec B311

        elif spec_type == "boolean" or spec_type == "bool":
            return random.choice([True, False])  # nosec B311

        elif spec_type == "uuid":
            return str(uuid.uuid4())

        elif spec_type == "date":
            start_date = datetime.date(2020, 1, 1)
            end_date = datetime.date.today()
            days_between = (end_date - start_date).days
            random_days = random.randrange(days_between + 1)  # nosec B311
            return (start_date + datetime.timedelta(days=random_days)).isoformat()

        elif spec_type == "datetime":
            start_date = datetime.datetime(2020, 1, 1)
            end_date = datetime.datetime.now()
            time_between = end_date - start_date
            random_seconds = random.randrange(int(time_between.total_seconds()))  # nosec B311
            return (start_date + datetime.timedelta(seconds=random_seconds)).isoformat()

        elif spec_type == "email":
            user = self._random_string(random.randint(5, 10))  # nosec B311
            domain = random.choice(["example.com", "test.org", "mock.net", "corp.co"])  # nosec B311
            return f"{user}@{domain}"

        elif spec_type == "name":
            first_names = ["Alice", "Bob", "Charlie", "David", "Eve", "Frank", "Grace", "Heidi"]
            last_names = ["Smith", "Johnson", "Williams", "Jones", "Brown", "Davis", "Miller", "Wilson"]
            return f"{random.choice(first_names)} {random.choice(last_names)}"  # nosec B311

        elif spec_type == "choice":
            choices = options.get("choices", [])
            return random.choice(choices) if choices else None  # nosec B311

        elif spec_type == "credit_card":
            return self._generate_credit_card()

        elif spec_type == "string":
            length = options.get("length", 10)
            return self._random_string(length)

        else:
            # Fallback
            return self._random_string(10)

    def _generate_credit_card(self):
        # Start with a Visa prefix (4) and generate 14 random digits
        prefix = "4"
        partial_cc = prefix + "".join([str(random.randint(0, 9)) for _ in range(14)])  # nosec B311

        # Calculate Luhn check digit
        total = 0
        for i, digit in enumerate(reversed(partial_cc)):
            n = int(digit)
            if i % 2 == 0:
                n *= 2
                if n > 9:
                    n -= 9
            total += n

        check_digit = (10 - (total % 10)) % 10
        return partial_cc + str(check_digit)

    def _random_string(self, length):
        letters = string.ascii_lowercase
        return ''.join(random.choice(letters) for i in range(length))  # nosec B311

    def export(self, data, format="json", table_name="mock_data"):
        """Exports data to the specified format."""
        if format == "json":
            return json.dumps(data, indent=2)

        elif format == "csv":
            if not data:
                return ""
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
            return output.getvalue()

        elif format == "sql":
            if not data:
                return ""

            # Basic validation for table name to prevent trivial injection
            if not table_name.isidentifier():
                raise ValueError("Invalid table name")

            statements = []
            for row in data:
                # Validate column names
                for col in row.keys():
                    if not col.isidentifier():
                        raise ValueError(f"Invalid column name: {col}")

                columns = ", ".join(row.keys())
                values = []
                for v in row.values():
                    if isinstance(v, (int, float)):
                        values.append(str(v))
                    elif isinstance(v, bool):
                        values.append("TRUE" if v else "FALSE")
                    elif v is None:
                        values.append("NULL")
                    else:
                        # Basic escaping for single quotes
                        escaped_val = str(v).replace("'", "''")
                        values.append(f"'{escaped_val}'")

                values_str = ", ".join(values)
                statements.append(f"INSERT INTO {table_name} ({columns}) VALUES ({values_str});")  # nosec B608
            return "\n".join(statements)

        else:
            raise ValueError(f"Unsupported format: {format}")
