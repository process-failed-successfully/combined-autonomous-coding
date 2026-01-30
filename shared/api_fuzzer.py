import random
import string
import json
import concurrent.futures
from typing import Any, Dict, List, Generator

class APIFuzzer:
    """
    Fuzzes API endpoints by generating and mutating payloads based on OpenAPI schema.
    """
    def __init__(self, manager):
        self.manager = manager

    def generate_valid_payload(self, schema: Dict[str, Any]) -> Any:
        """
        Generates a valid payload based on the OpenAPI schema.
        Recursively handles objects, arrays, and primitives.
        """
        if not schema:
            return {}

        # Handle 'allOf', 'oneOf', 'anyOf' - basic support: take the first one or merge
        if 'allOf' in schema:
            combined = {}
            for sub in schema['allOf']:
                combined.update(self.generate_valid_payload(sub))
            return combined

        if 'oneOf' in schema:
            return self.generate_valid_payload(schema['oneOf'][0])

        if 'anyOf' in schema:
            return self.generate_valid_payload(schema['anyOf'][0])

        type_ = schema.get('type')

        if not type_ and 'properties' in schema:
            type_ = 'object'

        if type_ == 'object':
            properties = schema.get('properties', {})
            obj = {}
            for key, prop_schema in properties.items():
                obj[key] = self.generate_valid_payload(prop_schema)
            return obj

        elif type_ == 'array':
            items_schema = schema.get('items', {})
            # Generate a list with 1 item for validity
            return [self.generate_valid_payload(items_schema)]

        elif type_ == 'string':
            fmt = schema.get('format')
            if fmt == 'date-time':
                return "2023-01-01T12:00:00Z"
            elif fmt == 'date':
                return "2023-01-01"
            elif fmt == 'uuid':
                return "123e4567-e89b-12d3-a456-426614174000"
            elif fmt == 'email':
                return "test@example.com"
            return "test_string"

        elif type_ == 'integer':
            return 1

        elif type_ == 'number':
            return 1.5

        elif type_ == 'boolean':
            return True

        return None

    def generate_fuzz_payloads(self, valid_payload: Any) -> Generator[Any, None, None]:
        """
        Generates mutations of the valid payload.
        """
        # Yield the valid one first (baseline)
        yield valid_payload

        if isinstance(valid_payload, dict):
            # 1. Missing fields
            for key in valid_payload:
                mutated = valid_payload.copy()
                del mutated[key]
                yield mutated

            # 2. Type Mismatch (e.g. str for int)
            for key, val in valid_payload.items():
                mutated = valid_payload.copy()
                if isinstance(val, int):
                    mutated[key] = "not_an_int"
                elif isinstance(val, str):
                    mutated[key] = 12345
                elif isinstance(val, bool):
                    mutated[key] = "not_a_bool"
                yield mutated

            # 3. Null values
            for key in valid_payload:
                mutated = valid_payload.copy()
                mutated[key] = None
                yield mutated

            # 4. Large payloads (buffer overflow / DoS)
            for key, val in valid_payload.items():
                if isinstance(val, str):
                    mutated = valid_payload.copy()
                    mutated[key] = "A" * 10000
                    yield mutated

            # 5. Injection strings
            injections = ["' OR 1=1 --", "<script>alert(1)</script>", "../../etc/passwd", "${jndi:ldap://...}"]
            for key, val in valid_payload.items():
                if isinstance(val, str):
                    for inj in injections:
                        mutated = valid_payload.copy()
                        mutated[key] = inj
                        yield mutated

        elif isinstance(valid_payload, list):
            # Empty list
            yield []
            # Large list
            if valid_payload:
                yield valid_payload * 100

    def fuzz_endpoint(self, method: str, url: str, schema: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Runs the fuzzing loop against the endpoint.
        """
        results = []

        # Determine payload source
        # Ideally we find the schema for the body.
        # If schema passed is the *whole* operation object, we need to dig for requestBody
        body_schema = {}
        if schema:
            content = schema.get('requestBody', {}).get('content', {})
            if 'application/json' in content:
                body_schema = content['application/json'].get('schema', {})

        # If no schema found, but we want to fuzz, we need a base payload.
        # If url has params, we might want to fuzz those too, but sticking to body for now.

        base_payload = self.generate_valid_payload(body_schema) if body_schema else {"fuzz": "test"}

        payloads = list(self.generate_fuzz_payloads(base_payload))

        print(f"Generated {len(payloads)} fuzz payloads for {method} {url}")

        max_workers = 5
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Helper to execute request
            def run_req(p):
                try:
                    b_str = json.dumps(p)
                    return self.manager.execute_request(method, url, body=b_str), None
                except Exception as exc:
                    return None, exc

            future_to_payload = {
                executor.submit(run_req, p): (i, p)
                for i, p in enumerate(payloads)
            }

            for future in concurrent.futures.as_completed(future_to_payload):
                index, payload = future_to_payload[future]
                try:
                    result, error = future.result()

                    if error:
                        print(f"  [{index+1}] Error: {error}")
                        results.append({"payload": payload, "error": str(error), "crash": False})
                        continue

                    status = result['status_code']
                    is_crash = 500 <= status < 600

                    results.append({
                        "payload": payload,
                        "status": status,
                        "crash": is_crash
                    })

                    marker = "🔥" if is_crash else "✅" if status < 500 else "❓"
                    print(f"  [{index+1}/{len(payloads)}] {marker} Status: {status}")

                except Exception as e:
                    print(f"  [{index+1}] Critical Error: {e}")
                    results.append({"payload": payload, "error": str(e), "crash": False})

        return results
