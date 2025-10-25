# Python API Reference

Use AI Backtest programmatically from Python code.

## Core Classes

### AgentInvoker

Invoke Claude with instruction files.

```python
from ai_backtest.agent import AgentInvoker

invoker = AgentInvoker(api_key="sk-ant-...")

response = invoker.invoke(
    task="Write a Python function",
    instruction_file_path="/path/to/CLAUDE.md",
    model="claude-3-5-sonnet-20250109",
    max_tokens=4096
)

print(response.full_response)
print(response.generated_code)
print(response.generated_commands)
```

### TestRunner

Run test suites and collect results.

```python
from ai_backtest.runner import TestRunner
from ai_backtest.parser import YAMLTestParser

# Parse tests
test_suites = YAMLTestParser.parse_directory("tests/backtests")

# Run tests
runner = TestRunner()
results = runner.run_suites(test_suites)

# Or run single test
result = runner.run_test(test_case, test_suite)
```

### YAMLTestParser

Parse YAML test files.

```python
from ai_backtest.parser import YAMLTestParser

# Parse single file
test_suite = YAMLTestParser.parse_file("tests/backtests/test.backtest.yaml")

# Parse directory
test_suites = YAMLTestParser.parse_directory("tests/backtests")

# Access test data
for suite in test_suites:
    print(f"Suite: {suite.name}")
    for test_case in suite.test_cases:
        print(f"  Test: {test_case.description}")
        for assertion in test_case.assertions:
            print(f"    Assert: {assertion.description}")
```

### AssertionRegistry

Evaluate assertions on responses.

```python
from ai_backtest.assertions import AssertionRegistry

# Evaluate single assertion
result = AssertionRegistry.evaluate(assertion, response)

print(f"Passed: {result.passed}")
print(f"Message: {result.message}")
print(f"Score: {result.score}")
```

### VersionComparator

Compare test results across versions.

```python
from ai_backtest.comparison import VersionComparator

# Compare results
comparison = VersionComparator.compare(baseline_results, candidate_results)

# Check for regressions
if VersionComparator.has_regressions(comparison):
    report = VersionComparator.regression_report(comparison)
    print(report)

# Access comparison data
print(f"Regressions: {len(comparison.regressions)}")
print(f"Improvements: {len(comparison.improvements)}")
print(f"Score deltas: {comparison.score_deltas}")
```

## Reporting

### MarkdownReporter

Generate Markdown reports.

```python
from ai_backtest.reporting import MarkdownReporter

# Generate report
report = MarkdownReporter.generate(results, title="Test Results")
print(report)

# Save to file
MarkdownReporter.save(results, "report.md")
```

### HTMLReporter

Generate HTML reports.

```python
from ai_backtest.reporting import HTMLReporter

# Generate report
html = HTMLReporter.generate(results, title="Test Results")

# Save to file
HTMLReporter.save(results, "report.html")
```

## Advanced

### Custom Validators

```python
from ai_backtest.code_analysis import CodeAnalyzer, CodeAnalysisRegistry
from ai_backtest.models import AssertionResult

class CustomValidator(CodeAnalyzer):
    def analyze(self, assertion, response):
        # Your validation logic
        passed = True  # Your check

        return AssertionResult(
            assertion=assertion,
            passed=passed,
            message="Your message"
        )

# Register
CodeAnalysisRegistry.register("custom", CustomValidator)
```

### LLM Judge Caching

```python
from ai_backtest.cache import JudgeCache

cache = JudgeCache()

# Cleanup expired entries
deleted = cache.cleanup_expired()

# Clear all
cache.clear()

# Access database
import sqlite3
conn = sqlite3.connect('.ai_backtest_cache.db')
cursor = conn.cursor()
cursor.execute("SELECT COUNT(*) FROM judge_cache")
print(f"Cached entries: {cursor.fetchone()[0]}")
```

## Complete Example

```python
from ai_backtest.parser import YAMLTestParser
from ai_backtest.runner import TestRunner
from ai_backtest.comparison import VersionComparator
from ai_backtest.reporting import HTMLReporter, MarkdownReporter

# 1. Parse tests
test_suites = YAMLTestParser.parse_directory("tests/backtests")
print(f"Loaded {len(test_suites)} test suites")

# 2. Run tests with baseline
runner = TestRunner()
baseline_results = []
for suite in test_suites:
    results = runner.run_suite(suite)
    baseline_results.extend(results)

# 3. Save baseline
MarkdownReporter.save(baseline_results, "baseline.md")

# ... Make changes to CLAUDE.md / AGENTS.md ...

# 4. Run tests with candidate
candidate_results = []
for suite in test_suites:
    results = runner.run_suite(suite)
    candidate_results.extend(results)

# 5. Compare versions
comparison = VersionComparator.compare(baseline_results, candidate_results)

# 6. Check for regressions
if VersionComparator.has_regressions(comparison):
    print("❌ Regressions detected!")
    print(VersionComparator.regression_report(comparison))
else:
    print("✅ No regressions!")

# 7. Generate reports
MarkdownReporter.save(candidate_results, "candidate.md")
HTMLReporter.save(candidate_results, "report.html")

# 8. Print statistics
total = len(candidate_results)
passed = sum(1 for r in candidate_results if r.passed)
print(f"\nResults: {passed}/{total} passed ({100*passed/total:.1f}%)")
```

## Models

### AgentResponse
Response from agent invocation.

```python
@dataclass
class AgentResponse:
    task: str
    full_response: str
    generated_code: list[str]
    generated_commands: list[str]
    tool_calls: list[dict]
    model: str
    conversation_trace: list[dict]
    # ... more fields
```

### TestResult
Result of running a test case.

```python
@dataclass
class TestResult:
    test_case: TestCase
    agent_response: AgentResponse
    assertion_results: list[AssertionResult]
    passed: bool
    duration_seconds: float
    # ... more fields
```

### AssertionResult
Result of evaluating an assertion.

```python
@dataclass
class AssertionResult:
    assertion: Assertion
    passed: bool
    message: str
    score: Optional[float]
    evidence: Optional[dict]
    timestamp: datetime
```

## See Also

- [Writing Tests](../guides/writing-tests.md) - YAML test format
- [Assertion Types](../guides/assertions.md) - All assertion types
- [Advanced Features](../guides/advanced.md) - Custom validators, caching
