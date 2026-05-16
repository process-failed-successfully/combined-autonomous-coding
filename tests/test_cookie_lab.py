from shared.cookie_lab import CookieLabManager
import json
import argparse
from shared.cookie_lab import run_cookie_lab_logic


class TestCookieLab:
    def setup_method(self):
        self.manager = CookieLabManager()

    def test_parse_cookie(self):
        cookie_str = 'session_id=12345; Domain=example.com; Path=/; Secure; HttpOnly'
        parsed = self.manager.parse(cookie_str)
        assert len(parsed) == 1
        c = parsed[0]
        assert c["name"] == "session_id"
        assert c["value"] == "12345"
        assert c["domain"] == "example.com"
        assert c["path"] == "/"
        assert c["secure"] is True or str(c["secure"]).lower() in ["true", "1", "yes"]
        assert c["httponly"] is True or str(c["httponly"]).lower() in ["true", "1", "yes"]

    def test_generate_cookie(self):
        data = [{
            "name": "test_cookie",
            "value": "abc",
            "domain": ".test.com",
            "path": "/test",
            "secure": True,
            "httponly": True
        }]
        result = self.manager.generate(data)
        assert len(result) == 1
        s = result[0]
        assert "test_cookie=abc" in s
        assert "Domain=.test.com" in s
        assert "Path=/test" in s
        assert "Secure" in s
        assert "HttpOnly" in s

    def test_parse_invalid(self):
        # A weird string that might not be a valid cookie shouldn't crash, but return gracefully
        parsed = self.manager.parse("")
        assert len(parsed) == 0

    def test_cli_parse(self, capsys):
        args = argparse.Namespace(action="parse", cookie="a=b; Domain=c.com")
        res = run_cookie_lab_logic(args)
        assert res is True
        captured = capsys.readouterr()
        out = captured.out
        assert "a" in out
        assert "b" in out
        assert "c.com" in out

    def test_cli_generate(self, capsys):
        data = [{"name": "foo", "value": "bar"}]
        args = argparse.Namespace(action="generate", json=json.dumps(data))
        res = run_cookie_lab_logic(args)
        assert res is True
        captured = capsys.readouterr()
        assert "foo=bar" in captured.out
