#!/usr/bin/env python3
"""Reproduce the PeTTa timeout behavior for AtLeastCuteCatsInPark."""

from __future__ import annotations

import argparse
import time

from pettachainer.pettachainer import PeTTaChainer


STATEMENTS = [
    "(: s1 (Cardinality CatsInPark 3) (STV 1 0.9))",
    "(: s2 (Implication (Premises (Member $c CatsInPark)) (Conclusions (Cat $c) (InPark $c) (Cute $c))) (STV 1 0.9))",
    "(: h1 (Implication (Premises (Cardinality CatsInPark $n) (Compute <= (2 $n) -> True)) (Conclusions (AtLeastCuteCatsInPark 2))) (STV 1 0.9))",
]

QUERIES = [
    "(: $prf (Implication (Premises (Cat $x)) (Conclusions (Cute $x))) $tv)",
    "(: $prf (And (Cat $c) (InPark $c) (Cute $c)) $tv)",
    "(: $prf (AtLeastCuteCatsInPark 2) $tv)",
]


def run_once(depth: int, timeout_sec: float | None) -> None:
    chainer = PeTTaChainer()

    print("--- add_atom timings ---")
    for stmt in STATEMENTS:
        t0 = time.perf_counter()
        chainer.add_atom(stmt)
        dt = time.perf_counter() - t0
        print(f"{dt:.4f}s | {stmt}")

    print(f"\n--- query timings (depth={depth}, timeout={timeout_sec}) ---")
    for i, query in enumerate(QUERIES, start=1):
        t0 = time.perf_counter()
        try:
            res = chainer.query(query, depth=depth, timeout_sec=timeout_sec)
            dt = time.perf_counter() - t0
            print(f"Q{i}: {dt:.4f}s | ok | result_len={len(res)}")
            print(res)
        except Exception as exc:  # pragma: no cover
            dt = time.perf_counter() - t0
            print(f"Q{i}: {dt:.4f}s | ERROR | {exc.__class__.__name__}: {exc}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--depth", type=int, default=10, help="Query depth")
    parser.add_argument(
        "--timeout",
        type=float,
        default=10.0,
        help="Query timeout in seconds; use <=0 for no timeout",
    )
    args = parser.parse_args()

    timeout: float | None = None if args.timeout <= 0 else args.timeout
    run_once(depth=args.depth, timeout_sec=timeout)


if __name__ == "__main__":
    main()
