"""Version comparison and regression detection."""

from typing import Optional

from ai_backtest.models import ComparisonResult, TestResult


class VersionComparator:
    """Compares test results across instruction versions."""

    @staticmethod
    def compare(
        baseline: list[TestResult],
        candidate: list[TestResult],
    ) -> ComparisonResult:
        """Compare baseline and candidate results.

        Args:
            baseline: Results from baseline instruction version
            candidate: Results from candidate instruction version

        Returns:
            ComparisonResult with regressions and improvements
        """
        # Build lookups by test description
        baseline_by_desc = {r.test_case.description: r for r in baseline}
        candidate_by_desc = {r.test_case.description: r for r in candidate}

        regressions = []
        improvements = []
        score_deltas = {}

        # Find regressions and improvements
        for desc, cand_result in candidate_by_desc.items():
            if desc not in baseline_by_desc:
                continue

            base_result = baseline_by_desc[desc]

            # Check for regression (passed -> failed)
            if base_result.passed and not cand_result.passed:
                regressions.append((base_result, cand_result))

            # Check for improvement (failed -> passed)
            if not base_result.passed and cand_result.passed:
                improvements.append((base_result, cand_result))

            # Track score changes
            base_score = VersionComparator._calculate_score(base_result)
            cand_score = VersionComparator._calculate_score(cand_result)
            if base_score is not None and cand_score is not None:
                delta = cand_score - base_score
                score_deltas[desc] = delta

        return ComparisonResult(
            baseline_results=baseline,
            candidate_results=candidate,
            regressions=regressions,
            improvements=improvements,
            score_deltas=score_deltas,
        )

    @staticmethod
    def _calculate_score(result: TestResult) -> Optional[float]:
        """Calculate overall score for a test result.

        Args:
            result: The test result

        Returns:
            Score between 0-1 or None
        """
        if not result.assertion_results:
            return None

        scores = [
            ar.score for ar in result.assertion_results if ar.score is not None
        ]

        if not scores:
            return None

        return sum(scores) / len(scores)

    @staticmethod
    def has_regressions(comparison: ComparisonResult) -> bool:
        """Check if comparison found any regressions.

        Args:
            comparison: The comparison result

        Returns:
            True if regressions found
        """
        return len(comparison.regressions) > 0

    @staticmethod
    def regression_report(comparison: ComparisonResult) -> str:
        """Generate human-readable regression report.

        Args:
            comparison: The comparison result

        Returns:
            Formatted report text
        """
        lines = []
        lines.append("# Version Comparison Report\n")

        total_baseline = len(comparison.baseline_results)
        total_candidate = len(comparison.candidate_results)
        baseline_passed = sum(1 for r in comparison.baseline_results if r.passed)
        candidate_passed = sum(1 for r in comparison.candidate_results if r.passed)

        lines.append("## Summary")
        lines.append(f"- **Baseline:** {baseline_passed}/{total_baseline} passed")
        lines.append(f"- **Candidate:** {candidate_passed}/{total_candidate} passed")
        lines.append(f"- **Regressions:** {len(comparison.regressions)}")
        lines.append(f"- **Improvements:** {len(comparison.improvements)}\n")

        if comparison.regressions:
            lines.append("## Regressions ⚠️\n")
            for base, cand in comparison.regressions:
                lines.append(f"- **{base.test_case.description}**")
                lines.append(f"  - Was passing in baseline")
                failures = cand.failures
                if failures:
                    for f in failures[:3]:
                        lines.append(f"  - Now failing: {f.message}")
                lines.append("")

        if comparison.improvements:
            lines.append("## Improvements ✓\n")
            for base, cand in comparison.improvements:
                lines.append(f"- **{base.test_case.description}**")
                lines.append(f"  - Was failing in baseline")
                lines.append(f"  - Now passing in candidate")
                lines.append("")

        if comparison.score_deltas:
            significant_deltas = {
                k: v for k, v in comparison.score_deltas.items() if abs(v) > 0.05
            }
            if significant_deltas:
                lines.append("## Score Changes\n")
                for desc, delta in sorted(
                    significant_deltas.items(), key=lambda x: x[1], reverse=True
                ):
                    arrow = "↑" if delta > 0 else "↓"
                    lines.append(f"- {arrow} {desc}: {delta:+.2f}")
                lines.append("")

        return "\n".join(lines)
