"""Tests for the fixer module."""

import pytest

from sherlockcode.core.fixer import (
    _parse_fix_block,
    _validate_python_syntax,
    CONFIDENCE_THRESHOLDS,
    SAFE_CATEGORIES,
)
from sherlockcode.core.reviewer import FixIssue, FixResult


class TestFixIssue:
    def test_create_fix_issue(self):
        fix = FixIssue(
            file="test.py",
            line="10",
            category="type_hints",
            confidence=99,
            original_code="def foo(x):",
            fixed_code="def foo(x: int) -> int:",
            explanation="Added type hints",
        )
        assert fix.file == "test.py"
        assert fix.category == "type_hints"
        assert fix.confidence == 99


class TestFixResult:
    def test_create_fix_result(self):
        result = FixResult()
        assert result.fixes == []
        assert result.applied == []
        assert result.skipped == []
        assert result.failed == []


class TestValidatePythonSyntax:
    def test_valid_syntax(self):
        code = "def foo(x: int) -> int:\n    return x + 1"
        assert _validate_python_syntax(code) is True

    def test_invalid_syntax(self):
        code = "def foo(x:):\n    return x +"
        assert _validate_python_syntax(code) is False

    def test_empty_code(self):
        assert _validate_python_syntax("") is True


class TestParseFixBlock:
    def test_parse_single_fix(self):
        text = """[FILE: test.py]
[LINE: 10]
[CATEGORY: type_hints]
[CONFIDENCE: 99]
[ORIGINAL:]
```python
def foo(x):
```
[FIXED:]
```python
def foo(x: int) -> int:
```
[EXPLANATION:]
Added type hints for better code quality."""
        fixes = _parse_fix_block(text)
        assert len(fixes) == 1
        assert fixes[0].file == "test.py"
        assert fixes[0].line == "10"
        assert fixes[0].category == "type_hints"
        assert fixes[0].confidence == 99
        assert "def foo(x):" in fixes[0].original_code
        assert "def foo(x: int)" in fixes[0].fixed_code

    def test_parse_multiple_fixes(self):
        text = """[FILE: test.py]
[LINE: 10]
[CATEGORY: type_hints]
[CONFIDENCE: 99]
[ORIGINAL:]
```python
def foo(x):
```
[FIXED:]
```python
def foo(x: int) -> int:
```
[EXPLANATION:]

[FILE: utils.py]
[LINE: 5]
[CATEGORY: naming]
[CONFIDENCE: 98]
[ORIGINAL:]
```python
def getData():
```
[FIXED:]
```python
def get_data():
```
[EXPLANATION:]
Renamed to snake_case."""
        fixes = _parse_fix_block(text)
        assert len(fixes) == 2
        assert fixes[0].file == "test.py"
        assert fixes[1].file == "utils.py"

    def test_parse_empty_text(self):
        fixes = _parse_fix_block("")
        assert fixes == []


class TestConfidenceThresholds:
    def test_safe_threshold(self):
        assert CONFIDENCE_THRESHOLDS["safe"] == 95

    def test_all_threshold(self):
        assert CONFIDENCE_THRESHOLDS["all"] == 0


class TestSafeCategories:
    def test_safe_categories_defined(self):
        assert "type_hints" in SAFE_CATEGORIES
        assert "naming" in SAFE_CATEGORIES
        assert "null_check" in SAFE_CATEGORIES
