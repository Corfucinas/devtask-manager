"""Tests for input validation."""
import pytest
from src.validators import validate_title, validate_tags, validate_id

class TestValidateTitle:
    def test_valid_title(self):
        assert validate_title("Fix login bug") == "Fix login bug"
    def test_strips_whitespace(self):
        assert validate_title("  spaced  ") == "spaced"
    def test_empty_raises(self):
        with pytest.raises(ValueError, match="empty"):
            validate_title("")
    def test_too_long_raises(self):
        with pytest.raises(ValueError, match="200"):
            validate_title("x" * 201)

class TestValidateTags:
    def test_empty_returns_empty(self):
        assert validate_tags([]) == []
    def test_valid_tags(self):
        assert validate_tags(["backend", "api"]) == ["backend", "api"]
    def test_lowercases(self):
        assert validate_tags(["Backend"]) == ["backend"]
    def test_invalid_chars_raise(self):
        with pytest.raises(ValueError, match="Invalid tag"):
            validate_tags(["bad tag!"])

class TestValidateId:
    def test_valid_id(self):
        assert validate_id(1) == 1
    def test_zero_raises(self):
        with pytest.raises(ValueError):
            validate_id(0)
