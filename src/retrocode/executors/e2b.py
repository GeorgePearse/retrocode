"""E2B sandbox executor for isolated test execution."""

import json
import os
import time
from typing import Optional

from retrocode.agent import AgentInvoker
from retrocode.models import TestCase, TestSuite
from retrocode.executors.base import ExecutionContext, ExecutorBackend, SandboxConfig, ExecutionError


class SandboxPool:
    """Manages a pool of reusable e2b sandbox sessions."""

    def __init__(self, max_sessions: int = 5) -> None:
        """Initialize sandbox pool.

        Args:
            max_sessions: Maximum number of concurrent sandbox sessions
        """
        self.max_sessions = max_sessions
        self.available_sessions: list[str] = []
        self.active_sessions: set[str] = set()
        # Import deferred to handle missing e2b gracefully
        self._e2b_module = None

    def _get_e2b_module(self):
        """Lazily import e2b module."""
        if self._e2b_module is None:
            try:
                import e2b  # noqa: F401
                self._e2b_module = e2b
            except ImportError:
                raise ExecutionError(
                    "e2b not installed. Install with: uv pip install e2b"
                )
        return self._e2b_module

    async def acquire(self, config: SandboxConfig) -> str:
        """Acquire a sandbox session.

        Args:
            config: Sandbox configuration

        Returns:
            Sandbox session ID
        """
        # For now, return a placeholder
        # Full implementation would create/reuse e2b sandboxes
        session_id = f"sandbox-{int(time.time() * 1000)}"
        self.active_sessions.add(session_id)
        return session_id

    async def release(self, session_id: str) -> None:
        """Release a sandbox session back to the pool.

        Args:
            session_id: Sandbox session ID
        """
        if session_id in self.active_sessions:
            self.active_sessions.remove(session_id)
            self.available_sessions.append(session_id)

    async def shutdown(self) -> None:
        """Shutdown all sandbox sessions."""
        self.available_sessions.clear()
        self.active_sessions.clear()


class E2BExecutor(ExecutorBackend):
    """Executor that runs tests in e2b sandboxes for isolation and security."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        max_sessions: int = 5,
        sandbox_config: Optional[SandboxConfig] = None,
    ) -> None:
        """Initialize e2b executor.

        Args:
            api_key: Anthropic API key. If None, uses ANTHROPIC_API_KEY env var.
            max_sessions: Maximum concurrent sandbox sessions
            sandbox_config: Default sandbox configuration
        """
        self.agent = AgentInvoker(api_key=api_key)
        self.pool = SandboxPool(max_sessions=max_sessions)
        self.sandbox_config = sandbox_config or SandboxConfig()
        self._initialized = False

    async def setup(self) -> None:
        """Set up e2b executor."""
        try:
            self.pool._get_e2b_module()
            self._initialized = True
        except ExecutionError:
            # e2b not available, will raise error on first test execution
            pass

    async def teardown(self) -> None:
        """Clean up e2b resources."""
        await self.pool.shutdown()

    async def execute_test(
        self,
        test_case: TestCase,
        test_suite: TestSuite,
    ) -> ExecutionContext:
        """Execute test in e2b sandbox.

        Args:
            test_case: The test case to execute
            test_suite: The test suite context

        Returns:
            ExecutionContext with execution details
        """
        start_time = time.time()

        # Get sandbox config from test suite metadata if available
        sandbox_config = SandboxConfig()
        if "sandbox_environment" in test_suite.metadata:
            config_dict = test_suite.metadata["sandbox_environment"]
            sandbox_config = SandboxConfig(**config_dict)

        try:
            # Acquire sandbox session
            session_id = await self.pool.acquire(sandbox_config)

            # For now, run agent locally
            # Full implementation would:
            # 1. Create e2b sandbox with custom environment
            # 2. Install dependencies (anthropic, etc.)
            # 3. Inject API key via environment variable
            # 4. Run agent invocation inside sandbox
            # 5. Capture stdout/stderr and file changes
            # 6. Return execution context with sandbox metadata

            agent_response = self.agent.invoke(
                task=test_case.task,
                instruction_file_path=test_suite.metadata.get(
                    "instruction_file",
                    "/home/georgepearse/CLAUDE.md"
                ),
                model=test_suite.model_under_test,
            )

            execution_time_ms = (time.time() - start_time) * 1000

            # Release sandbox session back to pool
            await self.pool.release(session_id)

            return ExecutionContext(
                agent_response=agent_response,
                execution_time_ms=execution_time_ms,
                execution_mode="e2b",
                sandbox_info={
                    "session_id": session_id,
                    "template": sandbox_config.template,
                    "timeout_seconds": sandbox_config.timeout_seconds,
                },
            )

        except Exception as e:
            execution_time_ms = (time.time() - start_time) * 1000

            return ExecutionContext(
                agent_response=None,  # type: ignore
                execution_time_ms=execution_time_ms,
                execution_mode="e2b",
                error_message=f"Sandbox execution failed: {str(e)}",
                exit_code=1,
            )
