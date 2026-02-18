import requests
import yaml
import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from rich.console import Console
from rich.table import Table
from shared.schema_lab import SchemaLabManager

class ContractVerifier:
    """
    Verifies that a running service adheres to its OpenAPI specification.
    """

    def __init__(self, project_dir: Optional[Path] = None):
        self.project_dir = project_dir or Path(".")
        self.schema_manager = SchemaLabManager(self.project_dir)
        self.console = Console()
        self.session = requests.Session()

    def load_spec(self, spec_path: Path) -> Dict[str, Any]:
        """Loads OpenAPI spec from file."""
        if not spec_path.exists():
            raise FileNotFoundError(f"Spec file not found: {spec_path}")

        try:
            with open(spec_path, 'r', encoding='utf-8') as f:
                if spec_path.suffix in ['.yaml', '.yml']:
                    return yaml.safe_load(f)
                else:
                    return json.load(f)
        except Exception as e:
            raise ValueError(f"Error loading spec: {e}")

    def generate_valid_payload(self, schema: Dict[str, Any]) -> Any:
        """
        Generates a basic valid payload for the given schema.
        This is a simplified version of APIFuzzer's generator, focused on correctness.
        """
        if not schema:
            return {}

        # Handle references (basic support)
        # Note: Proper resolution requires full spec access, which we pass if needed.
        # For now, we assume dereferenced or simple schemas.
        # If we encounter $ref, we might fail or need to resolve.
        # Let's handle simple types.

        t = schema.get("type")

        if "enum" in schema:
            return schema["enum"][0]

        if "default" in schema:
            return schema["default"]

        if t == "object":
            obj = {}
            props = schema.get("properties", {})
            required = schema.get("required", [])
            for k, v in props.items():
                # Only generate required fields to keep it minimal but valid
                if k in required:
                    obj[k] = self.generate_valid_payload(v)
            return obj
        elif t == "array":
            items = schema.get("items", {})
            # Generate one item
            return [self.generate_valid_payload(items)]
        elif t == "string":
            fmt = schema.get("format")
            if fmt == "uuid":
                return "123e4567-e89b-12d3-a456-426614174000"
            elif fmt == "email":
                return "user@example.com"
            elif fmt == "date":
                return "2023-01-01"
            elif fmt == "date-time":
                return "2023-01-01T12:00:00Z"
            return "string"
        elif t == "integer":
            return 1
        elif t == "number":
            return 1.0
        elif t == "boolean":
            return True
        elif t == "null":
            return None

        return None

    def verify_endpoint(self, method: str, url: str, operation: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sends a request and verifies the response against the operation spec.
        """
        result = {
            "method": method,
            "url": url,
            "status": "pass",
            "errors": [],
            "status_code": 0
        }

        # Prepare request
        headers = {"User-Agent": "ContractVerifier/1.0", "Accept": "application/json"}
        json_body = None

        # Check for requestBody
        req_body = operation.get("requestBody", {})
        content = req_body.get("content", {})
        if "application/json" in content:
            schema = content["application/json"].get("schema", {})
            json_body = self.generate_valid_payload(schema)
            headers["Content-Type"] = "application/json"

        try:
            response = self.session.request(method, url, headers=headers, json=json_body, timeout=5)
            result["status_code"] = response.status_code

            # Validate Status Code
            responses_spec = operation.get("responses", {})
            str_code = str(response.status_code)

            # Find matching response spec (exact code or 'default')
            response_spec = responses_spec.get(str_code) or responses_spec.get("default")

            if not response_spec:
                result["status"] = "fail"
                result["errors"].append(f"Undocumented status code: {str_code}")
                return result

            # Validate Body
            content_spec = response_spec.get("content", {})
            if "application/json" in content_spec:
                schema = content_spec["application/json"].get("schema", {})
                try:
                    body_data = response.json()
                    valid, msg = self.schema_manager.validate_instance(body_data, schema)
                    if not valid:
                        result["status"] = "fail"
                        result["errors"].append(f"Schema Validation Failed: {msg}")
                except json.JSONDecodeError:
                    # Only fail if schema expected JSON
                    if response.text.strip():
                        result["status"] = "fail"
                        result["errors"].append("Invalid JSON body received")

        except requests.RequestException as e:
            result["status"] = "error"
            result["errors"].append(str(e))

        return result

    def run_verification(self, spec_path: Path, target_url: str):
        """
        Main loop to verify all endpoints.
        """
        try:
            spec = self.load_spec(spec_path)
        except Exception as e:
            self.console.print(f"[bold red]Error loading spec:[/bold red] {e}")
            return

        # Prepare server URL
        # We override spec servers with target_url
        base_url = target_url.rstrip('/')

        paths = spec.get("paths", {})
        total = 0
        passed = 0
        failed = 0

        table = Table(title=f"Contract Verification: {spec.get('info', {}).get('title', 'API')}")
        table.add_column("Method", style="cyan")
        table.add_column("Path", style="magenta")
        table.add_column("Status", justify="center")
        table.add_column("Details")

        for path, methods in paths.items():
            for method, operation in methods.items():
                if method.lower() not in ['get', 'post', 'put', 'delete', 'patch']:
                    continue

                # Only verify GET for safety by default?
                # Or verify all but warn?
                # Let's verify all since we generated 'valid' payloads.
                # Ideally, we should only verify 'safe' methods or require a --unsafe flag.
                # For this MVP, let's stick to GET unless it's a dry run?
                # No, contract testing needs to test POST too.
                # We assume the user is targeting a test environment.

                # Construct URL
                # Handle path parameters (e.g. /users/{id})
                # We need to substitute them.
                full_url = base_url + path
                if "{" in path:
                    # Simple substitution with dummy values based on param definition
                    # This requires parsing 'parameters' list in operation or path
                    params = operation.get("parameters", []) + methods.get("parameters", [])
                    for param in params:
                        if param.get("in") == "path":
                            name = param["name"]
                            # Guess value based on type or name
                            val = "1"
                            if "id" in name.lower() and "uuid" in str(param).lower():
                                val = "123e4567-e89b-12d3-a456-426614174000"
                            full_url = full_url.replace(f"{{{name}}}", str(val))

                res = self.verify_endpoint(method.upper(), full_url, operation)

                total += 1
                status_style = "green" if res["status"] == "pass" else "red"
                if res["status"] == "pass":
                    passed += 1
                    symbol = "✅"
                else:
                    failed += 1
                    symbol = "❌"

                details = ", ".join(res["errors"]) if res["errors"] else f"Status: {res['status_code']}"
                table.add_row(method.upper(), path, f"[{status_style}]{symbol}[/{status_style}]", details)

        self.console.print(table)
        self.console.print(f"\nSummary: {total} tests, [green]{passed} passed[/green], [red]{failed} failed[/red]")

        if failed > 0:
            sys.exit(1)

def run_contract_lab_logic(args):
    """CLI Entry point for Contract Lab."""
    verifier = ContractVerifier(args.project_dir)

    if args.action == "verify":
        spec_path = Path(args.spec)
        target_url = args.url
        verifier.run_verification(spec_path, target_url)
    else:
        print(f"Unknown action: {args.action}")
        sys.exit(1)
