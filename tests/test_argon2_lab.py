import pytest

pytest.importorskip("argon2")

from shared.argon2_lab import Argon2LabManager

class TestArgon2LabManager:
    def setup_method(self):
        self.manager = Argon2LabManager()

    def test_hash_password(self):
        password = "mysecretpassword123!"
        hashed = self.manager.hash_password(
            password=password,
            time_cost=2,
            memory_cost=10240,
            parallelism=2,
            hash_len=16
        )
        assert hashed.startswith("$argon2id$v=19$m=10240,t=2,p=2$")

    def test_verify_password_success(self):
        password = "mysecretpassword123!"
        hashed = self.manager.hash_password(password)
        is_valid = self.manager.verify_password(password, hashed)
        assert is_valid is True

    def test_verify_password_failure(self):
        password = "mysecretpassword123!"
        wrong_password = "wrongpassword"
        hashed = self.manager.hash_password(password)
        is_valid = self.manager.verify_password(wrong_password, hashed)
        assert is_valid is False
