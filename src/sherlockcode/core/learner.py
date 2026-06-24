"""Learning system for SherlockCode - extracts patterns from git history."""

import json
import re
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional

from sherlockcode.providers.base import BaseProvider
from sherlockcode.core.git import get_repo_root


@dataclass
class StyleRules:
    """Coding style rules."""
    variables: str = "snake_case"
    functions: str = "snake_case"
    classes: str = "PascalCase"
    constants: str = "UPPER_SNAKE_CASE"
    indent: int = 4
    max_line_length: int = 100
    quote_style: str = "double"


@dataclass
class BugPattern:
    """A bug pattern found in the codebase."""
    pattern_id: str
    description: str
    example_before: str = ""
    example_after: str = ""
    frequency: int = 1


@dataclass
class DesignPattern:
    """A design pattern found in the codebase."""
    pattern_id: str
    description: str
    usage_count: int = 1


@dataclass
class KnowledgeBase:
    """Collected knowledge from the codebase."""
    style_rules: StyleRules = field(default_factory=StyleRules)
    bug_patterns: list[BugPattern] = field(default_factory=list)
    design_patterns: list[DesignPattern] = field(default_factory=list)
    conventions: list[str] = field(default_factory=list)
    last_updated: str = ""


class Learner:
    """Analyzes git history and code patterns to build a knowledge base."""

    def __init__(self, path: Optional[Path] = None):
        self.path = path
        self.repo_root = get_repo_root(path) if path else Path.cwd()
        self.knowledge_dir = self.repo_root / ".sherlock" / "knowledge"
        self.knowledge_file = self.knowledge_dir / "knowledge.json"

    def _ensure_knowledge_dir(self):
        """Create knowledge directory if it doesn't exist."""
        self.knowledge_dir.mkdir(parents=True, exist_ok=True)

    def _load_existing_knowledge(self) -> KnowledgeBase:
        """Load existing knowledge base if it exists."""
        if self.knowledge_file.exists():
            try:
                with open(self.knowledge_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                style_rules = StyleRules(**data.get("style_rules", {}))
                bug_patterns = [BugPattern(**p) for p in data.get("bug_patterns", [])]
                design_patterns = [DesignPattern(**p) for p in data.get("design_patterns", [])]

                return KnowledgeBase(
                    style_rules=style_rules,
                    bug_patterns=bug_patterns,
                    design_patterns=design_patterns,
                    conventions=data.get("conventions", []),
                    last_updated=data.get("last_updated", ""),
                )
            except (json.JSONDecodeError, TypeError):
                pass

        return KnowledgeBase()

    def _save_knowledge(self, knowledge: KnowledgeBase):
        """Save knowledge base to file."""
        self._ensure_knowledge_dir()
        knowledge.last_updated = datetime.now().isoformat()

        with open(self.knowledge_file, "w", encoding="utf-8") as f:
            json.dump(asdict(knowledge), f, indent=2, ensure_ascii=False)

    def learn_from_provider(
        self,
        provider: BaseProvider,
        since: Optional[str] = None,
        max_commits: int = 500,
    ) -> KnowledgeBase:
        """Learn patterns using an LLM provider.

        Args:
            provider: LLM provider for pattern analysis
            since: Start date for learning (e.g., "2024-01-01")
            max_commits: Maximum number of commits to analyze

        Returns:
            KnowledgeBase with extracted patterns
        """
        # Get git history
        from sherlockcode.core.git import _run_git

        args = ["log", "--format=%H %s", f"-{max_commits}"]
        if since:
            args.insert(2, f"--since={since}")

        try:
            log_output = _run_git(args, cwd=self.repo_root)
        except Exception:
            log_output = ""

        # Build analysis prompt
        prompt = self._build_analysis_prompt(log_output)

        # Get LLM response
        response = provider.generate(prompt)

        # Parse response
        knowledge = self._parse_llm_response(response)

        # Merge with existing knowledge
        existing = self._load_existing_knowledge()
        merged = self._merge_knowledge(existing, knowledge)

        # Save
        self._save_knowledge(merged)

        return merged

    def _build_analysis_prompt(self, git_log: str) -> str:
        """Build analysis prompt from git log."""
        template_path = Path(__file__).parent.parent / "prompts" / "learn_pattern_extraction.md"
        template = template_path.read_text(encoding="utf-8") if template_path.exists() else ""

        return f"""{template}

## Git Commit History

```
{git_log[:5000]}
```

## Analysis

Analyze the commit messages and identify patterns in the codebase.
"""

    def _parse_llm_response(self, response: str) -> KnowledgeBase:
        """Parse LLM response into KnowledgeBase."""
        # Try to extract JSON from response
        json_match = re.search(r'\{[\s\S]*"style_rules"[\s\S]*\}', response)

        if json_match:
            try:
                data = json.loads(json_match.group())
                style_rules = StyleRules(**data.get("style_rules", {}))
                bug_patterns = [BugPattern(**p) for p in data.get("bug_patterns", [])]
                design_patterns = [DesignPattern(**p) for p in data.get("design_patterns", [])]

                return KnowledgeBase(
                    style_rules=style_rules,
                    bug_patterns=bug_patterns,
                    design_patterns=design_patterns,
                    conventions=data.get("conventions", []),
                )
            except (json.JSONDecodeError, TypeError):
                pass

        return KnowledgeBase()

    def _merge_knowledge(self, existing: KnowledgeBase, new: KnowledgeBase) -> KnowledgeBase:
        """Merge new knowledge with existing knowledge."""
        # Update style rules
        if new.style_rules.variables != "snake_case":
            existing.style_rules = new.style_rules

        # Merge bug patterns
        for new_pattern in new.bug_patterns:
            found = False
            for existing_pattern in existing.bug_patterns:
                if existing_pattern.pattern_id == new_pattern.pattern_id:
                    existing_pattern.frequency += new_pattern.frequency
                    found = True
                    break
            if not found:
                existing.bug_patterns.append(new_pattern)

        # Merge design patterns
        for new_pattern in new.design_patterns:
            found = False
            for existing_pattern in existing.design_patterns:
                if existing_pattern.pattern_id == new_pattern.pattern_id:
                    existing_pattern.usage_count += new_pattern.usage_count
                    found = True
                    break
            if not found:
                existing.design_patterns.append(new_pattern)

        # Merge conventions
        for conv in new.conventions:
            if conv not in existing.conventions:
                existing.conventions.append(conv)

        return existing

    def get_knowledge(self) -> KnowledgeBase:
        """Get the current knowledge base."""
        return self._load_existing_knowledge()

    def reset(self):
        """Reset all learned knowledge."""
        if self.knowledge_file.exists():
            self.knowledge_file.unlink()

    def export(self, path: Optional[Path] = None) -> str:
        """Export knowledge to a file."""
        knowledge = self._load_existing_knowledge()
        export_path = path or self.knowledge_file

        with open(export_path, "w", encoding="utf-8") as f:
            json.dump(asdict(knowledge), f, indent=2, ensure_ascii=False)

        return str(export_path)

    def get_stats(self) -> dict:
        """Get learning statistics."""
        knowledge = self._load_existing_knowledge()
        return {
            "last_updated": knowledge.last_updated,
            "bug_patterns_count": len(knowledge.bug_patterns),
            "design_patterns_count": len(knowledge.design_patterns),
            "conventions_count": len(knowledge.conventions),
            "total_patterns": len(knowledge.bug_patterns) + len(knowledge.design_patterns),
        }
