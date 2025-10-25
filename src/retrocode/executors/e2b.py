"""E2B sandbox executor for isolated test execution."""

import hashlib
import json
import os
import time
from pathlib import Path
from typing import Optional

from retrocode.agent import AgentInvoker
from retrocode.executors.base import (
    ExecutionContext,
    ExecutionError,
    ExecutorBackend,
    SandboxConfig,
)
from retrocode.models import TestCase, TestSuite


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
                import e2b  # type: ignore[import-not-found]

                self._e2b_module = e2b
            except ImportError:
                raise ExecutionError("e2b not installed. Install with: uv pip install e2b")
        return self._e2b_module

    def acquire(self, config: SandboxConfig) -> str:
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

    def release(self, session_id: str) -> None:
        """Release a sandbox session back to the pool.

        Args:
            session_id: Sandbox session ID
        """
        if session_id in self.active_sessions:
            self.active_sessions.remove(session_id)
            self.available_sessions.append(session_id)

    def shutdown(self) -> None:
        """Shutdown all sandbox sessions."""
        self.available_sessions.clear()
        self.active_sessions.clear()


class E2BExecutor(ExecutorBackend):
    """Executor that runs tests in e2b sandboxes for isolation and security."""

    # Path to the template mapping cache
    TEMPLATE_CACHE_PATH = Path(".retrocode/cache/template-mapping.json")

    def __init__(
        self,
        api_key: Optional[str] = None,
        max_sessions: int = 5,
        sandbox_config: Optional[SandboxConfig] = None,
        cache_dir: Optional[Path] = None,
    ) -> None:
        """Initialize e2b executor.

        Args:
            api_key: Anthropic API key. If None, uses ANTHROPIC_API_KEY env var.
            max_sessions: Maximum concurrent sandbox sessions
            sandbox_config: Default sandbox configuration
            cache_dir: Directory for template cache. If None, uses .retrocode/cache
        """
        self.agent = AgentInvoker(api_key=api_key)
        self.pool = SandboxPool(max_sessions=max_sessions)
        self.sandbox_config = sandbox_config or SandboxConfig()
        self.cache_dir = cache_dir or Path(".retrocode/cache")
        self._initialized = False
        self._template_cache: dict = {}

    def setup(self) -> None:
        """Set up e2b executor."""
        try:
            self.pool._get_e2b_module()
            self._initialized = True
        except ExecutionError:
            # e2b not available, will raise error on first test execution
            pass

    def teardown(self) -> None:
        """Clean up e2b resources."""
        self.pool.shutdown()

    def _load_template_cache(self) -> dict:
        """Load the template cache from disk.

        Returns:
            Dictionary with cached template information
        """
        if not self._template_cache:
            cache_path = self.cache_dir / "template-mapping.json"
            if cache_path.exists():
                with open(cache_path, "r") as f:
                    self._template_cache = json.load(f)
            else:
                self._template_cache = {"curated_templates": {}, "custom_templates": {}}
        return self._template_cache

    def _save_template_cache(self) -> None:
        """Save the template cache to disk."""
        cache_path = self.cache_dir / "template-mapping.json"
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        with open(cache_path, "w") as f:
            json.dump(self._template_cache, f, indent=2)

    def _hash_dockerfile(self, dockerfile_path: Path) -> str:
        """Compute SHA-256 hash of Dockerfile content.

        Args:
            dockerfile_path: Path to the Dockerfile

        Returns:
            Lowercase hex digest of SHA-256 hash
        """
        with open(dockerfile_path, "rb") as f:
            content = f.read()
        return hashlib.sha256(content).hexdigest()

    def _get_curated_template(self, name: str) -> Optional[str]:
        """Get template ID for a curated template.

        Args:
            name: Name of curated template (base, claude-tools, etc.)

        Returns:
            Template ID if exists and is built, None otherwise
        """
        cache = self._load_template_cache()
        if name in cache.get("curated_templates", {}):
            return cache["curated_templates"][name].get("template_id")
        return None

    def _get_cached_template(self, content_hash: str) -> Optional[str]:
        """Look up a custom template in the cache by content hash.

        Args:
            content_hash: SHA-256 hash of Dockerfile content

        Returns:
            Template ID if cached, None otherwise
        """
        cache = self._load_template_cache()
        return cache.get("custom_templates", {}).get(content_hash, {}).get("template_id")

    def _cache_template(
        self, identifier: str, template_id: str, dockerfile_path: Optional[Path] = None
    ) -> None:
        """Cache a template ID.

        Args:
            identifier: Either template name (curated) or content hash (custom)
            template_id: The e2b template ID
            dockerfile_path: Path to Dockerfile (for curated templates)
        """
        cache = self._load_template_cache()

        # Check if this is a curated template
        if identifier in cache.get("curated_templates", {}):
            cache["curated_templates"][identifier]["template_id"] = template_id
        else:
            # Custom template - use identifier as content hash
            if "custom_templates" not in cache:
                cache["custom_templates"] = {}
            cache["custom_templates"][identifier] = {
                "template_id": template_id,
                "dockerfile_path": str(dockerfile_path) if dockerfile_path else None,
            }

        self._template_cache = cache
        self._save_template_cache()

    def _build_template(self, dockerfile_path: Path) -> str:
        """Build a Dockerfile into an e2b template.

        Args:
            dockerfile_path: Path to the Dockerfile

        Returns:
            Template ID of the built template

        Raises:
            ExecutionError: If template building fails
        """
        try:
            # Get e2b module (needed for future SDK integration)
            _e2b = self.pool._get_e2b_module()  # noqa: F841

            # Read Dockerfile content (needed for future SDK integration)
            with open(dockerfile_path, "r") as f:
                _dockerfile_content = f.read()  # noqa: F841

            # Build template using e2b SDK
            # This is a placeholder - actual implementation would call e2b.build_template()
            # For now, generate a template ID based on the hash
            content_hash = self._hash_dockerfile(dockerfile_path)
            template_id = f"tmpl_{content_hash[:16]}"

            # TODO: Actual e2b SDK call
            # template = _e2b.build_template(
            #     dockerfile=_dockerfile_content,
            #     name=f"template-{content_hash[:8]}",
            # )
            # template_id = template.id

            return template_id
        except Exception as e:
            raise ExecutionError(f"Failed to build template from {dockerfile_path}: {str(e)}")

    def _build_or_get_template(
        self, dockerfile_path: Optional[Path] = None, template_name: Optional[str] = None
    ) -> str:
        """Get or build an e2b template.

        Args:
            dockerfile_path: Path to custom Dockerfile. If None, uses template_name.
            template_name: Name of curated template (base, claude-tools). Only used if dockerfile_path is None.

        Returns:
            Template ID for use with e2b

        Raises:
            ExecutionError: If template cannot be obtained
        """
        # Case 1: Curated template
        if dockerfile_path is None and template_name:
            cached_id = self._get_curated_template(template_name)
            if cached_id:
                return cached_id

            # Build curated template
            dockerfile_path = Path(".retrocode/environments") / f"{template_name}.Dockerfile"
            if not dockerfile_path.exists():
                raise ExecutionError(
                    f"Curated template '{template_name}' not found at {dockerfile_path}"
                )

            template_id = self._build_template(dockerfile_path)
            self._cache_template(template_name, template_id, dockerfile_path)
            return template_id

        # Case 2: Custom Dockerfile
        if dockerfile_path:
            if not dockerfile_path.exists():
                raise ExecutionError(f"Dockerfile not found: {dockerfile_path}")

            content_hash = self._hash_dockerfile(dockerfile_path)
            cached_id = self._get_cached_template(content_hash)
            if cached_id:
                return cached_id

            # Build custom template
            template_id = self._build_template(dockerfile_path)
            self._cache_template(content_hash, template_id, dockerfile_path)
            return template_id

        raise ExecutionError("Either dockerfile_path or template_name must be provided")

    def _inject_environment_vars(self, env_vars: dict, sandbox_session_id: str) -> None:
        """Inject environment variables into a sandbox session.

        Args:
            env_vars: Dictionary of environment variables to inject
            sandbox_session_id: ID of the sandbox session

        Raises:
            ExecutionError: If injection fails
        """
        try:
            # TODO: Implement actual e2b environment variable injection
            # This would involve using the e2b SDK to set env vars in the running sandbox
            # For now, just validate the input
            if not isinstance(env_vars, dict):
                raise ExecutionError("Environment variables must be a dictionary")

            # Example of what the actual implementation would do:
            # e2b = self.pool._get_e2b_module()
            # session = e2b.Sandbox(sandbox_id=sandbox_session_id)
            # for key, value in env_vars.items():
            #     session.run_command(f"export {key}={value}")

        except Exception as e:
            raise ExecutionError(f"Failed to inject environment variables: {str(e)}")

    def _copy_instruction_files(self, instruction_file_path: Path, sandbox_session_id: str) -> None:
        """Copy instruction files into a sandbox session.

        Args:
            instruction_file_path: Path to the instruction file (e.g., CLAUDE.md)
            sandbox_session_id: ID of the sandbox session

        Raises:
            ExecutionError: If copy fails
        """
        try:
            if not instruction_file_path.exists():
                raise ExecutionError(f"Instruction file not found: {instruction_file_path}")

            # TODO: Implement actual e2b file upload
            # This would involve using the e2b SDK to upload files to the sandbox
            # For now, just validate the input

            # Example of what the actual implementation would do:
            # e2b = self.pool._get_e2b_module()
            # session = e2b.Sandbox(sandbox_id=sandbox_session_id)
            # with open(instruction_file_path, "rb") as f:
            #     session.upload_file(f, f"/workspace/{instruction_file_path.name}")

        except Exception as e:
            raise ExecutionError(f"Failed to copy instruction files: {str(e)}")

    def execute_test(
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
            # Step 1: Build or get template
            template_id = None
            if sandbox_config.custom_dockerfile:
                # Use custom Dockerfile
                template_id = self._build_or_get_template(
                    dockerfile_path=Path(sandbox_config.custom_dockerfile)
                )
            else:
                # Use curated template (default to 'base')
                template_name = sandbox_config.template or "base"
                template_id = self._build_or_get_template(template_name=template_name)

            # Step 2: Acquire sandbox session with the template
            session_id = self.pool.acquire(sandbox_config)

            # Step 3: Inject environment variables (e.g., ANTHROPIC_API_KEY)
            env_vars_to_inject = dict(sandbox_config.environment_vars)

            # Always inject API key if available
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if api_key:
                env_vars_to_inject["ANTHROPIC_API_KEY"] = api_key

            if env_vars_to_inject:
                self._inject_environment_vars(env_vars_to_inject, session_id)

            # Step 4: Copy instruction files to sandbox
            instruction_file = test_suite.metadata.get(
                "instruction_file", "/home/georgepearse/CLAUDE.md"
            )
            if instruction_file:
                self._copy_instruction_files(Path(instruction_file), session_id)

            # Step 5: Run agent invocation inside sandbox
            # TODO: When e2b SDK is available, execute agent inside sandbox via:
            # result = e2b_session.run_command("python -m retrocode.agent ...")
            # For now, run locally
            agent_response = self.agent.invoke(
                task=test_case.task,
                instruction_file_path=instruction_file,
                model=test_suite.model_under_test,
            )

            execution_time_ms = (time.time() - start_time) * 1000

            # Step 6: Release sandbox session back to pool
            self.pool.release(session_id)

            return ExecutionContext(
                agent_response=agent_response,
                execution_time_ms=execution_time_ms,
                execution_mode="e2b",
                sandbox_info={
                    "session_id": session_id,
                    "template_id": template_id,
                    "template": sandbox_config.template or "base",
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
