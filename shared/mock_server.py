import http.server
import json
import yaml
import logging
from pathlib import Path
from typing import Optional, Dict, Any, cast
import asyncio

from shared.config import Config
from shared.mock_data import MockDataGenerator
from agents.gemini import GeminiAgent
from agents.cursor import CursorAgent
from agents.local import LocalAgent
from agents.openrouter import OpenRouterAgent

logger = logging.getLogger(__name__)


class MockRequestHandler(http.server.BaseHTTPRequestHandler):
    def __init__(self, *args, project_dir: Path, config: Dict[str, Any], agent_config: Config, **kwargs):
        self.project_dir = project_dir
        self.mock_config = config
        self.agent_config = agent_config
        super().__init__(*args, **kwargs)

    def do_GET(self):
        self.handle_request("GET")

    def do_POST(self):
        self.handle_request("POST")

    def do_PUT(self):
        self.handle_request("PUT")

    def do_DELETE(self):
        self.handle_request("DELETE")

    def do_PATCH(self):
        self.handle_request("PATCH")

    def handle_request(self, method: str):
        path = self.path.split('?')[0]

        # 1. Check for configured routes
        route_config = self._find_route(method, path)
        if route_config:
            self._handle_configured_route(route_config)
            return

        # 2. AI Fallback
        self._handle_ai_fallback(method, path)

    def _find_route(self, method: str, path: str) -> Optional[Dict[str, Any]]:
        routes = self.mock_config.get("routes", [])
        for route in routes:
            if route.get("path") == path and route.get("method", "GET").upper() == method:
                return route
        return None

    def _handle_configured_route(self, route: Dict[str, Any]):
        response_spec = route.get("response", {})
        status = response_spec.get("status", 200)

        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()

        response_body = {}

        # Static Response
        if "body" in response_spec:
            response_body = response_spec["body"]

        # Schema Generation
        elif "schema" in response_spec:
            schema_file = self.project_dir / response_spec["schema"]
            if schema_file.exists():
                try:
                    with open(schema_file, "r") as f:
                        schema = json.load(f)
                    generator = MockDataGenerator(schema)
                    # Generate one record or a list? Default to one record if not specified,
                    # but typically APIs return objects or lists.
                    # Let's assume schema describes the return object.
                    records = generator.generate(count=1)
                    response_body = records[0] if records else {}
                except Exception as e:
                    response_body = {"error": f"Failed to generate data from schema: {e}"}
            else:
                response_body = {"error": f"Schema file not found: {response_spec['schema']}"}

        self.wfile.write(json.dumps(response_body).encode("utf-8"))

    def _handle_ai_fallback(self, method: str, path: str):
        # Read body if present
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8') if content_length > 0 else ""

        logger.info(f"Delegating to AI Agent: {method} {path}")

        response_data = self._invoke_agent(method, path, self.headers, body)

        self.send_response(response_data.get("status", 200))
        self.send_header("Content-Type", "application/json")
        self.end_headers()

        self.wfile.write(json.dumps(response_data.get("body", {})).encode("utf-8"))

    def _invoke_agent(self, method: str, path: str, headers: Any, body: str) -> Dict[str, Any]:
        prompt = f"""
You are acting as a Mock API Server.
I have received an HTTP request that does not match any static configuration.
Your task is to generate a realistic JSON response based on the request details and the project context.

Request Details:
Method: {method}
Path: {path}
Headers: {dict(headers)}
Body: {body}

Instructions:
1. Analyze the request to understand what resource is being accessed or modified.
2. Generate a plausible JSON response body.
3. Determine the appropriate HTTP status code (e.g., 200, 201, 404, 400).
4. Return ONLY a JSON object with the following structure:
{{
  "status": <int>,
  "body": <json_object_or_array>
}}
Do not include any markdown formatting or explanations outside the JSON.
"""

        # Initialize Agent
        agent_class_map = {
            "gemini": GeminiAgent,
            "cursor": CursorAgent,
            "local": LocalAgent,
            "openrouter": OpenRouterAgent,
        }

        agent_type = self.agent_config.agent_type
        agent_class = agent_class_map.get(agent_type)

        if not agent_class:
            return {"status": 500, "body": {"error": f"Unknown agent type: {agent_type}"}}

        agent = cast(Any, agent_class)(self.agent_config)

        try:
            # We need to run the async agent method in a synchronous context
            # Since this is running in a thread, we can use asyncio.run
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            # Agent run returns (status, response, actions)
            # We assume response is the string we want.
            _, response_text, _ = loop.run_until_complete(agent.run_agent_session(prompt))
            loop.close()

            # Parse the response
            # Cleanup markdown code blocks if present
            cleaned_response = response_text.strip()
            if cleaned_response.startswith("```json"):
                cleaned_response = cleaned_response[7:]
            if cleaned_response.endswith("```"):
                cleaned_response = cleaned_response[:-3]

            return json.loads(cleaned_response.strip())

        except json.JSONDecodeError:
            logger.error(f"Failed to parse AI response: {response_text}")
            return {"status": 500, "body": {"error": "AI generated invalid JSON", "raw": response_text}}
        except Exception as e:
            logger.error(f"AI Agent error: {e}")
            return {"status": 500, "body": {"error": f"AI Agent error: {e}"}}


def run_mock_server(project_dir: Path, port: int = 8000, agent_type: str = "gemini", model: Optional[str] = None):
    """
    Starts the AI-powered mock server.
    """
    # Load Configuration
    mock_config: Dict[str, Any] = {}
    config_file = project_dir / "mock_config.yaml"
    if config_file.exists():
        try:
            with open(config_file, "r") as f:
                mock_config = yaml.safe_load(f) or {}
            print(f"✅ Loaded mock configuration from {config_file.name}")
        except Exception as e:
            print(f"❌ Error loading mock config: {e}")
            return

    # Prepare Agent Config
    agent_config = Config(
        project_dir=project_dir,
        agent_type=agent_type,
        model=model,
        max_iterations=1,
        stream_output=False,  # We don't want streaming to stdout mixed with server logs
        verbose=False
    )

    # Factory for request handler
    def handler_factory(*args, **kwargs):
        return MockRequestHandler(*args, project_dir=project_dir, config=mock_config, agent_config=agent_config, **kwargs)

    print("--- AI Mock Server ---")
    print(f"Listening on port {port}...")
    print(f"Agent: {agent_type}")
    print("Press Ctrl+C to stop.")

    try:
        with http.server.ThreadingHTTPServer(("", port), handler_factory) as httpd:
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server...")
    except Exception as e:
        print(f"❌ Server error: {e}")
