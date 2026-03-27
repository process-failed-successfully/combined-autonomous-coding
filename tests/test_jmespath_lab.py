import pytest
from shared.jmespath_lab import JmesPathLabManager


def test_jmespath_lab_manager_evaluate_valid():
    manager = JmesPathLabManager()
    data = {
        "store": {
            "book": [
                {"title": "A", "author": "Alice"},
                {"title": "B", "author": "Bob"}
            ]
        }
    }

    result = manager.evaluate(data, "store.book[*].author")
    assert result == ["Alice", "Bob"]

    result = manager.evaluate(data, "store.book[0].title")
    assert result == "A"


def test_jmespath_lab_manager_evaluate_empty_path():
    manager = JmesPathLabManager()
    data = {"key": "value"}
    result = manager.evaluate(data, "")
    assert result == {"key": "value"}


def test_jmespath_lab_manager_evaluate_invalid_path():
    manager = JmesPathLabManager()
    data = {"key": "value"}
    with pytest.raises(ValueError, match="Invalid JMESPath expression"):
        manager.evaluate(data, "a..b")
