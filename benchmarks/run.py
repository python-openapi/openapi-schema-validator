from __future__ import annotations

import argparse
import gc
import json
import platform
import statistics
import time
import tracemalloc
from datetime import datetime
from datetime import timezone
from pathlib import Path
from typing import Any

from benchmarks.cases import BenchmarkCase
from benchmarks.cases import build_cases
from openapi_schema_validator.shortcuts import _clear_validate_cache
from openapi_schema_validator.shortcuts import validate


def _measure_compile_time_ms(
    case: BenchmarkCase,
    rounds: int,
) -> float:
    samples: list[float] = []
    for _ in range(rounds):
        start_ns = time.perf_counter_ns()
        case.validator_class(
            case.schema,
            **case.validator_kwargs,
        )
        elapsed_ms = (time.perf_counter_ns() - start_ns) / 1_000_000
        samples.append(elapsed_ms)
    return statistics.median(samples)


def _measure_first_validate_ms(case: BenchmarkCase) -> float:
    validator = case.validator_class(case.schema, **case.validator_kwargs)
    start_ns = time.perf_counter_ns()
    validator.validate(case.instance)
    return (time.perf_counter_ns() - start_ns) / 1_000_000


def _measure_compiled_validate_per_second(
    case: BenchmarkCase,
    iterations: int,
    warmup: int,
) -> float:
    validator = case.validator_class(case.schema, **case.validator_kwargs)
    for _ in range(warmup):
        validator.validate(case.instance)

    start_ns = time.perf_counter_ns()
    for _ in range(iterations):
        validator.validate(case.instance)
    elapsed = (time.perf_counter_ns() - start_ns) / 1_000_000_000
    return iterations / elapsed


def _measure_helper_validate_per_second(
    case: BenchmarkCase,
    iterations: int,
    warmup: int,
    *,
    check_schema: bool,
) -> float:
    _clear_validate_cache()
    for _ in range(warmup):
        validate(
            case.instance,
            case.schema,
            cls=case.validator_class,
            check_schema=check_schema,
            **case.validator_kwargs,
        )

    start_ns = time.perf_counter_ns()
    for _ in range(iterations):
        validate(
            case.instance,
            case.schema,
            cls=case.validator_class,
            check_schema=check_schema,
            **case.validator_kwargs,
        )
    elapsed = (time.perf_counter_ns() - start_ns) / 1_000_000_000
    return iterations / elapsed


def _measure_peak_memory_kib(
    case: BenchmarkCase,
    iterations: int,
) -> float:
    validator = case.validator_class(case.schema, **case.validator_kwargs)
    tracemalloc.start()
    for _ in range(iterations):
        validator.validate(case.instance)
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return peak / 1024


def _measure_case(
    case: BenchmarkCase,
    iterations: int,
    warmup: int,
    compile_rounds: int,
) -> dict[str, Any]:
    gc_enabled = gc.isenabled()
    gc.disable()

    try:
        return {
            "name": case.name,
            "validator_class": case.validator_class.__name__,
            "compile_ms": _measure_compile_time_ms(case, compile_rounds),
            "first_validate_ms": _measure_first_validate_ms(case),
            "compiled_validations_per_second": (
                _measure_compiled_validate_per_second(
                    case,
                    iterations,
                    warmup,
                )
            ),
            "helper_validations_per_second": (
                _measure_helper_validate_per_second(
                    case,
                    iterations,
                    warmup,
                    check_schema=True,
                )
            ),
            "helper_trusted_validations_per_second": (
                _measure_helper_validate_per_second(
                    case,
                    iterations,
                    warmup,
                    check_schema=False,
                )
            ),
            "compiled_peak_memory_kib": _measure_peak_memory_kib(
                case,
                max(iterations, 100),
            ),
        }
    finally:
        if gc_enabled:
            gc.enable()


def _build_report(
    cases: list[BenchmarkCase],
    iterations: int,
    warmup: int,
    compile_rounds: int,
) -> dict[str, Any]:
    results = [
        _measure_case(
            case,
            iterations=iterations,
            warmup=warmup,
            compile_rounds=compile_rounds,
        )
        for case in cases
    ]
    return {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "benchmark_parameters": {
            "iterations": iterations,
            "warmup": warmup,
            "compile_rounds": compile_rounds,
        },
        "cases": results,
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run validation performance benchmarks.",
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=1000,
        help="Measured validation iterations per case.",
    )
    parser.add_argument(
        "--warmup",
        type=int,
        default=100,
        help="Warmup iterations per case.",
    )
    parser.add_argument(
        "--compile-rounds",
        type=int,
        default=50,
        help="Schema compile measurements per case.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("reports/benchmarks/python-baseline.json"),
        help="Path to write JSON benchmark report.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    cases = build_cases()
    report = _build_report(
        cases,
        iterations=args.iterations,
        warmup=args.warmup,
        compile_rounds=args.compile_rounds,
    )

    output_path = args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(f"Saved benchmark report to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
