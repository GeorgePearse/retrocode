# Assertion Types Reference

Complete reference for all 10 assertion types supported by evaluator.

## Overview

Assertions validate different aspects of agent responses:

| Type | Purpose | Use Case |
|------|---------|----------|
| `must_contain` | String presence | Tool usage, required patterns |
| `must_not_contain` | String absence | Forbidden patterns, anti-patterns |
| `regex_match` | Pattern matching | Complex requirements, format validation |
| `json_schema` | Structure validation | API responses, structured output |
| `code_analysis` | Static code analysis | Type hints, docstrings, code quality |
| `llm_judge` | Subjective evaluation | Behavioral rules, clarity, helpfulness |
| `snapshot` | Output comparison | Regression detection, stability |
| `pr_match` | PR comparison | Match against GitHub PR changes |
| `code_contains` | Required code patterns | Ensure specific code is present |
| `code_excludes` | Forbidden code patterns | Prevent dangerous/unwanted code |

## 1. must_contain

Check if generated output contains a required string.

### Basic Example

```yaml
assertions:
  - type: must_contain
    description: "Must mention the tool we recommend"
    pattern: "rg"  # ripgrep
    severity: error
```

### With Target

```yaml
assertions:
  - type: must_contain
    target: generated_commands      # Only check shell commands
    pattern: "uv"                   # Must use uv
    severity: error
    description: "Should use uv package manager"
```

### Multiple Required Patterns

Create separate assertions:

```yaml
assertions:
  - type: must_contain
    pattern: "def "
    description: "Should define a function"

  - type: must_contain
    pattern: "return"
    description: "Should have a return statement"
```

### Common Targets

- `full_response` (default) - Entire response text
- `generated_code` - Python code blocks only
- `generated_commands` - Shell commands only
- `tool_calls` - API calls made by agent

## 2. must_not_contain

Check that output does NOT contain forbidden strings.

### Basic Example

```yaml
assertions:
  - type: must_not_contain
    pattern: "pip install"
    description: "Should not use pip"
    severity: error
```

### Real-World Example

```yaml
assertions:
  - type: must_not_contain
    target: generated_code
    pattern: "sys.path"
    description: "Should not modify sys.path"
    severity: error

  - type: must_not_contain
    target: generated_commands
    pattern: "find "
    description: "Should use fd instead of find"
    severity: error
```

### Anti-Pattern Detection

```yaml
assertions:
  - type: must_not_contain
    pattern: "# TODO"
    description: "Should not have TODOs in production code"
    severity: warning

  - type: must_not_contain
    pattern: "except:"
    description: "Bare except is bad practice"
    severity: warning
```

## 3. regex_match

Match against regex patterns (full regex syntax supported).

### Basic Example

```yaml
assertions:
  - type: regex_match
    pattern: "def\s+\w+\("
    description: "Should define at least one function"
    severity: error
```

### Type Hint Validation

```yaml
assertions:
  - type: regex_match
    target: generated_code
    pattern: "def\s+\w+\([^)]*:\s*\w+\)[^:]*->\s*\w+"
    description: "Functions should have type hints"
    severity: error
```

### Docstring Validation

```yaml
assertions:
  - type: regex_match
    target: generated_code
    pattern: '""".*"""'
    description: "Classes should have docstrings"
    severity: error
```

### Multi-line Matching

Use flags for complex patterns:

```yaml
assertions:
  - type: regex_match
    pattern: 'class\s+\w+:.*?def\s+__init__'
    description: "Classes should have __init__ method"
    severity: error
```

## 4. json_schema

Validate that JSON output matches a schema.

### Basic Example

```yaml
assertions:
  - type: json_schema
    target: generated_code    # Target must contain valid JSON
    description: "Output should be valid JSON"
    metadata:
      schema:
        type: object
        properties:
          name:
            type: string
          age:
            type: integer
        required: [name, age]
```

### Complex Schema

```yaml
assertions:
  - type: json_schema
    description: "API response structure validation"
    metadata:
      schema:
        type: object
        properties:
          status:
            type: string
            enum: [success, error]
          data:
            type: object
            properties:
              users:
                type: array
                items:
                  type: object
                  properties:
                    id:
                      type: integer
                    email:
                      type: string
                      format: email
```

## 5. code_analysis

Run static analysis on generated code.

### Available Validators

#### python_type_check
```yaml
assertions:
  - type: code_analysis
    metadata:
      validator: "python_type_check"
    severity: error
    description: "All functions must have type hints"
```

Checks for:
- Function return type hints
- Parameter type annotations
- Missing annotations

#### docstring_check
```yaml
assertions:
  - type: code_analysis
    metadata:
      validator: "docstring_check"
    severity: error
    description: "All classes and functions must have docstrings"
```

Checks for:
- Function docstrings
- Class docstrings
- Module docstrings

#### no_bash_find
```yaml
assertions:
  - type: code_analysis
    metadata:
      validator: "no_bash_find"
    severity: error
    description: "Should not use bash 'find' command"
```

Prevents:
- `find` command usage
- Recommends using `fd` instead

