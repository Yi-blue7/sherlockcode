# SherlockCode

> AI-powered code review tool - find bugs, fix code, learn patterns.

[![PyPI version](https://badge.fury.io/py/sherlockcode.svg)](https://badge.fury.io/py/sherlockcode)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

## Features

- **AI-Powered Review** - Get intelligent code reviews powered by Claude or GPT-4
- **Auto-Fix** - Automatically fix common issues with safety validation
- **Learning System** - Learn from your git history to understand project patterns
- **Multi-Model Support** - Use Claude, OpenAI, or local models
- **Rich Terminal Output** - Beautiful colored output in terminal
- **GitHub Action** - Integrate into your CI/CD pipeline

## Quick Start

```bash
# Install
pip install sherlockcode

# Initialize in your project
sherlock config init

# Review your changes
sherlock review

# Auto-fix issues
sherlock fix --preview  # Preview fixes
sherlock fix --apply    # Apply fixes

# Learn from your codebase
sherlock learn
sherlock learn --stats   # View learned patterns
```

## Commands

### `sherlock review`

Review code changes using AI.

```bash
sherlock review                      # Review unstaged changes
sherlock review --diff HEAD~3        # Review last 3 commits
sherlock review --persona security   # Security-focused review
sherlock review --output markdown    # Markdown output
```

### `sherlock fix`

Auto-fix code issues.

```bash
sherlock fix --preview               # Preview fixes (default)
sherlock fix --apply                 # Apply fixes
sherlock fix --safe                  # Only high-confidence fixes (default)
sherlock fix --all                   # Apply all fixes
```

### `sherlock learn`

Learn patterns from your git history.

```bash
sherlock learn                       # Learn from recent commits
sherlock learn --since 2024-01-01   # Learn since date
sherlock learn --stats               # View learned patterns
sherlock learn --export patterns.json
```

## Configuration

Create `.sherlockconfig.yml` in your project root:

```yaml
provider:
  default: claude
  models:
    claude:
      api_key: ${CLAUDE_API_KEY}
      model: claude-3-5-sonnet-20241022
    openai:
      api_key: ${OPENAI_API_KEY}
      model: gpt-4o

review:
  persona: default
  max_files: 50

fix:
  mode: safe
  backup: true

learn:
  enabled: true
```

Or use environment variables:
- `CLAUDE_API_KEY` - Anthropic API key
- `OPENAI_API_KEY` - OpenAI API key

## GitHub Action

Add to your workflow:

```yaml
name: Code Review
on: [pull_request]

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.10"
      - run: pip install sherlockcode
      - run: sherlock review --output github
        env:
          CLAUDE_API_KEY: ${{ secrets.CLAUDE_API_KEY }}
```

## Persona System

Choose a review persona:

| Persona | Focus |
|---------|-------|
| `default` | Comprehensive review |
| `security` | Security vulnerabilities |
| `performance` | Performance issues |
| `architect` | Architecture and design |
| `readability` | Code clarity |

## Comparison

| Feature | SherlockCode | CodeRabbit | ReviewDog |
|---------|-------------|------------|-----------|
| Open Source | ✅ | ❌ | ✅ |
| Auto Fix | ✅ | ❌ | ❌ |
| Learning | ✅ | ❌ | ❌ |
| Multi-Model | ✅ | ❌ | ❌ |
| Free Tier | ✅ | ❌ | ✅ |

## Development

```bash
# Clone
git clone https://github.com/yourusername/sherlockcode.git
cd sherlockcode

# Install in dev mode
pip install -e ".[dev]"

# Run tests
pytest tests/ -v
```

## License

MIT License - see [LICENSE](LICENSE) for details.

---

Made with ❤️ for developers who care about code quality.
# Test v2
