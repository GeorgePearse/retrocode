# CI/CD Integration

Set up automated backtesting in your GitHub workflow.

## GitHub Actions Workflow

Create `.github/workflows/backtest-validate.yml`:

```yaml
name: Validate Instruction Changes

on:
  pull_request:
    paths:
      - 'CLAUDE.md'
      - 'AGENTS.md'
      - 'tests/backtests/**'
      - '.github/workflows/backtest-validate.yml'

jobs:
  backtest:
    runs-on: ubuntu-latest
    timeout-minutes: 30

    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.11"

      - name: Install uv
        uses: astral-sh/setup-uv@v2

      - name: Install dependencies
        run: uv sync

      - name: Run backtests
        run: retrocode run --tests tests/backtests --output results.md
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}

      - name: Comment PR with results
        if: always()
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const results = fs.readFileSync('results.md', 'utf8');

            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: `## 🧪 Backtest Results\n\n${results}`
            });

      - name: Check for failures
        run: |
          if grep -q "FAILED" results.md; then
            echo "❌ Some tests failed"
            exit 1
          fi
```

## Setup

### 1. Add API Key Secret

```bash
# In GitHub: Settings → Secrets and variables → Actions
# Add new secret: ANTHROPIC_API_KEY
# Value: sk-ant-...
```

### 2. Trigger Workflow

The workflow runs when:
- You open a PR modifying `CLAUDE.md`, `AGENTS.md`, or test files
- You can also trigger manually via Actions tab

### 3. Review Results

Results appear as a comment on your PR.

## Regression Detection

Compare against main branch:

```yaml
- name: Run baseline (main branch)
  run: |
    git fetch origin main
    git show origin/main:tests/backtests/ > /tmp/baseline_tests/ 2>/dev/null || true
    retrocode run --tests tests/backtests --output baseline.json
  env:
    ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}

- name: Run candidate (current branch)
  run: retrocode run --tests tests/backtests --output candidate.json
  env:
    ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}

- name: Compare versions
  run: retrocode compare --baseline baseline.json --candidate candidate.json
```

## Cost Control

Each test costs ~$0.01 for judge calls (cached after first run).

### Estimate Costs

- 10 tests with 2 judge assertions each
- First run: 20 LLM calls × $0.0005 = **$0.01**
- Subsequent runs: ~0 (cached)
- Monthly: ~$1-5 depending on changes

### Optimize Costs

```yaml
# In tests: Use severity: warning for expensive judges
assertions:
  - type: llm_judge
    severity: warning  # Non-blocking, skip in PR checks
```

Then only run expensive tests in scheduled jobs:

```yaml
on:
  schedule:
    - cron: '0 0 * * 0'  # Weekly
```

## Multiple Instruction Files

Test multiple files (CLAUDE.md, AGENTS.md, etc):

```yaml
tests/backtests/
├── claude_rules.backtest.yaml
│   metadata:
│     instruction_file: "/path/to/CLAUDE.md"
├── agents_rules.backtest.yaml
│   metadata:
│     instruction_file: "/path/to/AGENTS.md"
```

All run in one command:
```bash
retrocode run --tests tests/backtests/
```

## Blocking Merges on Failure

Make tests required for merge:

1. Go to repository Settings → Branch protection rules
2. Add rule for `main` branch
3. Check "Require status checks to pass"
4. Select "backtest" job

Now PRs can't merge if tests fail.

## Advanced: Historical Testing

Test against historical PRs:

```python
# Extract test cases from historical PRs
from retrocode.parser import YAMLTestParser

test_suites = YAMLTestParser.parse_directory("tests/backtests")

# Run against previous version
test_suite.instructions_version = "v1.0"
results_v1 = runner.run_suite(test_suite)

# Run against new version
test_suite.instructions_version = "v2.0"
results_v2 = runner.run_suite(test_suite)

# Compare
comparison = VersionComparator.compare(results_v1, results_v2)
```

## Dashboard & Reports

### Generate HTML Report

```yaml
- name: Generate report
  run: retrocode run --tests tests/backtests --html report.html

- name: Upload artifact
  uses: actions/upload-artifact@v3
  with:
    name: backtest-report
    path: report.html
    retention-days: 30
```

### View Reports

1. Click "Artifacts" in GitHub Actions run
2. Download `backtest-report.html`
3. Open in browser

## Manual Testing

Test locally before pushing:

```bash
# Run all tests
pytest tests/backtests/ -v

# Run specific test
pytest tests/backtests/tool_usage.backtest.yaml -v

# See full output
pytest tests/backtests/ -s
```

## Troubleshooting

### API Key Not Found in Actions

Make sure secret is set:
1. Settings → Secrets and variables → Actions
2. Secret name is exactly `ANTHROPIC_API_KEY`

### Tests Timeout

Increase timeout in workflow:
```yaml
timeout-minutes: 60  # Increase from default 30
```

### Out of Memory

Some jobs fail due to memory. Reduce parallel runs:
```bash
# Run tests sequentially instead of parallel
pytest tests/backtests/ -n 1
```

### Cache Issues

Clear cache for fresh run:
```yaml
- name: Clear cache
  run: rm -f .retrocode_cache.db
```

## Examples

### Minimal Setup

```yaml
name: Backtest

on: [pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v4
        with:
          python-version: "3.11"
      - run: pip install -e .
      - run: pytest tests/backtests/
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
```

### Comprehensive Setup

```yaml
name: Comprehensive Backtest

on:
  pull_request:
    paths:
      - 'CLAUDE.md'
      - 'tests/backtests/**'
      - 'src/**'

jobs:
  backtest:
    runs-on: ubuntu-latest
    timeout-minutes: 60

    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - uses: actions/setup-python@v4
        with:
          python-version: "3.11"

      - uses: astral-sh/setup-uv@v2

      - run: uv sync

      # Baseline
      - run: retrocode run --tests tests/backtests --output baseline.json
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}

      # Candidate
      - run: retrocode run --tests tests/backtests --html report.html
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}

      # Report
      - uses: actions/upload-artifact@v3
        if: always()
        with:
          name: backtest-report
          path: report.html
          retention-days: 7

      # Comment
      - uses: actions/github-script@v7
        if: always()
        with:
          script: |
            const fs = require('fs');
            try {
              const report = fs.readFileSync('report.html', 'utf8');
              github.rest.issues.createComment({
                issue_number: context.issue.number,
                owner: context.repo.owner,
                repo: context.repo.repo,
                body: `## Backtest Report\nSee artifacts for HTML report`
              });
            } catch(e) {
              console.log("No report generated");
            }
```

## Next Steps

- [Examples](../examples/basic-test.md) - Real test suites
- [Advanced Features](advanced.md) - Custom validators, caching
- [API Reference](../reference/api.md) - Programmatic usage
