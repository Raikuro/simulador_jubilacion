# Performance Guide

This guide explains the performance benchmark suite and the performance
principles the project follows. It documents what is measured, what is not,
and how to run the measurements.

## Project principle

From [CONTRIBUTION.md](CONTRIBUTION.md):

- Never optimize before profiling.
- Document every optimization.
- Benchmark after major optimizations.

Correctness and determinism always come before performance.

## Benchmark suite

The benchmarks live in `tests/benchmarks/` and are part of Phase 4 (P4.4) of
the v0.4 infrastructure milestone. They are **wall-clock measurements**, not
hard assertions: each test measures an operation with `time.perf_counter`,
prints a `[BENCHMARK]` line, and asserts correctness invariants — it does
**not** fail the build when a measurement rises.

Breakdown (26 tests):

| File | Tests | Measures |
|------|-------|----------|
| `test_cli_performance.py` | 10 | CLI startup (`--help`, `--version`), study validation, config validate/list/set+get, list behaviour with no database |
| `test_execution_performance.py` | 9 | Sequential determinism, parallel determinism, parallel = sequential equality, translation overhead and scaling, parallel dispatch timing |
| `test_persistence_performance.py` | 7 | Single-operation save times (`save_experiment`, `save_plan`, `save_execution_result`), `load_plan`, write pipeline (2 / 4 units), round-trip integrity |

Run them:

```bash
.venv/bin/python -m pytest tests/benchmarks -v
```

Each benchmark prints its wall-clock time on stdout, e.g.:

```
[BENCHMARK] cli validate study: 0.0123s
[BENCHMARK] parallel dispatch (8 units, 4 workers): 0.0442s
```

## What the determinism tests enforce

The execution benchmarks are the important correctness gate. They assert:

1. Sequential execution is deterministic — same plan, same result twice.
2. Parallel execution is deterministic — same plan, same result twice.
3. Parallel results equal sequential results.
4. Different worker counts produce identical results.

These are hard assertions and are part of the full `pytest` suite. If you
change the executor, translation layer, or engine code they must remain
green.

## Interpreting measurements

Because the measurements are informational, use them as relative regressions:

- Compare a change against the previous run on the **same machine**.
- Prefer stable, reproducible data (the synthetic `make_benchmark_dataset`
  fixtures) over real market files for isolating code changes.
- Watch for order-of-magnitude changes, not a few tens of milliseconds — the
  absolute numbers are machine- and load-dependent.

## Where the hot paths are

From the benchmark layout, the instrumented surfaces are:

| Area | Where | What matters |
|------|-------|--------------|
| CLI startup | `src/cli/main.py` entry | Import cost; keep CLI imports lazy |
| Plan translation | `src/research/` → engine translation | O(units) construction cost |
| Parallel dispatch | `src/infrastructure/execution/parallel_executor.py` | Determinism + per-worker overhead |
| Persistence | `src/infrastructure/persistence/` | Per-entity save; the SQLite write pipeline |

## Guidance for contributors

- **Profile before optimizing** — measure with the benchmark output, then
  change one thing at a time.
- **Keep determinism** — parallel and sequential must match; any parallelism
  change must keep the 4 determinism assertions green.
- **Keep correctness first** — the engine, research, and optimization layers
  are frozen; do not trade correctness for speed in them.
- **Document optimizations** — record what changed and why in the commit
  message and, if user-visible, in the relevant user documentation.
- **Re-run the benchmarks** after any change to the executor, persistence, or
  CLI entry point.

## See also

- [DEVELOPMENT_WORKFLOW.md](DEVELOPMENT_WORKFLOW.md) — verification loop.
- [CONTRIBUTION.md](CONTRIBUTION.md) — the performance principle.
- [DOCUMENTATION_TREE.md](../DOCUMENTATION_TREE.md) — where benchmarks sit in
  the milestone plan (P4.4).
- `docs/continuity/NEXT_SESSION.md` — milestone status and invariants.