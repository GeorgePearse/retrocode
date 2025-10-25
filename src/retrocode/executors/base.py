"""Base executor interface for running tests in different environments."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Optional

from pydantic import BaseModel, Field

from retrocode.models import AgentResponse, TestCase, TestSuite


class ExecutionContext(BaseModel):
    """Complete context from test execution including outputs and metrics."""

    agent_response: AgentResponse
    stdout: str = ""
    stderr: str = ""
    exit_code: int = 0
    files_created: list[str] = Field(default_factory=list)
    files_modified: list[str] = Field(default_factory=list)
    execution_time_ms: float = 0.0
    memory_peak_mb: Optional[float] = None
    sandbox_info: Optional[dict[str, Any]] = None
    execution_mode: str = "local"  # "local" or "e2b"
    error_message: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ExecutorBackend(ABC):
    """Abstract base class for test execution backends."""

    @abstractmethod
    async def execute_test(
        self,
        test_case: TestCase,
        test_suite: TestSuite,
    ) -> ExecutionContext:
        """Execute a single test case and return execution context.

        Args:
            test_case: The test case to execute
            test_suite: The test suite context

        Returns:
            ExecutionContext with all execution details and outputs

        Raises:
            ExecutionError: If execution fails critically
        """
        pass

    @abstractmethod
    async def setup(self) -> None:
        """Set up the execution environment."""
        pass

    @abstractmethod
    async def teardown(self) -> None:
        """Clean up the execution environment."""
        pass


class ExecutionError(Exception):
    """Raised when test execution fails."""

    pass


class SandboxConfig(BaseModel):
    """Configuration for sandbox-based execution."""

    template: str = "python-3.11"
    timeout_seconds: int = 300
    memory_limit_mb: int = 2048
    cpu_cores: Optional[int] = None
    enable_networking: bool = True
    preserve_on_error: bool = False
    custom_dockerfile_path: Optional[str] = None
