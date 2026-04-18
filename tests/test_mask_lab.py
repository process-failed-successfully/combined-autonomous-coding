import pytest
from shared.mask_lab import MaskLabManager

def test_mask_email():
    manager = MaskLabManager()
    text = "Contact me at test@example.com for more info."
    masked = manager.mask_text(text, rules=["email"])
    assert "t**t@example.com" in masked

def test_mask_email_short():
    manager = MaskLabManager()
    text = "My email is a@b.com."
    masked = manager.mask_text(text, rules=["email"])
    assert "a@b.com" not in masked
    assert "*@b.com" in masked

def test_mask_phone():
    manager = MaskLabManager()
    text = "Call 123-456-7890 today!"
    masked = manager.mask_text(text, rules=["phone"])
    # 123-456-7890 is 12 chars
    assert "Call ************ today!" in masked

def test_mask_credit_card():
    manager = MaskLabManager()
    text = "My CC is 1234 5678 1234 5678."
    masked = manager.mask_text(text, rules=["credit_card"])
    assert "My CC is **** **** **** 5678." in masked

def test_mask_ssn():
    manager = MaskLabManager()
    text = "SSN: 123-45-6789"
    masked = manager.mask_text(text, rules=["ssn"])
    # 123-45-6789 is 11 chars
    assert "SSN: ***********" in masked

def test_mask_ipv4():
    manager = MaskLabManager()
    text = "Server IP is 192.168.1.1"
    masked = manager.mask_text(text, rules=["ipv4"])
    # 192.168.1.1 is 11 chars
    assert "Server IP is ***********" in masked

def test_mask_all():
    manager = MaskLabManager()
    text = "Email: john@doe.com, Phone: 555-555-5555, CC: 1111-2222-3333-4444"
    masked = manager.mask_text(text) # Should mask all by default
    assert "j**n@doe.com" in masked
    # 555-555-5555 is 12 chars
    assert "************" in masked
    assert "****-****-****-4444" in masked

def test_mask_empty_text():
    manager = MaskLabManager()
    assert manager.mask_text("") == ""
    assert manager.mask_text(None) == None
