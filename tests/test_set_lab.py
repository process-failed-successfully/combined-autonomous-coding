import pytest
from shared.set_lab import SetLabManager

@pytest.fixture
def manager():
    return SetLabManager()

def test_set_union(manager):
    list_a = ["apple", "banana"]
    list_b = ["banana", "cherry"]
    result = manager.perform_operation(list_a, list_b, "union")
    assert sorted(result) == ["apple", "banana", "cherry"]

def test_set_intersect(manager):
    list_a = ["apple", "banana", "cherry"]
    list_b = ["banana", "date"]
    result = manager.perform_operation(list_a, list_b, "intersect")
    assert sorted(result) == ["banana"]

def test_set_difference(manager):
    list_a = ["apple", "banana", "cherry"]
    list_b = ["banana", "date"]
    result = manager.perform_operation(list_a, list_b, "difference")
    assert sorted(result) == ["apple", "cherry"]

def test_set_sym_diff(manager):
    list_a = ["apple", "banana", "cherry"]
    list_b = ["banana", "date"]
    result = manager.perform_operation(list_a, list_b, "sym_diff")
    assert sorted(result) == ["apple", "cherry", "date"]

def test_set_is_subset(manager):
    list_a = ["apple", "banana"]
    list_b = ["apple", "banana", "cherry"]
    assert manager.perform_operation(list_a, list_b, "is_subset") is True

    list_a = ["apple", "date"]
    assert manager.perform_operation(list_a, list_b, "is_subset") is False

def test_set_is_superset(manager):
    list_a = ["apple", "banana", "cherry"]
    list_b = ["apple", "banana"]
    assert manager.perform_operation(list_a, list_b, "is_superset") is True

    list_b = ["apple", "date"]
    assert manager.perform_operation(list_a, list_b, "is_superset") is False

def test_set_ignore_case(manager):
    list_a = ["Apple", "banana"]
    list_b = ["APPLE", "cherry"]
    # It should return 'Apple' from list_a or 'APPLE' from list_b
    result = manager.perform_operation(list_a, list_b, "intersect", ignore_case=True)
    # The current implementation uses the first found original case.
    # list_b mapping is added first, then list_a, so list_a overwrites list_b.
    assert sorted(result) == ["Apple"]

def test_set_trim(manager):
    list_a = [" apple ", "banana"]
    list_b = ["apple", "cherry"]
    result = manager.perform_operation(list_a, list_b, "intersect", trim=True)
    assert sorted(result) == ["apple"]

def test_set_ignore_case_and_trim(manager):
    list_a = [" APPLE ", "banana"]
    list_b = ["apple", "cherry"]
    result = manager.perform_operation(list_a, list_b, "intersect", ignore_case=True, trim=True)
    assert sorted(result) == [" APPLE "]

def test_unknown_operation(manager):
    with pytest.raises(ValueError, match="Unknown operation: invalid_op"):
        manager.perform_operation([], [], "invalid_op")
