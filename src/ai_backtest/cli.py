"""Command-line interface for backtesting."""

import sys
from pathlib import Path
from typing import Optional

import click

from ai_backtest.comparison import VersionComparator
from ai_backtest.parser import YAMLTestParser
from ai_backtest.reporting import HTMLReporter, MarkdownReporter
from ai_backtest.runner import TestRunner


@click.group()
def cli() -> None:
    """AI Backtest: Test instruction files like CLAUDE.md and AGENTS.md."""
    pass


@cli.command()
@click.option(
    "--tests",
    type=click.Path(exists=True),
    default="tests/backtests",
    help="Directory containing test files",
)
@click.option(
    "--output",
    type=click.Path(),
    default="backtest_results.md",
    help="Output file for results",
)
@click.option(
    "--html",
    type=click.Path(),
    default=None,
    help="Generate HTML report at this path",
)
@click.option(
    "--api-key",
    envvar="ANTHROPIC_API_KEY",
    help="Anthropic API key",
)
def run(
    tests: str,
    output: str,
    html: Optional[str],
    api_key: Optional[str],
) -> None:
    """Run all backtests."""
    click.echo(f"Running backtests from {tests}...")

    # Parse tests
    try:
        test_suites = YAMLTestParser.parse_directory(tests)
        if not test_suites:
            click.echo("No test files found.", err=True)
            sys.exit(1)
        click.echo(f"Found {len(test_suites)} test suites")
    except Exception as e:
        click.echo(f"Error parsing tests: {e}", err=True)
        sys.exit(1)

    # Run tests
    runner = TestRunner(api_key=api_key)
    all_results = runner.run_suites(test_suites)

    # Flatten results
    flat_results = []
    for suite_name, results in all_results.items():
        flat_results.extend(results)

    # Generate reports
    passed = sum(1 for r in flat_results if r.passed)
    failed = sum(1 for r in flat_results if not r.passed)
    total = len(flat_results)

    click.echo(f"\nResults: {passed}/{total} passed, {failed} failed")

    # Save markdown report
    MarkdownReporter.save(flat_results, output)
    click.echo(f"Markdown report saved to {output}")

    # Save HTML report if requested
    if html:
        HTMLReporter.save(flat_results, html)
        click.echo(f"HTML report saved to {html}")

    sys.exit(0 if failed == 0 else 1)


@cli.command()
@click.option(
    "--baseline",
    type=click.Path(exists=True),
    required=True,
    help="Baseline results file (JSON)",
)
@click.option(
    "--candidate",
    type=click.Path(exists=True),
    required=True,
    help="Candidate results file (JSON)",
)
@click.option(
    "--output",
    type=click.Path(),
    default="comparison_report.md",
    help="Output file for comparison",
)
def compare(
    baseline: str,
    candidate: str,
    output: str,
) -> None:
    """Compare two test runs."""
    import json

    click.echo("Comparing baseline and candidate results...")

    # Load results
    try:
        with open(baseline, encoding="utf-8") as f:
            baseline_data = json.load(f)
        with open(candidate, encoding="utf-8") as f:
            candidate_data = json.load(f)
    except Exception as e:
        click.echo(f"Error loading results: {e}", err=True)
        sys.exit(1)

    # Compare
    comparison = VersionComparator.compare(baseline_data, candidate_data)

    # Generate report
    report = VersionComparator.regression_report(comparison)
    Path(output).write_text(report, encoding="utf-8")

    click.echo(report)
    click.echo(f"\nReport saved to {output}")

    # Exit with error if regressions found
    if VersionComparator.has_regressions(comparison):
        sys.exit(1)


@cli.command()
@click.option(
    "--tests",
    type=click.Path(exists=True),
    default="tests/backtests",
    help="Directory containing test files",
)
def list_tests(tests: str) -> None:
    """List all available tests."""
    try:
        test_suites = YAMLTestParser.parse_directory(tests)
    except Exception as e:
        click.echo(f"Error parsing tests: {e}", err=True)
        sys.exit(1)

    for suite in test_suites:
        click.echo(f"\n{suite.name}")
        click.echo(f"  Description: {suite.description}")
        click.echo(f"  Instruction version: {suite.instructions_version}")
        click.echo(f"  Test cases:")
        for test_case in suite.test_cases:
            click.echo(f"    - {test_case.description}")
            for assertion in test_case.assertions:
                click.echo(f"      [{assertion.type.value}] {assertion.description}")


if __name__ == "__main__":
    cli()
