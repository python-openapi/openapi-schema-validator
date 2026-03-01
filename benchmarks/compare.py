from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

LOWER_IS_BETTER_METRICS = {
    "compile_ms",
    "first_validate_ms",
    "compiled_peak_memory_kib",
}
HIGHER_IS_BETTER_METRICS = {
    "compiled_validations_per_second",
    "helper_validations_per_second",
    "helper_trusted_validations_per_second",
}
ALL_METRICS = [
    "compile_ms",
    "first_validate_ms",
    "compiled_validations_per_second",
    "helper_validations_per_second",
    "helper_trusted_validations_per_second",
    "compiled_peak_memory_kib",
]


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare two benchmark JSON reports.",
    )
    parser.add_argument(
        "--baseline",
        type=Path,
        required=True,
        help="Path to baseline benchmark JSON.",
    )
    parser.add_argument(
        "--candidate",
        type=Path,
        required=True,
        help="Path to candidate benchmark JSON.",
    )
    parser.add_argument(
        "--regression-threshold",
        type=float,
        default=0.0,
        help=(
            "Percent threshold for regressions. "
            "Example: 5 means fail only when regression exceeds 5%%."
        ),
    )
    parser.add_argument(
        "--fail-on-regression",
        action="store_true",
        help="Exit with status 1 if regressions exceed threshold.",
    )
    return parser.parse_args()


def _load_report(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _cases_by_name(report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {case["name"]: case for case in report["cases"]}


def _percent_change(baseline_value: float, candidate_value: float) -> float:
    if baseline_value == 0:
        if candidate_value == 0:
            return 0.0
        return float("inf")
    return ((candidate_value - baseline_value) / baseline_value) * 100.0


def _is_regression(metric: str, percent_change: float) -> bool:
    if metric in LOWER_IS_BETTER_METRICS:
        return percent_change > 0
    return percent_change < 0


def _format_status(is_regression: bool, percent_change: float) -> str:
    if abs(percent_change) < 1e-12:
        return "no change (0.00%)"

    direction = "regression" if is_regression else "improvement"
    sign = "+" if percent_change >= 0 else ""
    return f"{direction} ({sign}{percent_change:.2f}%)"


def _compare_reports(
    baseline: dict[str, Any],
    candidate: dict[str, Any],
    regression_threshold: float,
) -> tuple[list[str], list[str]]:
    baseline_cases = _cases_by_name(baseline)
    candidate_cases = _cases_by_name(candidate)

    report_lines: list[str] = []
    regressions: list[str] = []

    for case_name in sorted(baseline_cases):
        if case_name not in candidate_cases:
            regressions.append(
                f"Missing case in candidate report: {case_name}"
            )
            continue

        report_lines.append(f"Case: {case_name}")
        baseline_case = baseline_cases[case_name]
        candidate_case = candidate_cases[case_name]

        for metric in ALL_METRICS:
            baseline_value = float(baseline_case[metric])
            candidate_value = float(candidate_case[metric])
            change = _percent_change(baseline_value, candidate_value)
            regression = _is_regression(metric, change)
            status = _format_status(regression, change)

            report_lines.append(
                "  "
                f"{metric}: baseline={baseline_value:.6f} "
                f"candidate={candidate_value:.6f} -> {status}"
            )

            if regression and abs(change) > regression_threshold:
                regressions.append(
                    f"{case_name} {metric} regressed by {abs(change):.2f}%"
                )

    extra_candidate_cases = set(candidate_cases).difference(baseline_cases)
    for case_name in sorted(extra_candidate_cases):
        report_lines.append(f"Case present only in candidate: {case_name}")

    return report_lines, regressions


def main() -> int:
    args = _parse_args()
    baseline = _load_report(args.baseline)
    candidate = _load_report(args.candidate)
    report_lines, regressions = _compare_reports(
        baseline,
        candidate,
        args.regression_threshold,
    )

    print(
        f"Comparing candidate {args.candidate} "
        f"against baseline {args.baseline}"
    )
    print("")
    print("\n".join(report_lines))

    if regressions:
        print("")
        print("Regressions above threshold:")
        for regression in regressions:
            print(f"- {regression}")

        if args.fail_on_regression:
            return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
