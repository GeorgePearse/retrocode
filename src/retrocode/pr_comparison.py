"""GitHub PR comparison utilities for backtesting."""

import os
from dataclasses import dataclass
from typing import Optional

from github import Github
from github.GithubException import GithubException


@dataclass
class FileChange:
    """Represents a single file changed in a PR."""

    path: str
    """File path relative to repository root."""

    additions: str
    """Added/modified content."""

    deletions: str
    """Deleted content."""

    language: Optional[str] = None
    """Programming language (inferred from extension)."""


@dataclass
class PRData:
    """Data extracted from a GitHub PR."""

    repo: str
    """Repository in format 'owner/repo'."""

    pr_number: int
    """Pull request number."""

    title: str
    """PR title."""

    files: list[FileChange]
    """Files changed in the PR."""


class PRFetcher:
    """Fetch and cache PR data from GitHub."""

    def __init__(self, token: Optional[str] = None) -> None:
        """Initialize PRFetcher with GitHub authentication.

        Authentication strategy (in order of precedence):
        1. Explicit token passed to this method
        2. GITHUB_TOKEN environment variable
        3. PyGithub's default credential store (GITHUB_PAT env var, ~/.config/gh/hosts.yml, etc.)

        Args:
            token: Optional explicit GitHub token. If provided, used for authentication.

        Raises:
            ValueError: If no authentication method is available.
        """
        # Try explicit token first
        if token:
            self.github = Github(token)
            return

        # Try environment variable
        env_token = os.getenv("GITHUB_TOKEN")
        if env_token:
            self.github = Github(env_token)
            return

        # Try default credential store (will raise if nothing found)
        try:
            self.github = Github()
        except Exception as e:
            raise ValueError(
                "No GitHub authentication found. Provide token parameter, "
                "GITHUB_TOKEN environment variable, or configure GitHub CLI."
            ) from e

    def fetch_pr(self, pr_reference: str) -> PRData:
        """Fetch PR data from GitHub.

        Args:
            pr_reference: PR reference in format 'owner/repo#123' or full URL.

        Returns:
            PRData object with files and changes.

        Raises:
            ValueError: If PR reference format is invalid.
            GithubException: If PR not found or API error occurs.
        """
        # Parse pr_reference
        repo_str, pr_num_str = self._parse_pr_reference(pr_reference)

        try:
            pr_num = int(pr_num_str)
        except ValueError as e:
            raise ValueError(f"Invalid PR number: {pr_num_str}") from e

        try:
            # Fetch repository and PR
            repo = self.github.get_repo(repo_str)
            pr = repo.get_pull(pr_num)
        except GithubException as e:
            raise ValueError(f"Failed to fetch PR: {e.data.get('message', str(e))}") from e

        # Extract file changes
        files: list[FileChange] = []

        for file in pr.get_files():
            # Fetch full file content at head and base
            try:
                # Use patch for now; can be improved to fetch full files
                files.append(
                    FileChange(
                        path=file.filename,
                        additions=file.patch or "",
                        deletions="",  # TODO: Parse deletions from patch
                        language=self._infer_language(file.filename),
                    )
                )
            except GithubException:
                # Skip files we can't fetch
                continue

        return PRData(
            repo=repo_str,
            pr_number=pr_num,
            title=pr.title,
            files=files,
        )

    @staticmethod
    def _parse_pr_reference(pr_reference: str) -> tuple[str, str]:
        """Parse PR reference into repo and PR number.

        Supports formats:
        - 'owner/repo#123'
        - 'https://github.com/owner/repo/pull/123'

        Args:
            pr_reference: PR reference string.

        Returns:
            Tuple of (repo, pr_number).

        Raises:
            ValueError: If format is invalid.
        """
        # Handle GitHub URL format
        if "github.com" in pr_reference and "/pull/" in pr_reference:
            parts = pr_reference.split("/")
            if len(parts) >= 5:
                owner = parts[-4]
                repo = parts[-3]
                pr_num = parts[-1]
                return f"{owner}/{repo}", pr_num

        # Handle 'owner/repo#123' format
        if "#" in pr_reference:
            repo_part, pr_num = pr_reference.rsplit("#", 1)
            return repo_part, pr_num

        raise ValueError(
            f"Invalid PR reference format: {pr_reference}. "
            "Use 'owner/repo#123' or 'https://github.com/owner/repo/pull/123'"
        )

    @staticmethod
    def _infer_language(filename: str) -> Optional[str]:
        """Infer programming language from file extension.

        Args:
            filename: File path or name.

        Returns:
            Programming language or None if unknown.
        """
        ext_to_lang = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".tsx": "typescript",
            ".jsx": "javascript",
            ".go": "go",
            ".rs": "rust",
            ".java": "java",
            ".cpp": "cpp",
            ".c": "c",
            ".rb": "ruby",
            ".php": "php",
            ".cs": "csharp",
        }

        for ext, lang in ext_to_lang.items():
            if filename.endswith(ext):
                return lang

        return None
