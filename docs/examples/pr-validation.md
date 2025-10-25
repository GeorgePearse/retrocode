# PR-Based Validation Examples

Real-world examples of validating code against GitHub PRs using the `pr_match`, `code_contains`, and `code_excludes` assertion types.

## Example 1: Implementing Authentication

Test that generated authentication code matches a known-good PR implementation.

```yaml
name: "Authentication Feature"
description: "Validate JWT authentication implementation"
instructions_version: "main"
model_under_test: "claude-3-5-sonnet-20250109"
metadata:
  instruction_file: "/path/to/CLAUDE.md"

test_cases:
  - description: "JWT authentication implementation matches PR #456"
    task: "Add JWT-based authentication with token refresh"

    assertions:
      # 1. Compare against PR implementation
      - type: pr_match
        description: "Code matches PR #456 structure"
        metadata:
          pr_reference: "MyOrg/myapp#456"
          match_level: "semantic"
          threshold: 0.75
          focus_files:
            - "src/auth.py"
            - "src/middleware.py"
        severity: error

      # 2. Require specific security functions
      - type: code_contains
        target: generated_code
        description: "Must include JWT verification function"
        metadata:
          snippet: |
            def verify_jwt_token(token: str) -> dict:
                """Verify JWT token and extract claims."""
          match_type: "semantic"
          language: "python"
        severity: error

      # 3. Require type hints
      - type: code_contains
        target: generated_code
        description: "Functions must have return type hints"
        metadata:
          snippet: r"def \w+\([^)]*\)[^:]*-> \w+"
          match_type: "regex"
          language: "python"
        severity: error

      # 4. Prevent security issues
      - type: code_excludes
        target: generated_code
        description: "Must not hardcode secrets"
        metadata:
          patterns:
            - r"SECRET_KEY\s*=\s*['\"][^'\"]*['\"]"
            - r"password\s*=\s*['\"][^'\"]*['\"]"
            - r"token\s*=\s*['\"][^'\"]*['\"]"
          match_type: "regex"
        severity: error

      # 5. Prevent bad practices
      - type: code_excludes
        target: generated_code
        description: "Must not use insecure functions"
        metadata:
          patterns:
            - r"pickle\.loads"
            - r"eval\("
            - r"exec\("
          match_type: "regex"
        severity: error
```

## Example 2: REST API Endpoint

Validate REST API implementation against a PR with specific code requirements.

```yaml
name: "REST API Features"
description: "Validate REST endpoint implementations"
instructions_version: "main"
model_under_test: "claude-3-5-sonnet-20250109"

test_cases:
  - description: "Create user endpoint matches PR requirements"
    task: |
      Create a POST endpoint to create users.
      Should validate input, return 201 Created with the new user.

    assertions:
      # Validate against reference implementation
      - type: pr_match
        metadata:
          pr_reference: "team/api-service#123"
          match_level: "semantic"
          threshold: 0.8
          focus_files: ["src/endpoints/users.py"]
        description: "Implementation matches PR #123"
        severity: error

      # Ensure proper decorator
      - type: code_contains
        target: generated_code
        metadata:
          snippet: r'@app\.post\("/users"\)'
          match_type: "regex"
          language: "python"
        description: "Should use POST /users route"
        severity: error

      # Require input validation
      - type: code_contains
        target: generated_code
        metadata:
          snippet: "Pydantic"
          match_type: "exact"
          language: "python"
        description: "Should use Pydantic for validation"
        severity: error

      # Require proper error handling
      - type: code_contains
        target: generated_code
        metadata:
          snippet: r"except\s+\(.*Error.*\):"
          match_type: "regex"
          language: "python"
        description: "Should handle specific exceptions"
        severity: warning

      # Prevent common mistakes
      - type: code_excludes
        target: generated_code
        metadata:
          patterns:
            - r"except\s*:"              # Bare except
            - r"return\s+None"           # Implicit None returns
            - r"print\("                 # Debugging prints
          match_type: "regex"
        description: "Avoid common anti-patterns"
        severity: warning
```

## Example 3: Database Model

Test ORM model implementation against reference PR.

```yaml
name: "Database Models"
description: "Validate SQLAlchemy model implementations"
instructions_version: "main"
model_under_test: "claude-3-5-sonnet-20250109"

test_cases:
  - description: "User model matches database PR schema"
    task: |
      Create a SQLAlchemy User model with:
      - id (primary key)
      - email (unique, indexed)
      - password (hashed)
      - created_at (timestamp)
      - updated_at (timestamp)

      Include proper relationships and constraints.

    assertions:
      # Match against schema PR
      - type: pr_match
        metadata:
          pr_reference: "data-team/schemas#89"
          match_level: "semantic"
          threshold: 0.7
        description: "Model matches database schema PR"
        severity: error

      # Require SQLAlchemy imports
      - type: code_contains
        target: generated_code
        metadata:
          snippet: "from sqlalchemy import"
          match_type: "exact"
          language: "python"
        description: "Must use SQLAlchemy"
        severity: error

      # Require type hints on columns
      - type: code_contains
        target: generated_code
        metadata:
          snippet: r"Column\([^)]*String[^)]*\)"
          match_type: "regex"
          language: "python"
        description: "Should define String columns"
        severity: error

      # Ensure unique constraint on email
      - type: code_contains
        target: generated_code
        metadata:
          snippet: "unique=True"
          match_type: "exact"
          language: "python"
        description: "Email should be unique"
        severity: error

      # Prevent ORM anti-patterns
      - type: code_excludes
        target: generated_code
        metadata:
          patterns:
            - "autoincrement=False"  # Should use auto-increment
            - r"mutable\s*=\s*True"  # Mutable defaults are bad
            - r"pool_size\s*=\s*1"   # Connection pooling mistake
          match_type: "regex"
        description: "Avoid ORM anti-patterns"
        severity: warning
```

