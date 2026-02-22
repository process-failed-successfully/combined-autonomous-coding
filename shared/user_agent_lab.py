import re
from typing import Dict, Optional, List

class UserAgentManager:
    """Manages User Agent parsing and generation."""

    def __init__(self):
        # Common Bot Signatures
        self.bot_signatures = [
            "Googlebot", "Bingbot", "Slurp", "DuckDuckBot", "Baiduspider",
            "YandexBot", "Sogou", "Exabot", "facebot", "ia_archiver"
        ]

        # Generator Templates
        self.templates = {
            "Windows": {
                "Chrome": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{version} Safari/537.36",
                "Firefox": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:{version}) Gecko/20100101 Firefox/{version}",
                "Edge": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{version} Safari/537.36 Edg/{version}",
            },
            "Mac": {
                "Chrome": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{version} Safari/537.36",
                "Safari": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/{version} Safari/605.1.15",
                "Firefox": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:{version}) Gecko/20100101 Firefox/{version}",
            },
            "Linux": {
                "Chrome": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{version} Safari/537.36",
                "Firefox": "Mozilla/5.0 (X11; Linux x86_64; rv:{version}) Gecko/20100101 Firefox/{version}",
            },
            "Android": {
                "Chrome": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{version} Mobile Safari/537.36",
                "Firefox": "Mozilla/5.0 (Android 10; Mobile; rv:{version}) Gecko/{version} Firefox/{version}",
            },
            "iOS": {
                "Safari": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/{version} Mobile/15E148 Safari/604.1",
                "Chrome": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/{version} Mobile/15E148 Safari/604.1",
            }
        }

        # Default Versions for Generation
        self.default_versions = {
            "Chrome": "120.0.0.0",
            "Firefox": "121.0",
            "Safari": "17.2",
            "Edge": "120.0.0.0",
        }

    def parse(self, ua_string: str) -> Dict[str, str]:
        """Parses a User Agent string."""
        result = {
            "browser": "Unknown",
            "version": "Unknown",
            "os": "Unknown",
            "device": "Desktop", # Default to Desktop
            "engine": "Unknown",
            "is_bot": "Yes" if self.is_bot(ua_string) else "No"
        }

        if not ua_string:
            return result

        # OS Detection
        if "Windows" in ua_string:
            result["os"] = "Windows"
        elif "Macintosh" in ua_string or "Mac OS X" in ua_string:
            result["os"] = "Mac OS X"
            if "iPhone" in ua_string or "iPad" in ua_string:
                result["os"] = "iOS"
                result["device"] = "Mobile" if "iPhone" in ua_string else "Tablet"
        elif "Android" in ua_string:
            result["os"] = "Android"
            result["device"] = "Mobile"
        elif "Linux" in ua_string:
            result["os"] = "Linux"

        # Browser Detection (Order matters!)
        # Edge
        if "Edg/" in ua_string:
            result["browser"] = "Edge"
            match = re.search(r"Edg/([\d.]+)", ua_string)
            if match: result["version"] = match.group(1)
            result["engine"] = "Blink"
        # Chrome (must be checked after Edge because Edge contains Chrome)
        elif "Chrome" in ua_string or "CriOS" in ua_string:
            result["browser"] = "Chrome"
            match = re.search(r"(?:Chrome|CriOS)/([\d.]+)", ua_string)
            if match: result["version"] = match.group(1)
            result["engine"] = "Blink"
        # Firefox
        elif "Firefox" in ua_string or "FxiOS" in ua_string:
            result["browser"] = "Firefox"
            match = re.search(r"(?:Firefox|FxiOS)/([\d.]+)", ua_string)
            if match: result["version"] = match.group(1)
            result["engine"] = "Gecko"
        # Safari (must be checked after Chrome because Chrome contains Safari)
        elif "Safari" in ua_string:
            result["browser"] = "Safari"
            match = re.search(r"Version/([\d.]+)", ua_string)
            if match: result["version"] = match.group(1)
            result["engine"] = "WebKit"
        # IE
        elif "MSIE" in ua_string or "Trident" in ua_string:
            result["browser"] = "Internet Explorer"
            match = re.search(r"(?:MSIE |rv:)([\d.]+)", ua_string)
            if match: result["version"] = match.group(1)
            result["engine"] = "Trident"

        return result

    def generate(self, os_name: str, browser: str, version: Optional[str] = None) -> Optional[str]:
        """Generates a UA string."""
        if os_name not in self.templates:
            return None
        if browser not in self.templates[os_name]:
            return None

        template = self.templates[os_name][browser]
        ver = version or self.default_versions.get(browser, "1.0")

        return template.format(version=ver)

    def is_bot(self, ua_string: str) -> bool:
        """Checks if the UA belongs to a bot."""
        lower_ua = ua_string.lower()
        for bot in self.bot_signatures:
            if bot.lower() in lower_ua:
                return True
        return False
