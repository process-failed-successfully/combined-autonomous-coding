import pytest
from shared.csp_lab import CspLabManager

@pytest.fixture
def manager():
    return CspLabManager()

def test_csp_parse(manager):
    policy = "default-src 'self'; img-src 'self' https://example.com; script-src 'unsafe-inline' 'unsafe-eval'"
    parsed = manager.parse(policy)

    assert "default-src" in parsed
    assert parsed["default-src"] == ["'self'"]

    assert "img-src" in parsed
    assert parsed["img-src"] == ["'self'", "https://example.com"]

    assert "script-src" in parsed
    assert parsed["script-src"] == ["'unsafe-inline'", "'unsafe-eval'"]

    # Test empty policy
    assert manager.parse("") == {}

    # Test malformed policy
    assert manager.parse(";;;") == {}

def test_csp_generate(manager):
    parsed = {
        "default-src": ["'self'"],
        "img-src": ["https://example.com"],
        "block-all-mixed-content": []
    }
    generated = manager.generate(parsed)
    assert "default-src 'self'" in generated
    assert "img-src https://example.com" in generated
    assert "block-all-mixed-content" in generated

    assert manager.generate({}) == ""

def test_csp_validate_valid(manager):
    policy = "default-src 'self'; img-src https://example.com; block-all-mixed-content"
    is_valid, warnings = manager.validate(policy)
    assert is_valid is True
    assert len(warnings) == 0

def test_csp_validate_invalid(manager):
    # Missing quotes on keyword
    policy1 = "default-src self"
    is_valid1, warnings1 = manager.validate(policy1)
    assert is_valid1 is False
    assert any("single quotes" in w and "'self'" in w for w in warnings1)

    # Unknown directive
    policy2 = "made-up-src 'self'"
    is_valid2, warnings2 = manager.validate(policy2)
    assert is_valid2 is False
    assert any("Unknown directive" in w and "made-up-src" in w for w in warnings2)

    # Empty directive value
    policy3 = "default-src; script-src 'self'"
    is_valid3, warnings3 = manager.validate(policy3)
    assert is_valid3 is False
    assert any("has no values" in w and "default-src" in w for w in warnings3)

def test_csp_validate_empty(manager):
    is_valid, warnings = manager.validate("")
    assert is_valid is False
    assert "Empty policy." in warnings[0]
