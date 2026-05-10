import argparse
import sys
import json
from http.cookies import SimpleCookie
from typing import Dict, Any, List

class CookieLabManager:
    """Manages Cookie parsing and generation operations."""

    def parse(self, cookie_string: str) -> List[Dict[str, Any]]:
        """Parses a Set-Cookie string or multiple cookies string into a structured list of dicts."""
        cookie = SimpleCookie()
        try:
            cookie.load(cookie_string)
        except Exception as e:
            raise ValueError(f"Failed to parse cookie string: {e}")

        results = []
        for key, morsel in cookie.items():
            parsed_cookie = {
                "name": key,
                "value": morsel.value,
            }
            # Add attributes if they exist
            if morsel["domain"]:
                parsed_cookie["domain"] = morsel["domain"]
            if morsel["path"]:
                parsed_cookie["path"] = morsel["path"]
            if morsel["expires"]:
                parsed_cookie["expires"] = morsel["expires"]
            if morsel["max-age"]:
                parsed_cookie["max-age"] = morsel["max-age"]
            if morsel["secure"]:
                parsed_cookie["secure"] = bool(morsel["secure"])
            if morsel["httponly"]:
                parsed_cookie["httponly"] = bool(morsel["httponly"])
            if morsel["samesite"]:
                parsed_cookie["samesite"] = morsel["samesite"]

            results.append(parsed_cookie)
        return results

    def generate(self, name: str, value: str, **kwargs) -> str:
        """Generates a Set-Cookie string from properties."""
        cookie = SimpleCookie()
        cookie[name] = value

        morsel = cookie[name]

        if kwargs.get('domain'):
            morsel['domain'] = kwargs['domain']
        if kwargs.get('path'):
            morsel['path'] = kwargs['path']
        if kwargs.get('expires'):
            morsel['expires'] = kwargs['expires']
        if kwargs.get('max_age'):
            morsel['max-age'] = kwargs['max_age']
        if kwargs.get('secure'):
            morsel['secure'] = True
        if kwargs.get('httponly'):
            morsel['httponly'] = True
        if kwargs.get('samesite'):
            morsel['samesite'] = kwargs['samesite']

        return cookie.output(header="Set-Cookie:").strip()


def run_cookie_lab_logic(args: argparse.Namespace):
    """CLI handler for Cookie Lab."""
    manager = CookieLabManager()

    if getattr(args, "action", None) == "tui":
        from shared.tui import AgentTUI
        print("Launching Cookie Lab TUI...")
        app = AgentTUI(project_dir=getattr(args, 'project_dir', None), start_tab="tab-cookie")
        app.run()
        sys.exit(0)

    if args.action == "parse":
        try:
            results = manager.parse(args.cookie_string)
            print(json.dumps(results, indent=2))
        except Exception as e:
            print(f"Error parsing cookie: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.action == "generate":
        try:
            result = manager.generate(
                name=args.name,
                value=args.value,
                domain=getattr(args, 'domain', None),
                path=getattr(args, 'path', None),
                expires=getattr(args, 'expires', None),
                max_age=getattr(args, 'max_age', None),
                secure=getattr(args, 'secure', False),
                httponly=getattr(args, 'httponly', False),
                samesite=getattr(args, 'samesite', None)
            )
            print(result)
        except Exception as e:
            print(f"Error generating cookie: {e}", file=sys.stderr)
            sys.exit(1)