#### no_sys_path_modify
```yaml
assertions:
  - type: code_analysis
    metadata:
      validator: "no_sys_path_modify"
    severity: error
    description: "Should not modify sys.path"
```

Prevents:
- `sys.path.append()`
- `sys.path.insert()`
- `sys.path.extend()`

## 6. llm_judge

Use Claude to evaluate subjective aspects.

### Basic Example

```yaml
assertions:
  - type: llm_judge
    description: "Code is well-structured"
    severity: warning  # Non-blocking
    metadata:
      judge_prompt: "Is this code well-structured and readable?"
      threshold: 0.7   # Score must be >= 0.7
```

### Custom Evaluation

```yaml
assertions:
  - type: llm_judge
    description: "Follows SOLID principles"
    metadata:
      judge_prompt: |
        Evaluate if this code follows SOLID principles:
        - Single Responsibility Principle
        - Open/Closed Principle
        - Liskov Substitution
        - Interface Segregation
        - Dependency Inversion

        Score from 0-1 and explain reasoning.
        Respond as JSON: {"score": 0.0-1.0, "reasoning": "..."}
      threshold: 0.8
```

### Advanced Options

```yaml
assertions:
  - type: llm_judge
    target: full_response
    metadata:
      judge_prompt: "Is this explanation clear?"
      threshold: 0.7
      response_schema:      # Enforce JSON structure
        type: object
        properties:
          score:
            type: number
            minimum: 0
            maximum: 1
          reasoning:
            type: string
```

### Performance Notes

- Judge calls are **cached** by default
- First call: 1-2 seconds
- Cached results: instant
- Budget ~$0.01 per test for judge calls

### Custom Judge Prompts

Good judge prompts:

✅ **Specific and measurable:**
```
Does this explain REST APIs clearly?
Consider: accuracy, examples, simplicity.
```

❌ **Vague:**
```
Is this good?
```

✅ **Request structured output:**
```
Respond with JSON: {"score": 0-1, "reasoning": "..."}
```

❌ **Open-ended:**
```
Tell me about the quality
```

## 7. snapshot

Compare generated output against previously saved snapshots.

### First Run (Create Snapshot)

```yaml
assertions:
  - type: snapshot
    metadata:
      snapshot_name: "api_example_v1"
      fields: ["generated_code"]
    description: "API example output should be consistent"
```

First run automatically creates the snapshot at `.snapshots/api_example_v1.snapshot.json`.

### Subsequent Runs (Compare)

Same assertion will compare new output against the snapshot. If they match, test passes.

### Update Snapshot

```bash
# Update all snapshots to current output
evaluator run --update-snapshots --tests tests/backtests/
```

### Multiple Fields

```yaml
assertions:
  - type: snapshot
    metadata:
      snapshot_name: "full_example"
      fields:
        - "full_response"
        - "generated_code"
        - "generated_commands"
    description: "Complete example should be reproducible"
```

### Use Cases

- **Regression detection**: Catch unexpected changes
- **Output stability**: Ensure consistent outputs
- **Reviewing changes**: Easy diff when updating instructions

## 8. pr_match

Compare generated code against a GitHub PR's changes.

### Basic Example

```yaml
assertions:
  - type: pr_match
    description: "Should match PR #456 implementation"
    metadata:
      pr_reference: "GeorgePearse/evaluator#456"
      match_level: "semantic"
      threshold: 0.75
    severity: error
```

### With Focus Files

Only compare specific files from the PR:

```yaml
assertions:
  - type: pr_match
    metadata:
      pr_reference: "owner/repo#123"
      match_level: "semantic"
      threshold: 0.75
      focus_files:
        - "src/auth.py"
        - "src/middleware.py"
    description: "Generated code should match PR #123 for auth modules"
```

### Match Levels

- **`exact`** - Character-for-character match (after whitespace normalization)
- **`semantic`** - AST-based comparison (same structure, different formatting)
- **`functional`** - LLM judge evaluates if code achieves same goal (expensive)

### Use Cases

- Validate against known-good implementations
- Ensure consistency with approved patterns
- Regression testing for instruction changes

## 9. code_contains

Ensure required code patterns are present.

### Basic Example

```yaml
assertions:
  - type: code_contains
    target: generated_code
    description: "Must implement authentication function"
    metadata:
      snippet: "def authenticate(user, password):"
      match_type: "exact"
      language: "python"
    severity: error
```

### Semantic Matching

Use AST-based comparison to allow different formatting:

```yaml
assertions:
  - type: code_contains
    target: generated_code
    metadata:
      snippet: |
        def verify_token(token: str) -> Optional[User]:
            payload = jwt.decode(token, SECRET_KEY)
            return User.get(payload['user_id'])
      match_type: "semantic"
      language: "python"
    description: "Must include JWT token verification"
```

### Regex Matching

Use regex for flexible pattern matching:

```yaml
assertions:
  - type: code_contains
    target: generated_code
    metadata:
      snippet: r"@app\.route\('/api/\w+'\)"
      match_type: "regex"
      language: "python"
    description: "Should define at least one API route"
```

### Match Types

