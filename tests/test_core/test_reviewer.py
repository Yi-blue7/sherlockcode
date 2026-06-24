"""Tests for the review engine."""

import subprocess

from sherlockcode.core.reviewer import (
    ReviewResult,
    review_code,
    build_review_prompt,
    load_prompt_template,
    parse_review_response,
)
from sherlockcode.providers.base import BaseProvider


class DummyProvider(BaseProvider):
    def _call_api(self, prompt: str, **kwargs) -> str:
        return """### Issues Found

🟡 **medium** - `test.py:2` - readability
Variable name 'x' is not descriptive.
Suggest: Rename to 'user_count'.

### Summary

Overall good code with minor readability issues."""


class TestLoadPromptTemplate:
    def test_loads_default_template(self):
        template = load_prompt_template("default")
        assert "senior software engineer" in template.lower()

    def test_loads_security_template(self):
        template = load_prompt_template("security")
        assert "security engineer" in template.lower()

    def test_unknown_persona_returns_default(self):
        template = load_prompt_template("nonexistent")
        assert "senior software engineer" in template.lower()


class TestBuildReviewPrompt:
    def test_includes_diff_and_structure(self):
        prompt = build_review_prompt(
            diff="+print('hello')",
            changed_files=["main.py"],
            file_contents={"main.py": "print('hello')"},
            project_structure="main.py\n",
            persona="default",
        )
        assert "+print('hello')" in prompt
        assert "main.py" in prompt


class TestParseReviewResponse:
    def test_parses_issues(self):
        response = """### Issues Found

🔴 **high** - `auth.py:10` - security
Hardcoded API key found.
Suggest: Use environment variable.

🟡 **medium** - `utils.py:5` - performance
Inefficient loop.
Suggest: Use list comprehension.

### Summary

Code needs security fixes."""
        issues = parse_review_response(response)
        assert len(issues) == 2
        assert issues[0].severity == "high"
        assert issues[0].file == "auth.py"
        assert issues[0].line == "10"
        assert issues[0].category == "security"
        assert issues[1].severity == "medium"

    def test_parses_empty_response(self):
        issues = parse_review_response("")
        assert issues == []


class TestReviewCode:
    def test_review_returns_result(self, tmp_path):
        repo = tmp_path / "repo"
        repo.mkdir()
        subprocess.run(["git", "init"], cwd=repo, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=repo, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, capture_output=True)
        (repo / "test.py").write_text("def main():\n    x = 1\n")
        subprocess.run(["git", "add", "test.py"], cwd=repo, capture_output=True)
        subprocess.run(["git", "commit", "-m", "init"], cwd=repo, capture_output=True)
        (repo / "test.py").write_text("def main():\n    x = 1\n    print(x)\n")

        provider = DummyProvider(api_key="test", model="test")
        result = review_code(provider, path=repo)
        assert isinstance(result, ReviewResult)
        assert len(result.issues) == 1
        assert result.issues[0].category == "readability"
