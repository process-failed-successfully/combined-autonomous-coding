import sys
import json
from http.cookies import SimpleCookie


class CookieLabManager:
    """Manages Cookie parsing and generation operations."""

    def parse(self, cookie_string: str) -> list:
        """Parses a raw Cookie or Set-Cookie header into structured data."""
        # SimpleCookie handles both "Cookie" (multiple key=value separated by semicolon)
        # and "Set-Cookie" format well enough, though "Set-Cookie" usually comes one per line.

        cookie = SimpleCookie()
        try:
            cookie.load(cookie_string)
        except Exception as e:
            return [{"error": str(e)}]

        parsed = []
        for key, morsel in cookie.items():
            entry = {
                "name": key,
                "value": morsel.value,
            }
            # Add standard attributes if present
            for attr in ["domain", "path", "expires", "max-age", "secure", "httponly", "samesite"]:
                if morsel[attr]:
                    entry[attr] = morsel[attr]
            parsed.append(entry)

        return parsed

    def generate(self, cookie_data: list) -> list:
        """Generates Set-Cookie header strings from a list of structured dictionaries."""
        results = []
        for c_data in cookie_data:
            if "name" not in c_data or "value" not in c_data:
                continue

            cookie = SimpleCookie()
            name = c_data["name"]
            value = c_data["value"]
            cookie[name] = value
            morsel = cookie[name]

            for attr in ["domain", "path", "expires", "secure", "httponly", "samesite"]:
                if attr in c_data:
                    # 'secure' and 'httponly' should be empty string or True-like in SimpleCookie
                    # but SimpleCookie accepts boolean if we convert it appropriately or just string
                    if attr in ("secure", "httponly"):
                        if str(c_data[attr]).lower() in ("true", "1", "yes"):
                            morsel[attr] = True
                    else:
                        morsel[attr] = str(c_data[attr])

            # SimpleCookie output is 'Set-Cookie: name=value; ...'
            results.append(cookie.output(header="").strip())
        return results


def run_cookie_lab_logic(args) -> bool:
    """CLI logic for the Cookie Lab."""
    manager = CookieLabManager()

    if args.action == "parse":
        if getattr(args, "cookie", None):
            res = manager.parse(args.cookie)
            print(json.dumps(res, indent=2))
            return True
        else:
            print("Error: --cookie string required.", file=sys.stderr)
            return False

    elif args.action == "generate":
        if getattr(args, "json", None):
            try:
                data = json.loads(args.json)
                if isinstance(data, dict):
                    data = [data]
                res = manager.generate(data)
                for r in res:
                    print(r)
                return True
            except Exception as e:
                print(f"Error generating cookie: {e}", file=sys.stderr)
                return False
        else:
            print("Error: --json required.", file=sys.stderr)
            return False

    return False
