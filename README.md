# retrocode

A comprehensive testing framework for validating AI instruction files (like `CLAUDE.md` and `AGENTS.md`) through automated backtesting. Run your instructions through realistic tasks and verify that the AI agent follows your guidelines.

## Why retrocode?

When you modify instruction files, you need confidence that:
- Your rules are still being followed
- Agent behavior hasn't regressed
- New guidelines improve performance

Traditional unit tests don't work for instruction files because outputs are non-deterministic. This framework instead provides:

1. **Multiple assertion types** - From simple regex checks to LLM-as-judge evaluations
2. **Comprehensive scoring** - Track behavioral improvements across versions
3. **pytest integration** - Run tests like any other test suite
4. **Isolated Sandboxes** - Run code in secure E2B sandboxes

## Architecture

The system is built on proven patterns from DSPy, promptfoo, and OpenAI Evals:

```
YAML Test Files
    ↓
Parser → TestSuite Objects
    ↓
Agent Invoker → Responses
    ↓
Assertion Evaluators (Deterministic + LLM Judge)
    ↓
Results
    ↓
Reports (Markdown, HTML)
```

## Installation

```bash
git clone https://github.com/your-org/retrocode
cd retrocode
uv sync
```

## Quick Start

### 1. Write a Test File

Create `tests/backtests/my_rules.backtest.yaml`:

```yaml
name: "My Custom Rules"
description: "Validate my instruction changes"
instructions_version: "main"
model_under_test: "claude-3-5-sonnet-20250109"
metadata:
  instruction_file: "/path/to/CLAUDE.md"

test_cases:
  - description: "Should use uv for package management"
    task: "Create a Python project for data processing"
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

      - type: llm_judge
        target: full_response
        description: "Overall approach is modern"
        severity: warning
        metadata:
          judge_prompt: "Is this using modern Python tooling?"
          threshold: 0.7
```

### 2. Run Tests

```bash
# Run all tests
retrocode run --tests tests/backtests

# Generate HTML report
retrocode run --tests tests/backtests --html report.html

# List available tests
retrocode list-tests
```

### 3. Use with pytest

```bash
# Run as pytest tests
pytest tests/backtests/

# Run specific test
pytest tests/backtests/my_rules.backtest.yaml -k "uv"

# Run with verbose output
pytest tests/backtests/ -vv
```

## Assertion Types

### 1. Deterministic Assertions

**`must_contain`** - Check if text is present
```yaml
assertions:
  - type: must_contain
    target: generated_commands
    pattern: "rg"  # Must use ripgrep
```

**`must_not_contain`** - Check if text is absent
```yaml
assertions:
  - type: must_not_contain
    target: generated_code
    pattern: "sys.path"  # Don't modify sys.path
```

**`regex_match`** - Regex pattern matching
```yaml
assertions:
  - type: regex_match
    target: full_response
    pattern: "def\s+\w+\([^)]*:\s*\w+\)"  # Type hints
```

**`json_schema`** - Validate JSON structure
```yaml
assertions:
  - type: json_schema
    target: generated_code
    metadata:
      schema:
        type: object
        properties:
          name: { type: string }
        required: [name]
```

### 2. Code Analysis Assertions

**`code_analysis`** - Static analysis of generated code
```yaml
assertions:
  - type: code_analysis
    metadata:
      validator: "python_type_check"  # Built-in validators
      # Options: python_type_check, docstring_check, no_bash_find, no_sys_path_modify
```

**Snapshot Testing** - Compare against known-good output
```yaml
assertions:
  - type: snapshot
    metadata:
      snapshot_name: "data_processor_v1"
      fields: ["generated_code", "generated_commands"]
```

### 3. LLM-as-Judge Assertions

Use another Claude to evaluate behavioral rules:

```yaml
assertions:
  - type: llm_judge
    target: full_response
    metadata:
      judge_prompt: |
        Evaluate if the code follows SOLID principles.
        Respond with JSON: {"score": 0-1, "reasoning": "..."}
      threshold: 0.8  # Minimum score required
      response_schema: {}  # Optional: enforce response format
```

**Judge Results:**
- Cached automatically (SQLite) - Same response won't be re-judged
- Configurable score thresholds
- Supports custom judge prompts
- Structured JSON output validation

## Test Targets

Each assertion can target different parts of the response:

- `full_response` - Entire agent response (default)
- `generated_code` - Python code blocks
- `generated_commands` - Shell commands
- `tool_calls` - API calls made by agent

```yaml
assertions:
  - type: must_contain
    target: generated_code  # Only check code blocks
    pattern: "class "
```

## Assertion Severity

Control whether failures block the test:

```yaml
assertions:
  - type: must_contain
    pattern: "important"
    severity: error    # Test fails if violated (default)

  - type: regex_match
    pattern: "optional_pattern"
    severity: warning  # Just a warning, test still passes
```


## Example Test Suites

See `tests/backtests/` for complete examples:

- **`tool_usage.backtest.yaml`** - Tool selection rules (uv, rg, fd, etc.)
- **`code_quality.backtest.yaml`** - Type hints, docstrings, OOP design
- **`behavioral_rules.backtest.yaml`** - Testing, error handling, workflows

## Advanced Features

### Custom Code Analyzers

Register custom validators:

```python
from retrocode.code_analysis import CodeAnalyzer, CodeAnalysisRegistry

class MyValidator(CodeAnalyzer):
    def analyze(self, assertion, response):
        # Custom validation logic
        return AssertionResult(passed=True, message="OK")

CodeAnalysisRegistry.register("my_validator", MyValidator)
```

### Direct Python Usage

```python
from retrocode.runner import TestRunner
from retrocode.parser import YAMLTestParser
from retrocode.reporting import HTMLReporter

# Parse tests
test_suites = YAMLTestParser.parse_directory("tests/backtests")

# Run tests
runner = TestRunner()
results = runner.run_suites(test_suites)

# Generate report
HTMLReporter.save(results, "report.html")
```

## Performance Tuning

### LLM Judge Caching

Judge results are cached automatically in SQLite:

```python
from retrocode.cache import JudgeCache

cache = JudgeCache()
cache.cleanup_expired()  # Remove expired entries
cache.clear()  # Clear all cache
```

### Parallel Test Execution

Run tests in pytest parallel mode:

```bash
pip install pytest-xdist
pytest tests/backtests/ -n auto
```

## Troubleshooting

**Tests are slow:** LLM judge calls take 1-2s. Cached results are instant. Use `severity: warning` for non-critical tests.

**Judge results are flaky:** Judge uses `temperature: 0` for determinism. Adjust `threshold` or judge prompt if needed.

**pytest doesn't discover tests:** Ensure `.backtest.yaml` naming and check `pyproject.toml` pytest config.

## FAQ

**Q: How much does this cost?** Judge calls cost ~$0.001-0.01 per test. Budget $10-20 for comprehensive backtesting.

**Q: Can I use different models?** Yes! Set `model_under_test` in YAML.

**Q: What if I don't want LLM judge?** Use only deterministic assertions.

## License

MIT
