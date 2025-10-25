"""Assertion implementations for validating agent responses."""

import json
import re
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Optional

from pydantic import ValidationError, validate_call

from ai_backtest.models import (
    AgentResponse,
    Assertion,
    AssertionResult,
    AssertionType,
)


class AssertionEvaluator(ABC):
    """Base class for assertion evaluators."""

    @abstractmethod
    def evaluate(self, assertion: Assertion, response: AgentResponse) -> AssertionResult:
        """Evaluate an assertion against a response.

        Args:
            assertion: The assertion to evaluate
            response: The agent response to check

        Returns:
            AssertionResult with pass/fail and details
        """
        pass

    def _get_check_content(self, assertion: Assertion, response: AgentResponse) -> str:
        """Get the content to check based on assertion target.

        Args:
            assertion: The assertion
            response: The agent response

        Returns:
            Content to validate
        """
        match assertion.target.value:
            case "generated_commands":
                return "\n".join(response.generated_commands)
            case "generated_code":
                return "\n".join(response.generated_code)
            case "tool_calls":
                return json.dumps(response.tool_calls)
            case _:
                return response.full_response


class MustContainEvaluator(AssertionEvaluator):
    """Evaluates must_contain assertions."""

    def evaluate(self, assertion: Assertion, response: AgentResponse) -> AssertionResult:
        """Check if content contains required text.

        Args:
            assertion: The assertion
            response: The agent response

        Returns:
            AssertionResult
        """
        if not assertion.pattern:
            return AssertionResult(
                assertion=assertion,
                passed=False,
                message="No pattern specified for must_contain assertion",
            )

        content = self._get_check_content(assertion, response)
        passed = assertion.pattern in content

        message = (
            f"✓ Found required text: {assertion.pattern}"
            if passed
            else f"✗ Required text not found: {assertion.pattern}"
        )

        return AssertionResult(
            assertion=assertion,
            passed=passed,
            message=message,
            evidence={"pattern": assertion.pattern, "found": passed},
        )


class MustNotContainEvaluator(AssertionEvaluator):
    """Evaluates must_not_contain assertions."""

    def evaluate(self, assertion: Assertion, response: AgentResponse) -> AssertionResult:
        """Check if content does not contain forbidden text.

        Args:
            assertion: The assertion
            response: The agent response

        Returns:
            AssertionResult
        """
        if not assertion.pattern:
            return AssertionResult(
                assertion=assertion,
                passed=False,
                message="No pattern specified for must_not_contain assertion",
            )

        content = self._get_check_content(assertion, response)
        passed = assertion.pattern not in content

        message = (
            f"✓ Forbidden text not found: {assertion.pattern}"
            if passed
            else f"✗ Forbidden text found: {assertion.pattern}"
        )

        return AssertionResult(
            assertion=assertion,
            passed=passed,
            message=message,
            evidence={"pattern": assertion.pattern, "found": not passed},
        )


class RegexMatchEvaluator(AssertionEvaluator):
    """Evaluates regex_match assertions."""

    def evaluate(self, assertion: Assertion, response: AgentResponse) -> AssertionResult:
        """Check if content matches regex pattern.

        Args:
            assertion: The assertion (pattern field contains regex)
            response: The agent response

        Returns:
            AssertionResult
        """
        if not assertion.pattern:
            return AssertionResult(
                assertion=assertion,
                passed=False,
                message="No pattern specified for regex_match assertion",
            )

        content = self._get_check_content(assertion, response)

        try:
            match = re.search(assertion.pattern, content, re.MULTILINE | re.DOTALL)
            passed = match is not None

            message = (
                f"✓ Regex matched: {assertion.pattern}"
                if passed
                else f"✗ Regex did not match: {assertion.pattern}"
            )

            return AssertionResult(
                assertion=assertion,
                passed=passed,
                message=message,
                evidence={"pattern": assertion.pattern, "matched": passed},
            )
        except re.error as e:
            return AssertionResult(
                assertion=assertion,
                passed=False,
                message=f"Invalid regex pattern: {e}",
            )


class JSONSchemaEvaluator(AssertionEvaluator):
    """Evaluates json_schema assertions."""

    def evaluate(self, assertion: Assertion, response: AgentResponse) -> AssertionResult:
        """Validate JSON content against schema.

        Args:
            assertion: The assertion (metadata['schema'] contains JSON schema)
            response: The agent response

        Returns:
            AssertionResult
        """
        content = self._get_check_content(assertion, response)

        try:
            json_obj = json.loads(content)
        except json.JSONDecodeError as e:
            return AssertionResult(
                assertion=assertion,
                passed=False,
                message=f"Failed to parse JSON: {e}",
                evidence={"content_sample": content[:100]},
            )

        schema = assertion.metadata.get("schema")
        if not schema:
            return AssertionResult(
                assertion=assertion,
                passed=False,
                message="No schema provided in metadata",
            )

        try:
            from jsonschema import ValidationError, validate

            validate(instance=json_obj, schema=schema)
            return AssertionResult(
                assertion=assertion,
                passed=True,
                message="✓ JSON schema validation passed",
                evidence={"schema_valid": True},
            )
        except ValidationError as e:
            return AssertionResult(
                assertion=assertion,
                passed=False,
                message=f"Schema validation failed: {e.message}",
                evidence={"error": e.message},
            )
        except ImportError:
            return AssertionResult(
                assertion=assertion,
                passed=False,
                message="jsonschema library not installed",
            )


class AssertionRegistry:
    """Registry for assertion evaluators."""

    _evaluators: dict[AssertionType, type[AssertionEvaluator]] = {
        AssertionType.MUST_CONTAIN: MustContainEvaluator,
        AssertionType.MUST_NOT_CONTAIN: MustNotContainEvaluator,
        AssertionType.REGEX_MATCH: RegexMatchEvaluator,
        AssertionType.JSON_SCHEMA: JSONSchemaEvaluator,
    }

    @classmethod
    def evaluate(
        cls, assertion: Assertion, response: AgentResponse
    ) -> AssertionResult:
        """Evaluate assertion using registered evaluator.

        Args:
            assertion: The assertion to evaluate
            response: The agent response

        Returns:
            AssertionResult

        Raises:
            ValueError: If assertion type is not registered
        """
        evaluator_class = cls._evaluators.get(assertion.type)
        if not evaluator_class:
            msg = f"Unknown assertion type: {assertion.type}"
            raise ValueError(msg)

        evaluator = evaluator_class()
        return evaluator.evaluate(assertion, response)

    @classmethod
    def register(
        cls, assertion_type: AssertionType, evaluator_class: type[AssertionEvaluator]
    ) -> None:
        """Register a custom evaluator.

        Args:
            assertion_type: The assertion type
            evaluator_class: The evaluator class
        """
        cls._evaluators[assertion_type] = evaluator_class
