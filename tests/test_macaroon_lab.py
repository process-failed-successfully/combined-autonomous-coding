import pytest
from shared.macaroon_lab import MacaroonManager

def test_macaroon_generate():
    res = MacaroonManager.generate("http://localhost", "test_id", "test_secret")
    assert res["success"] is True
    assert "token" in res
    assert res["token"].startswith("MDA")

def test_macaroon_inspect():
    res = MacaroonManager.generate("http://localhost", "test_id", "test_secret")
    token = res["token"]

    inspect_res = MacaroonManager.inspect(token)
    assert inspect_res["success"] is True
    assert inspect_res["location"] == "http://localhost"
    assert inspect_res["identifier"] == "test_id"
    assert inspect_res["caveats"] == []

def test_macaroon_caveat():
    res = MacaroonManager.generate("http://localhost", "test_id", "test_secret")
    token = res["token"]

    caveat_res = MacaroonManager.add_caveat(token, "time < 2025")
    assert caveat_res["success"] is True
    new_token = caveat_res["token"]

    inspect_res = MacaroonManager.inspect(new_token)
    assert inspect_res["success"] is True
    assert len(inspect_res["caveats"]) == 1
    assert inspect_res["caveats"][0] == "time < 2025"

def test_macaroon_verify_success():
    res = MacaroonManager.generate("http://localhost", "test_id", "test_secret")
    token = res["token"]

    verify_res = MacaroonManager.verify(token, "test_secret")
    assert verify_res["success"] is True

def test_macaroon_verify_failure():
    res = MacaroonManager.generate("http://localhost", "test_id", "test_secret")
    token = res["token"]

    verify_res = MacaroonManager.verify(token, "wrong_secret")
    assert verify_res["success"] is False

def test_macaroon_verify_with_caveats():
    res = MacaroonManager.generate("http://localhost", "test_id", "test_secret")
    token = res["token"]

    caveat_res = MacaroonManager.add_caveat(token, "time < 2025")
    new_token = caveat_res["token"]

    # Needs caveat to be satisfied
    verify_res = MacaroonManager.verify(new_token, "test_secret", ["time < 2025"])
    assert verify_res["success"] is True

def test_macaroon_verify_missing_caveat():
    res = MacaroonManager.generate("http://localhost", "test_id", "test_secret")
    token = res["token"]

    caveat_res = MacaroonManager.add_caveat(token, "time < 2025")
    new_token = caveat_res["token"]

    # Missing caveat satisfaction
    verify_res = MacaroonManager.verify(new_token, "test_secret", [])
    assert verify_res["success"] is False
