"""Tests for the learner module."""

import pytest

from sherlockcode.core.learner import (
    Learner,
    KnowledgeBase,
    StyleRules,
    BugPattern,
    DesignPattern,
)


class TestStyleRules:
    def test_default_style_rules(self):
        rules = StyleRules()
        assert rules.variables == "snake_case"
        assert rules.functions == "snake_case"
        assert rules.classes == "PascalCase"
        assert rules.indent == 4


class TestBugPattern:
    def test_create_bug_pattern(self):
        pattern = BugPattern(
            pattern_id="null_check",
            description="Missing null check",
            frequency=5,
        )
        assert pattern.pattern_id == "null_check"
        assert pattern.frequency == 5


class TestDesignPattern:
    def test_create_design_pattern(self):
        pattern = DesignPattern(
            pattern_id="di",
            description="Dependency Injection",
            usage_count=3,
        )
        assert pattern.pattern_id == "di"
        assert pattern.usage_count == 3


class TestKnowledgeBase:
    def test_default_knowledge_base(self):
        kb = KnowledgeBase()
        assert kb.bug_patterns == []
        assert kb.design_patterns == []
        assert kb.conventions == []
        assert kb.style_rules is not None

    def test_knowledge_base_with_data(self):
        kb = KnowledgeBase(
            style_rules=StyleRules(variables="camelCase"),
            bug_patterns=[
                BugPattern(pattern_id="test", description="test")
            ],
        )
        assert kb.style_rules.variables == "camelCase"
        assert len(kb.bug_patterns) == 1


class TestLearner:
    def test_learner_initialization(self, tmp_path):
        import subprocess
        repo = tmp_path / "repo"
        repo.mkdir()
        subprocess.run(["git", "init"], cwd=repo, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=repo, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, capture_output=True)

        learner = Learner(repo)
        assert learner.repo_root == repo

    def test_get_stats(self, tmp_path):
        import subprocess
        repo = tmp_path / "repo"
        repo.mkdir()
        subprocess.run(["git", "init"], cwd=repo, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=repo, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, capture_output=True)

        learner = Learner(repo)
        stats = learner.get_stats()
        assert "bug_patterns_count" in stats
        assert "design_patterns_count" in stats