- **`exact`** - Substring match (case-sensitive, whitespace-normalized)
- **`semantic`** - AST-based comparison for Python
- **`regex`** - Full regex pattern matching

## 10. code_excludes

Prevent dangerous or unwanted code patterns.

### Basic Example

```yaml
assertions:
  - type: code_excludes
    target: generated_code
    description: "Must not use dangerous functions"
    metadata:
      patterns:
        - r"eval\("
        - r"exec\("
        - r"__import__\("
      match_type: "regex"
    severity: error
```

### Security Best Practices

```yaml
assertions:
  - type: code_excludes
    target: generated_code
    metadata:
      patterns:
        - "eval("
        - "exec("
        - "os.system("
        - "subprocess.call"
        - "pickle.loads"
      match_type: "regex"
    description: "Must not use functions that execute arbitrary code"

  - type: code_excludes
    target: generated_code
    metadata:
      patterns:
        - "sys.path.append"
        - "sys.path.insert"
        - "__import__"
      match_type: "exact"
    description: "Must not modify Python internals"
```

### Architectural Patterns

```yaml
assertions:
  - type: code_excludes
    target: generated_code
    metadata:
      patterns:
        - r"from \w+ import \*"  # Wildcard imports
        - r"global \w+"          # Global variables
        - "# TODO"               # Unfinished code
      match_type: "regex"
    description: "Must follow code style guidelines"
```

### Multiple Patterns

Specify multiple patterns to check:

```yaml
assertions:
  - type: code_excludes
    target: generated_code
    metadata:
      patterns:
        - r"except\s*:"      # Bare except
        - r"\.strip\(\)"     # Unsafe string operations
        - "FIXME"            # Unresolved issues
      match_type: "regex"
    severity: warning  # Non-blocking
    description: "Code quality checks"
```

## Assertion Targets

Available for: `must_contain`, `must_not_contain`, `regex_match`, `code_analysis`, `code_contains`, `code_excludes`

| Target | Contains |
|--------|----------|
| `full_response` | Complete agent response |
| `generated_code` | Python/code blocks from response |
| `generated_commands` | Shell commands from response |
| `tool_calls` | API calls the agent made |

Example:

```yaml
assertions:
  - type: must_contain
    target: generated_code      # Only check code blocks
    pattern: "class "
    description: "Should define a class"
```

## Assertion Severity

Control whether failures block the test:

```yaml
assertions:
  - type: must_contain
    pattern: "critical_requirement"
    severity: error    # Test FAILS if violated (default)

  - type: llm_judge
    metadata:
      judge_prompt: "Nice to have"
    severity: warning  # Test PASSES even if violated
```

### Scoring with Severity

- **Error assertions**: Test passes only if ALL error assertions pass
- **Warning assertions**: Recorded but don't block test
- **Mix**: Test fails if any error fails, warnings are informational

## Combining Assertions

Multiple assertions on one test case:

```yaml
test_cases:
  - description: "Comprehensive API test"
    task: "Create a REST API endpoint"
    assertions:
      # Must have
      - type: must_contain
        pattern: "@app.route"
        severity: error

      # Should not have
      - type: must_not_contain
        pattern: "except:"
        severity: error

      # Code quality
      - type: code_analysis
        metadata:
          validator: "python_type_check"
        severity: error

      # Behavioral validation
      - type: llm_judge
        metadata:
          judge_prompt: "Is this RESTful?"
        severity: warning
```

## Best Practices

### ✅ DO

- **Be specific** in patterns and descriptions
- **Use error for critical** requirements
- **Use warning for nice-to-haves**
- **Layer assertions** (deterministic + subjective)
- **Cache judge results** for cost efficiency

### ❌ DON'T

- Use `must_contain` for multiple patterns (create separate assertions)
- Mix multiple requirements in one pattern
- Use vague judge prompts
- Forget to document why assertion exists
- Update snapshots without reviewing changes

## Examples

### Testing Tool Usage

```yaml
test_cases:
  - description: "Uses recommended tools"
    task: "Set up a Python project"
    assertions:
      - type: must_contain
        target: generated_commands
        pattern: "uv"

      - type: must_not_contain
        target: generated_commands
        pattern: "pip install"

      - type: regex_match
        target: generated_code
        pattern: "python -m venv"
```

### Testing Code Quality

```yaml
test_cases:
  - description: "Code meets quality standards"
    task: "Implement a data processor"
    assertions:
      - type: code_analysis
        metadata:
          validator: "python_type_check"

      - type: code_analysis
        metadata:
          validator: "docstring_check"

      - type: must_not_contain
        target: generated_code
        pattern: "# TODO"
```

### Testing Behavior

```yaml
test_cases:
  - description: "Helpful error messages"
    task: "What's wrong with my code?"
    assertions:
      - type: llm_judge
        metadata:
          judge_prompt: "Does this helpfully diagnose the issue?"
          threshold: 0.8

      - type: must_contain
        pattern: "error"
```

## Next Steps

- [Writing Tests](../guides/writing-tests.md) - Complete test format guide
- [Advanced Features](../guides/advanced.md) - Custom validators, caching
- [Examples](../examples/basic-test.md) - Real test suites