## Example 4: Configuration Validation

Ensure configuration matches security best practices PR.

```yaml
name: "Security Configuration"
description: "Validate security-related configuration"
instructions_version: "main"
model_under_test: "claude-3-5-sonnet-20250109"

test_cases:
  - description: "Environment configuration follows security PR"
    task: |
      Create a configuration module that:
      - Loads from environment variables
      - Uses sensible defaults
      - Validates required variables
      - Handles both dev and production

    assertions:
      # Match reference security config
      - type: pr_match
        metadata:
          pr_reference: "security-team/config-standards#202"
          match_level: "semantic"
          threshold: 0.75
        description: "Config matches security standards PR"
        severity: error

      # Require environment loading
      - type: code_contains
        target: generated_code
        metadata:
          snippet: r"os\.getenv\("
          match_type: "regex"
          language: "python"
        description: "Should load from environment"
        severity: error

      # Require validation
      - type: code_contains
        target: generated_code
        metadata:
          snippet: "assert"
          match_type: "exact"
          language: "python"
        description: "Should validate required settings"
        severity: error

      # Prevent hardcoding secrets
      - type: code_excludes
        target: generated_code
        metadata:
          patterns:
            - r"password\s*=\s*['\"]"
            - r"api_key\s*=\s*['\"]"
            - r"secret\s*=\s*['\"]"
            - r"token\s*=\s*['\"]"
          match_type: "regex"
        description: "Must not hardcode secrets"
        severity: error

      # Prevent other mistakes
      - type: code_excludes
        target: generated_code
        metadata:
          patterns:
            - "eval("
            - "exec("
            - "compile("
          match_type: "exact"
          language: "python"
        description: "Must not use code evaluation"
        severity: error
```

## Running the Examples

### First Example: Run against PR #456

```bash
# Run the authentication test
pytest docs/examples/pr-validation.md -v -k "JWT_authentication"

# With detailed output
pytest docs/examples/pr-validation.md::test_cases -v -s
```

### Generate Comparison Report

```bash
# Run tests and generate comparison against baseline
retrocode run --tests docs/examples/pr-validation.md --html report.html
```

### Continuous Integration

Add to `.github/workflows/validate-pr.yml`:

```yaml
- name: Validate against reference PRs
  run: pytest docs/examples/pr-validation.md -v
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

## Key Patterns

### 1. Progressive Validation

```yaml
assertions:
  # Must have (error severity)
  - type: pr_match
    metadata:
      pr_reference: "team/api#123"
      threshold: 0.8
    severity: error

  # Should have (warning severity)
  - type: code_contains
    metadata:
      snippet: "docstring"
    severity: warning

  # Must not have (error severity)
  - type: code_excludes
    metadata:
      patterns: ["eval("]
    severity: error
```

### 2. Security-First Approach

Always use `code_excludes` for security-sensitive patterns:

```yaml
assertions:
  - type: code_excludes
    metadata:
      patterns:
        - r"eval\("
        - r"exec\("
        - r"pickle\.loads"
        - r"os\.system\("
        - r"subprocess\.call"
      match_type: "regex"
    severity: error
    description: "Prevent code execution vulnerabilities"
```

### 3. Type Safety Validation

Enforce type hints and proper typing:

```yaml
assertions:
  - type: code_contains
    metadata:
      snippet: r"def \w+\([^)]*:[^)]*\)[^:]*-> \w+"
      match_type: "regex"
    severity: error
    description: "All functions must have type hints"
```

## Best Practices

✅ **DO**
- Use `pr_match` as the primary validation mechanism
- Layer `code_contains` for required patterns
- Use `code_excludes` for security/safety checks
- Set realistic thresholds (0.7-0.8) for semantic matching
- Use error severity for must-haves, warning for nice-to-haves

❌ **DON'T**
- Set PR match threshold too high (>0.9) - allows some variation
- Use `code_contains` for everything - it's less maintainable
- Forget security validation with `code_excludes`
- Hardcode PR numbers - use environment variables in CI/CD
- Ignore warnings - they provide valuable feedback

## Next Steps

- [Assertion Types Reference](../guides/assertions.md) - All assertion types
- [Writing Tests](../guides/writing-tests.md) - Complete test format
- [Advanced Features](../guides/advanced.md) - Custom validators and caching
