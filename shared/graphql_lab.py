import sys
import json
import requests
import time
from typing import Dict, Any, Optional

class GraphQLLabManager:
    """
    Manages GraphQL requests and introspection.
    """

    def __init__(self, url: str, headers: Optional[Dict[str, str]] = None):
        self.url = url
        self.headers = headers or {}
        # Ensure Content-Type is set for GraphQL
        if "Content-Type" not in self.headers:
            self.headers["Content-Type"] = "application/json"

    def execute(self, query: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Executes a GraphQL query/mutation.
        """
        payload = {"query": query}
        if variables:
            payload["variables"] = variables

        try:
            start_time = time.time()
            response = requests.post(self.url, json=payload, headers=self.headers, timeout=30)
            elapsed = time.time() - start_time

            result = {
                "status_code": response.status_code,
                "elapsed": elapsed,
                "ok": response.ok,
                "headers": dict(response.headers)
            }

            try:
                result["json"] = response.json()
            except ValueError:
                result["body"] = response.text
                result["error"] = "Invalid JSON response"

            return result

        except requests.exceptions.RequestException as e:
            return {"error": str(e), "ok": False, "status_code": 0}

    def introspect(self) -> Dict[str, Any]:
        """
        Performs a standard introspection query.
        """
        introspection_query = """
        query IntrospectionQuery {
          __schema {
            queryType { name }
            mutationType { name }
            subscriptionType { name }
            types {
              ...FullType
            }
            directives {
              name
              description
              locations
              args {
                ...InputValue
              }
            }
          }
        }

        fragment FullType on __Type {
          kind
          name
          description
          fields(includeDeprecated: true) {
            name
            description
            args {
              ...InputValue
            }
            type {
              ...TypeRef
            }
            isDeprecated
            deprecationReason
          }
          inputFields {
            ...InputValue
          }
          interfaces {
            ...TypeRef
          }
          enumValues(includeDeprecated: true) {
            name
            description
            isDeprecated
            deprecationReason
          }
          possibleTypes {
            ...TypeRef
          }
        }

        fragment InputValue on __InputValue {
          name
          description
          type { ...TypeRef }
          defaultValue
        }

        fragment TypeRef on __Type {
          kind
          name
          ofType {
            kind
            name
            ofType {
              kind
              name
              ofType {
                kind
                name
                ofType {
                  kind
                  name
                  ofType {
                    kind
                    name
                    ofType {
                      kind
                      name
                      ofType {
                        kind
                        name
                      }
                    }
                  }
                }
              }
            }
          }
        }
        """
        return self.execute(introspection_query)

def run_graphql_lab_logic(args):
    """
    CLI logic for GraphQL Lab.
    """
    # Parse headers
    headers = {}
    if args.header:
        for h in args.header:
            if ":" in h:
                k, v = h.split(":", 1)
                headers[k.strip()] = v.strip()
            else:
                pass

    manager = GraphQLLabManager(args.url, headers)

    if args.action == "query":
        query = args.query
        # If query is a file, read it
        try:
            with open(query, "r") as f:
                query = f.read()
        except (FileNotFoundError, OSError):
            pass # Assume it's a raw query string

        variables = None
        if args.variables:
            # Try to read from file
            try:
                with open(args.variables, "r") as f:
                    variables = json.load(f)
            except (FileNotFoundError, OSError):
                # Try to parse as JSON string
                try:
                    variables = json.loads(args.variables)
                except json.JSONDecodeError as e:
                    print(f"Error parsing variables: {e}", file=sys.stderr)
                    sys.exit(1)

        print(f"--- GraphQL Query to {args.url} ---")
        result = manager.execute(query, variables)

        if not result["ok"]:
            print(f"❌ Request Failed (Status: {result.get('status_code')})")
            if "error" in result:
                print(f"Error: {result['error']}")
            if "body" in result:
                print(f"Body: {result['body']}")
            sys.exit(1)

        data = result.get("json", {})

        # Check for GraphQL errors
        if "errors" in data:
            print("⚠️  GraphQL Errors:")
            print(json.dumps(data["errors"], indent=2))

        if "data" in data:
            print("✅ Data:")
            print(json.dumps(data["data"], indent=2))

        if args.verbose:
            print(f"\nTime: {result.get('elapsed', 0):.3f}s")

    elif args.action == "schema":
        print(f"--- Introspecting Schema at {args.url} ---")
        result = manager.introspect()

        if not result["ok"]:
            print(f"❌ Introspection Failed (Status: {result.get('status_code')})")
            sys.exit(1)

        data = result.get("json", {})
        if "errors" in data:
            print("❌ GraphQL Errors during introspection:")
            print(json.dumps(data["errors"], indent=2))
            sys.exit(1)

        schema = data.get("data", {}).get("__schema")
        if not schema:
            print("❌ No schema found in response.")
            sys.exit(1)

        if args.format == "json":
            print(json.dumps(data, indent=2))
        else:
            # Simple SDL-like summary
            print("\nTypes:")
            for t in schema.get("types", []):
                if not t["name"].startswith("__"):
                     kind = t["kind"]
                     print(f"  {kind} {t['name']}")

            print("\nDirectives:")
            for d in schema.get("directives", []):
                print(f"  @{d['name']}")

    sys.exit(0)
