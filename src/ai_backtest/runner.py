"""Test runner for executing test suites."""

import time
from typing import Optional

from tqdm import tqdm

from ai_backtest.agent import AgentInvoker
from ai_backtest.assertions import AssertionRegistry
from ai_backtest.models import AgentResponse, AssertionSeverity, TestCase, TestResult, TestSuite


class TestRunner:
    """Runs test suites and collects results."""

    def __init__(self, api_key: Optional[str] = None) -> None:
        """Initialize the test runner.

        Args:
            api_key: Anthropic API key. If None, uses ANTHROPIC_API_KEY env var.
        """
        self.agent = AgentInvoker(api_key=api_key)

    def run_suite(self, test_suite: TestSuite) -> list[TestResult]:
        """Run all tests in a suite.

        Args:
            test_suite: The test suite to run

        Returns:
            List of TestResult objects
        """
        results = []
        for test_case in tqdm(test_suite.test_cases, desc=test_suite.name):
            result = self.run_test(test_case, test_suite)
            results.append(result)
        return results

    def run_test(self, test_case: TestCase, test_suite: TestSuite) -> TestResult:
        """Run a single test case.

        Args:
            test_case: The test case to run
            test_suite: The test suite context

        Returns:
            TestResult object
        """
        start_time = time.time()

        # Invoke agent
        try:
            agent_response = self.agent.invoke(
                task=test_case.task,
                instruction_file_path=test_suite.metadata.get(
                    "instruction_file",
                    "/home/georgepearse/CLAUDE.md"
                ),
                model=test_suite.model_under_test,
            )
        except Exception as e:
            # Return failed result if agent invocation fails
            return TestResult(
                test_case=test_case,
                agent_response=AgentResponse(
                    task=test_case.task,
                    full_response=f"Error: {str(e)}",
                    model=test_suite.model_under_test,
                    instruction_file_path="unknown",
                ),
                assertion_results=[],
                passed=False,
                duration_seconds=time.time() - start_time,
            )

        # Evaluate assertions
        assertion_results = []
        for assertion in test_case.assertions:
            try:
                result = AssertionRegistry.evaluate(assertion, agent_response)
                assertion_results.append(result)
            except Exception as e:
                from ai_backtest.models import AssertionResult

                assertion_results.append(
                    AssertionResult(
                        assertion=assertion,
                        passed=False,
                        message=f"Error evaluating assertion: {str(e)}",
                    )
                )

        # Determine overall pass/fail
        # Fail if any error-level assertion fails
        errors = [r for r in assertion_results if not r.passed and r.assertion.severity == AssertionSeverity.ERROR]
        passed = len(errors) == 0

        duration = time.time() - start_time

        return TestResult(
            test_case=test_case,
            agent_response=agent_response,
            assertion_results=assertion_results,
            passed=passed,
            duration_seconds=duration,
        )

    def run_suites(self, test_suites: list[TestSuite]) -> dict[str, list[TestResult]]:
        """Run multiple test suites.

        Args:
            test_suites: List of test suites to run

        Returns:
            Dictionary mapping suite name to results
        """
        all_results: dict[str, list[TestResult]] = {}
        for suite in test_suites:
            all_results[suite.name] = self.run_suite(suite)
        return all_results
