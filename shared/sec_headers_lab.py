import requests
import sys
from typing import Dict, Any, List, Tuple

class SecHeadersManager:
    """
    Analyzes HTTP security headers and provides a grade.
    """

    HEADERS_TO_CHECK = {
        "Strict-Transport-Security": {
            "required": True,
            "description": "Enforces HTTPS connections.",
            "recommendation": "max-age=31536000; includeSubDomains; preload"
        },
        "Content-Security-Policy": {
            "required": True,
            "description": "Prevents XSS and other code injection attacks.",
            "recommendation": "default-src 'self'"
        },
        "X-Frame-Options": {
            "required": True,
            "description": "Prevents clickjacking.",
            "recommendation": "DENY or SAMEORIGIN"
        },
        "X-Content-Type-Options": {
            "required": True,
            "description": "Prevents MIME-sniffing.",
            "recommendation": "nosniff"
        },
        "Referrer-Policy": {
            "required": True,
            "description": "Controls how much referrer information is included with requests.",
            "recommendation": "strict-origin-when-cross-origin"
        },
        "Permissions-Policy": {
            "required": False,
            "description": "Controls which browser features are allowed.",
            "recommendation": "geolocation=(), microphone=(), camera=()"
        }
    }

    def analyze_url(self, url: str) -> Dict[str, Any]:
        try:
            # Enforce http/https prefix if missing, default to https
            if not url.startswith('http://') and not url.startswith('https://'):
                url = 'https://' + url

            response = requests.head(url, timeout=10, allow_redirects=True)
            if response.status_code == 405: # Method Not Allowed
                response = requests.get(url, timeout=10, allow_redirects=True, stream=True)
            return self.analyze_headers(response.headers, url)
        except requests.exceptions.RequestException as e:
            return {"error": str(e), "url": url}

    def analyze_headers(self, headers: requests.structures.CaseInsensitiveDict, url: str = "") -> Dict[str, Any]:
        results = {}
        score = 100

        # requests.structures.CaseInsensitiveDict handles case-insensitive lookups automatically

        for header_name, config in self.HEADERS_TO_CHECK.items():
            value = headers.get(header_name)

            if value is not None:
                results[header_name] = {
                    "status": "Present",
                    "value": value,
                    "description": config["description"]
                }
            else:
                results[header_name] = {
                    "status": "Missing",
                    "value": None,
                    "description": config["description"]
                }
                if config["required"]:
                    score -= 15 # Deduct 15 points for missing required header

        # Additional checks for deprecated/insecure headers
        insecure_headers = ["X-Powered-By", "Server"]
        for header_name in insecure_headers:
            value = headers.get(header_name)
            if value is not None:
                results[header_name] = {
                    "status": "Warning",
                    "value": value,
                    "description": f"Information disclosure: {header_name} header is present."
                }
                score -= 5 # Minor deduction for information disclosure

        # Cap score at 0
        score = max(0, score)

        # Determine Grade
        grade = "F"
        if score >= 90:
            grade = "A"
        elif score >= 80:
            grade = "B"
        elif score >= 65:
            grade = "C"
        elif score >= 50:
            grade = "D"

        return {
            "url": url,
            "grade": grade,
            "score": score,
            "details": results
        }


async def run_sec_headers_lab_logic(args):
    """
    CLI Handler for Security Headers Lab.
    """
    if getattr(args, 'tui', False):
        from shared.tui import AgentTUI
        from pathlib import Path
        app = AgentTUI(project_dir=Path.cwd(), start_tab="tab-sec-headers-lab")
        import asyncio
        if asyncio.get_event_loop().is_running():
            await app.run_async()
        else:
            app.run()
        return

    if not args.url:
        print("Error: --url is required in CLI mode. Or use --tui for the interactive interface.", file=sys.stderr)
        sys.exit(1)

    manager = SecHeadersManager()
    print(f"Analyzing {args.url}...\n")

    result = manager.analyze_url(args.url)

    if "error" in result:
        print(f"Error analyzing URL: {result['error']}", file=sys.stderr)
        sys.exit(1)

    print(f"URL: {result['url']}")
    print(f"Grade: {result['grade']} (Score: {result['score']})\n")

    print(f"{'Header':<30} | {'Status':<10} | {'Value'}")
    print("-" * 80)

    for header, details in result["details"].items():
        val = details['value'] if details['value'] else 'N/A'
        # Truncate long values
        if len(val) > 40:
            val = val[:37] + "..."

        print(f"{header:<30} | {details['status']:<10} | {val}")

    if getattr(args, 'json', False):
        import json
        print("\nJSON Output:")
        print(json.dumps(result, indent=2))

    sys.exit(0)
