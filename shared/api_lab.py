import yaml
import json
import requests
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

class ApiLabManager:
    """
    Manages API Lab state, including loading specs and executing requests.
    """

    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.spec_data: Dict[str, Any] = {}
        self.history: List[Dict[str, Any]] = []
        self.session = requests.Session()

    def load_spec(self, path: Optional[Path] = None) -> bool:
        """
        Loads an OpenAPI specification from a file.
        If no path is provided, looks for 'openapi.yaml' or 'openapi.json' in the project root.
        """
        if path:
            target_path = path
        else:
            # Try default locations
            yaml_path = self.project_dir / "openapi.yaml"
            json_path = self.project_dir / "openapi.json"
            if yaml_path.exists():
                target_path = yaml_path
            elif json_path.exists():
                target_path = json_path
            else:
                return False

        try:
            with open(target_path, 'r') as f:
                if target_path.suffix == '.json':
                    self.spec_data = json.load(f)
                else:
                    self.spec_data = yaml.safe_load(f)
            return True
        except Exception as e:
            print(f"Error loading spec: {e}")
            return False

    def list_endpoints(self) -> List[Dict[str, str]]:
        """
        Returns a list of available endpoints from the loaded spec.
        """
        endpoints = []
        if not self.spec_data or 'paths' not in self.spec_data:
            return endpoints

        for path, methods in self.spec_data['paths'].items():
            for method, details in methods.items():
                if method.lower() in ['get', 'post', 'put', 'delete', 'patch', 'options', 'head']:
                    endpoints.append({
                        'method': method.upper(),
                        'path': path,
                        'summary': details.get('summary', '')
                    })
        return endpoints

    def get_server_url(self) -> str:
        """
        Attempts to determine the base URL from the spec.
        """
        if not self.spec_data:
            return "http://localhost:8000"

        if 'servers' in self.spec_data and self.spec_data['servers']:
            return self.spec_data['servers'][0].get('url', "http://localhost:8000")

        return "http://localhost:8000"

    def fuzz_endpoint(self, method: str, path: str) -> List[Dict[str, Any]]:
        """
        Fuzzes a specific endpoint.
        """
        from shared.api_fuzzer import APIFuzzer
        fuzzer = APIFuzzer(self)

        # Resolve full URL
        base = self.get_server_url()
        if path.startswith("http"):
            full_url = path
            # Try to infer relative path for schema lookup?
            # For now, if full url is passed, schema lookup might fail if we don't reverse match.
            # We'll rely on fuzzing without schema or user providing relative path.
        else:
            full_url = base.rstrip('/') + "/" + path.lstrip('/')

        # Find schema
        schema = {}
        if self.spec_data and 'paths' in self.spec_data:
            if path in self.spec_data['paths']:
                path_item = self.spec_data['paths'][path]
                if method.lower() in path_item:
                    schema = path_item[method.lower()]

        return fuzzer.fuzz_endpoint(method, full_url, schema)

    def execute_request(self, method: str, url: str, headers: Dict[str, str] = None, params: Dict[str, str] = None, body: str = None) -> Dict[str, Any]:
        """
        Executes an HTTP request.
        """
        try:
            # Parse body if it looks like JSON
            json_body = None
            data_body = None

            if body:
                try:
                    json_body = json.loads(body)
                except json.JSONDecodeError:
                    data_body = body

            response = self.session.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json=json_body,
                data=data_body,
                timeout=10
            )

            result = {
                'status_code': response.status_code,
                'headers': dict(response.headers),
                'body': response.text,
                'success': response.ok
            }

            # Try to format JSON body for display
            try:
                if result['body']:
                    parsed = response.json()
                    result['body'] = json.dumps(parsed, indent=2)
            except ValueError:
                pass

            self.history.append({
                'method': method,
                'url': url,
                'status': response.status_code
            })

            return result

        except requests.RequestException as e:
            return {
                'status_code': 0,
                'headers': {},
                'body': f"Request Error: {str(e)}",
                'success': False
            }

def run_api_lab_cli(args):
    """
    CLI entry point for API Lab.
    """
    project_dir = args.project_dir.resolve()
    manager = ApiLabManager(project_dir)

    # Attempt to load spec
    if not manager.load_spec():
        print(f"Warning: No openapi.yaml or openapi.json found in {project_dir}")
        print("Functionality may be limited.")

    if args.action == "list":
        endpoints = manager.list_endpoints()
        if not endpoints:
            print("No endpoints found in spec.")
            sys.exit(0)

        print(f"--- API Endpoints ({len(endpoints)}) ---")
        # Calc max method length for padding
        max_method = max(len(e['method']) for e in endpoints)
        for e in endpoints:
            method = e['method'].ljust(max_method)
            path = e['path']
            summary = f" - {e['summary']}" if e['summary'] else ""
            print(f"{method} {path}{summary}")
        sys.exit(0)

    elif args.action == "run":
        method = args.method.upper()
        url = args.url
        body = args.body

        headers = {}
        if args.headers:
            try:
                headers = json.loads(args.headers)
            except json.JSONDecodeError:
                print("Error: Invalid JSON format for --headers", file=sys.stderr)
                sys.exit(1)

        # If URL is relative, prepend base URL from spec
        if not url.startswith("http"):
            base = manager.get_server_url()
            # Handle slashes
            if base.endswith("/") and url.startswith("/"):
                url = base + url[1:]
            elif not base.endswith("/") and not url.startswith("/"):
                url = base + "/" + url
            else:
                url = base + url
            print(f"Resolved URL: {url}")

        print(f"Executing {method} {url}...")
        result = manager.execute_request(method, url, headers=headers, body=body)

        status_code = result['status_code']
        status_marker = "✅" if result['success'] else "❌"

        print(f"\n--- Response ({status_marker} {status_code}) ---")
        print("Headers:")
        for k, v in result['headers'].items():
            print(f"  {k}: {v}")

        print("\nBody:")
        print(result['body'])

        sys.exit(0 if result['success'] else 1)

    elif args.action == "fuzz":
        method = args.method.upper()
        path = args.url # Argument name is url, but for fuzz we prefer path key

        results = manager.fuzz_endpoint(method, path)

        crashes = [r for r in results if r['crash']]
        print(f"\n--- Fuzzing Complete ---")
        print(f"Total Requests: {len(results)}")
        print(f"Crashes (5xx): {len(crashes)}")

        if crashes:
            print("\n❌ CRASHES DETECTED:")
            for c in crashes:
                print(f"  Payload: {c['payload']}")
                print(f"  Status: {c['status']}")
                print(f"  Error: {c.get('error', '')}")
            sys.exit(1)
        else:
            print("\n✅ No crashes detected.")
            sys.exit(0)

    else:
        print(f"Unknown action: {args.action}", file=sys.stderr)
        sys.exit(1)
