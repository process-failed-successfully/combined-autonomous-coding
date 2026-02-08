import pytest
from shared.unit_lab import UnitLabManager

class TestUnitLabManager:
    @pytest.fixture
    def manager(self):
        return UnitLabManager()

    def test_storage_conversion(self, manager):
        # KB to Bytes
        assert manager.convert(1, "kb", "b") == 1000.0
        # KiB to Bytes
        assert manager.convert(1, "kib", "b") == 1024.0
        # MB to KB
        assert manager.convert(1, "mb", "kb") == 1000.0
        # GB to MB
        assert manager.convert(1, "gb", "mb") == 1000.0

    def test_time_conversion(self, manager):
        # Minutes to Seconds
        assert manager.convert(1, "m", "s") == 60.0
        # Hours to Minutes
        assert manager.convert(1, "h", "m") == 60.0
        # Days to Hours
        assert manager.convert(1, "d", "h") == 24.0

    def test_length_conversion(self, manager):
        # Meters to Centimeters
        assert manager.convert(1, "m", "cm") == 100.0
        # Kilometers to Meters
        assert manager.convert(1, "km", "m") == 1000.0
        # Inches to cm (approx check)
        assert abs(manager.convert(1, "in", "cm") - 2.54) < 0.0001

    def test_weight_conversion(self, manager):
        # Kilograms to Grams
        assert manager.convert(1, "kg", "g") == 1000.0
        # Pounds to Kilograms (approx check)
        assert abs(manager.convert(1, "lb", "kg") - 0.453592) < 0.0001

    def test_temperature_conversion(self, manager):
        # Celsius to Fahrenheit
        assert manager.convert(0, "c", "f") == 32.0
        assert manager.convert(100, "c", "f") == 212.0
        # Fahrenheit to Celsius
        assert manager.convert(32, "f", "c") == 0.0
        # Celsius to Kelvin
        assert manager.convert(0, "c", "k") == 273.15
        # Kelvin to Celsius
        assert manager.convert(273.15, "k", "c") == 0.0

    def test_invalid_units(self, manager):
        with pytest.raises(ValueError, match="Unknown unit"):
            manager.convert(1, "foo", "bar")

    def test_incompatible_categories(self, manager):
        with pytest.raises(ValueError, match="Incompatible units"):
            manager.convert(1, "m", "kg")

    def test_case_insensitivity(self, manager):
        assert manager.convert(1, "KB", "b") == 1000.0
        assert manager.convert(1, "m", "CM") == 100.0
