# AI Backtest

Test instruction files like `CLAUDE.md` and `AGENTS.md` through automated backtesting. Validate that AI agent behavior follows your guidelines and detect regressions before deployment.

## Why AI Backtest?

When you modify instruction files, you need confidence that:

- ✅ Your rules are still being followed
- ✅ Agent behavior hasn't regressed
- ✅ New guidelines improve performance

Traditional unit tests don't work for instruction files because outputs are non-deterministic. **AI Backtest** provides a rigorous framework for testing instruction changes:

## Key Features

- **Multiple Assertion Types** - From simple pattern checks to LLM-as-judge evaluations
- **Regression Detection** - Compare against baseline to catch breaking changes
- **Comprehensive Scoring** - Track behavioral improvements across versions
- **pytest Integration** - Run tests like any other test suite
- **CI/CD Ready** - GitHub Actions workflow included
- **Production Grade** - Fully typed Python, comprehensive error handling

## The Framework

Built on proven patterns from DSPy, promptfoo, OpenAI Evals, and finance backtesting:

```
Historical PRs (Test Cases)
        ↓
[New Configuration]
        ↓
Agent Invocation → Responses
        ↓
Multi-Type Assertions
  ├─ Deterministic (regex, string matching)
  ├─ Code Analysis (AST, type hints, docstrings)
  ├─ LLM-as-Judge (behavioral rules with caching)
  └─ Snapshots (generated code comparison)
        ↓
Multi-Tier Diff Scoring
  ├─ Exact Match (100%)
  ├─ Semantic Match (80%)
  ├─ Functional Match (60%)
  ├─ Partial Match (30%)
  └─ No Match (0%)
        ↓
Results & Regression Reports
```

## Quick Start

### 1. Write a Test

Create `tests/backtests/my_rules.backtest.yaml`:

```yaml
name: "My Rules"
description: "Validate my instructions"
instructions_version: "main"
metadata:
  instruction_file: "/path/to/CLAUDE.md"

test_cases:
  - description: "Should use uv for package management"
    task: "Create a Python project"
    assertions:
      - type: must_contain
        target: generated_commands
        description: "Mentions uv"
        pattern: "uv"
        severity: error
      - type: must_not_contain
        target: generated_commands
        description: "Doesn't use pip"
        pattern: "pip install"
        severity: error
```

### 2. Run Tests

```bash
# Via pytest
pytest tests/backtests/

# Via CLI
ai-backtest run --tests tests/backtests --html report.html

# List all tests
ai-backtest list-tests
```

### 3. Detect Regressions

```bash
# Run baseline
ai-backtest run --tests tests/backtests --output baseline.json

# Make changes to your instructions...

# Run candidate
ai-backtest run --tests tests/backtests --output candidate.json

# Compare
ai-backtest compare --baseline baseline.json --candidate candidate.json
```

## Core Concepts

### Assertion Types

Test different aspects of agent behavior:

- **Deterministic**: Pattern matching, string containment
- **Code Analysis**: Type hints, docstrings, complexity
- **LLM Judge**: Behavioral rules ("Does this follow SOLID principles?")
- **Snapshots**: Compare against known-good outputs

### Multi-Tier Diff Scoring

Evaluates generated code fairly:

| Score | Meaning |
|-------|---------|
| 100% | Exact reproduction of expected change |
| 80% | Same intent, different style |
| 60% | Solves problem, different approach |
| 30% | Shows understanding but incomplete |
| 0% | Fundamentally wrong approach |

### Finance Backtesting Analogy

Think of it like backtesting trading strategies:

| Finance | Code Generation |
|---------|-----------------|
| Strategy | Configuration (MCP, AGENTS.md, prompts) |
| Historical trades | Historical PRs |
| Performance metrics | Code quality (Pass@k, CodeBLEU) |
| Curve fitting risk | Overfitting to specific PR types |

## What You'll Learn

This documentation covers:

- **Getting Started** - Installation and first test
- **Writing Tests** - YAML format, test structure, best practices
- **Assertions** - All 7 types with real examples
- **Advanced Features** - Custom validators, LLM judge tuning, caching
- **CI/CD Integration** - GitHub Actions, PR validation, reports
- **Python API** - Programmatic test execution
- **Research & Design** - Naming decisions, architectural patterns, diff scoring

## Built With

- **Pydantic** - Type-safe configuration
- **YAML** - Human-readable test format
- **pytest** - Familiar test execution
- **SQLite** - Judge result caching
- **Anthropic Claude** - As test executor and judge
- **Click** - CLI interface

## Architecture

Built on proven patterns from:

- **Promptfoo** (YAML tests, GitHub Actions)
- **DSPy** (Assertion framework, optimization)
- **Evidently** (LLM evaluation in CI/CD)
- **HumanEval** (Pass@k metrics)
- **Finance backtesting** (Methodology, statistical rigor)
- **SWE-bench/RepoBench** (Historical PR mining)

## Next Steps

→ **[Get Started](getting-started.md)** - Installation and your first test

→ **[Write Tests](guides/writing-tests.md)** - Complete YAML format guide

→ **[Research](research/inspirations.md)** - See architectural patterns and design decisions

## License

MIT - See [LICENSE](https://github.com/GeorgePearse/ai-backtest/blob/main/LICENSE)

## Contributing

Contributions welcome! Please ensure:

- All code has type hints and docstrings
- Tests cover new functionality
- Pre-commit hooks pass

See [CONTRIBUTING.md](https://github.com/GeorgePearse/ai-backtest/blob/main/CONTRIBUTING.md)
