import sys
import http.cookies
import json


class CookieLabManager:
    """Manages parsing and generating HTTP Cookie headers."""

    def parse_cookie(self, cookie_string: str) -> dict:
        """Parses a Cookie or Set-Cookie string into a dictionary."""
        cookie = http.cookies.SimpleCookie()
        try:
            cookie.load(cookie_string)
        except http.cookies.CookieError as e:
            return {"error": str(e)}

        result = {}
        for key, morsel in cookie.items():
            morsel_dict = {"value": morsel.value}
            # Add other attributes if they exist
            for attr in ['expires', 'path', 'comment', 'domain', 'max-age', 'secure', 'httponly', 'version', 'samesite']:
                if morsel[attr]:
                    morsel_dict[attr] = morsel[attr]
            result[key] = morsel_dict
        return {"cookies": result}

    def generate_cookie(self, key: str, value: str, **kwargs) -> dict:
        """Generates a Set-Cookie string."""
        cookie = http.cookies.SimpleCookie()
        cookie[key] = value
        morsel = cookie[key]

        for attr, attr_value in kwargs.items():
            if attr_value is not None:
                morsel[attr] = attr_value

        return {"set_cookie": morsel.OutputString()}


def run_cookie_lab_logic(args) -> bool:
    """CLI entry point for Cookie Lab logic."""
    manager = CookieLabManager()

    if getattr(args, "action", None) == "parse":
        if not getattr(args, "string", None):
            print("Error: --string is required for parsing.", file=sys.stderr)
            return False

        res = manager.parse_cookie(args.string)
        if "error" in res:
            print(f"Error parsing cookie: {res['error']}", file=sys.stderr)
            return False

        print(json.dumps(res, indent=2))
        return True

    elif getattr(args, "action", None) == "generate":
        if not getattr(args, "key", None) or not getattr(args, "value", None):
            print("Error: --key and --value are required for generation.", file=sys.stderr)
            return False

        kwargs = {}
        if getattr(args, "domain", None):
            kwargs["domain"] = args.domain
        if getattr(args, "path", None):
            kwargs["path"] = args.path
        if getattr(args, "expires", None):
            kwargs["expires"] = args.expires
        if getattr(args, "max_age", None):
            kwargs["max-age"] = args.max_age
        if getattr(args, "secure", False):
            kwargs["secure"] = True
        if getattr(args, "httponly", False):
            kwargs["httponly"] = True
        if getattr(args, "samesite", None):
            kwargs["samesite"] = args.samesite

        res = manager.generate_cookie(args.key, args.value, **kwargs)
        print(res["set_cookie"])
        return True

    else:
        print("Error: Unknown action or missing arguments.", file=sys.stderr)
        return False
