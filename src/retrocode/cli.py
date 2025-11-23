"""Command-line interface for backtesting."""

import json
import sys
from pathlib import Path
from typing import Optional

import click

from retrocode.executors import E2BExecutor, LocalExecutor
from retrocode.models import TestResult
from retrocode.parser import YAMLTestParser
from retrocode.reporting import HTMLReporter, MarkdownReporter
from retrocode.runner import TestRunner


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
@click.option(
    "--executor",
    type=click.Choice(["local", "e2b"]),
    default="local",
    help="Execution backend: 'local' (default) or 'e2b' (isolated sandbox)",
)
@click.option(
    "--e2b-template",
    type=str,
    default="base",
    help="E2B template to use: 'base' or 'claude-tools' (only used with --executor e2b)",
)
def run(
    tests: str,
    output: str,
    html: Optional[str],
    api_key: Optional[str],
    executor: str,
    e2b_template: str,
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

    # Create executor based on choice
    if executor == "e2b":
        try:
            from retrocode.executors.base import SandboxConfig

            click.echo(f"Using E2B sandbox executor with template: {e2b_template}")
            sandbox_config = SandboxConfig(template=e2b_template)
            executor_instance = E2BExecutor(
                api_key=api_key,
                sandbox_config=sandbox_config,
            )
        except ImportError:
            click.echo(
                "E2B executor requires e2b-code-interpreter. "
                "Install with: uv pip install 'retrocode[e2b]'",
                err=True,
            )
            sys.exit(1)
    else:
        click.echo("Using local executor")
        executor_instance = LocalExecutor(api_key=api_key)

    # Run tests
    runner = TestRunner(api_key=api_key, executor=executor_instance)
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

    # Save results based on extension
    if output.endswith(".json"):
        with open(output, "w", encoding="utf-8") as f:
            json.dump([r.model_dump(mode="json") for r in flat_results], f, indent=2)
        click.echo(f"JSON results saved to {output}")
    else:
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
        click.echo("  Test cases:")
        for test_case in suite.test_cases:
            click.echo(f"    - {test_case.description}")
            for assertion in test_case.assertions:
                click.echo(f"      [{assertion.type.value}] {assertion.description}")


if __name__ == "__main__":
    cli()
