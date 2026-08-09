# Development Workflow Guide

This is the day-to-day development workflow for working in the
`sim-retire` repository. It assumes you have read
[INSTALLATION_AND_QUICKSTART.md](INSTALLATION_AND_QUICKSTART.md) and
[CONTRIBUTION.md](CONTRIBUTION.md).

## 1. Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

The dev extras install `pytest`, `ruff`, and `mypy` together with the
package.

## 2. The verification loop

Run the full suite, the linter, and the type checker before and after any
change:

```bash
pytest -q                     # full suite (808 tests)
pytest tests/ -v              # verbose, to see every test
ruff check src tests           # lint
mypy src --strict             # production typing (0 errors)
mypy tests --strict           # test typing (0 errors)
```

The `pyproject.toml` carries the `ruff`, `mypy`, and `pytest` configuration.
`mypy` runs in `--strict` mode for both `src` and `tests`.

## 3. Test layout

| Directory | What it covers | Count (reference) |
|-----------|----------------|--------------------|
| `tests/domain/` | Engine domain model, services, policies | 369 |
| `tests/cli/` | CLI commands and configuration | 168 |
| `tests/infrastructure/` | Persistence and parallel execution | 102 |
| `tests/integration/` | End-to-end workflow tests (P4.1–P4.3) | 135 |
| `tests/benchmarks/` | Wall-clock performance benchmarks (P4.4) | 26 |
| `tests/` (dataset slicing) | Multi-cohort dataset slice coverage | 8 |

Benchmarks are wall-clock measurements, not fail-fail assertions. See
[PERFORMANCE_GUIDE.md](PERFORMANCE_GUIDE.md) for how to read them.

## 4. Frozen code

The architectural invariants in `docs/continuity/NEXT_SESSION.md` list the
frozen surfaces. Respect them:

- v0.1 engine, v0.2 research, v0.3 optimization layers are frozen.
- Each CLI command is frozen once its phase closes; extending a command
  requires architect approval.
- `src/cli/builders.py` is shared and evolvable — add builder functions, but
  do not change existing signatures.

## 5. Branching and commits

Follow the branch strategy in [CONTRIBUTION.md](CONTRIBUTION.md):

- `feature/<name>`, `bugfix/<name>`, `refactor/<name>`.
- Commits are small and atomic. During a single milestone, follow the atomic
  milestone commit policy in `docs/continuity/AI_ARCHITECT_GUIDE.md` instead
  of creating intermediate commits.
- Commit only after all gates pass:
  1. `pytest -q` green
  2. `ruff check src tests` clean
  3. `mypy src tests` clean

## 6. Documentation responsibilities

When public behaviour or the specification changes, update the matching
documents:

| Change | Update |
|--------|--------|
| User-visible behaviour | `README.md`, `docs/development/CLI_USAGE.md`, `docs/development/CONFIG_REFERENCE.md` |
| Configuration keys or precedence | `docs/development/CONFIG_REFERENCE.md`, `docs/development/CONFIG_PRECEDENCE.md` |
| Architecture | `docs/development/ARCHITECTURE_OVERVIEW.md` |
| State of the project | `docs/continuity/CURRENT_STATE.md`, `docs/continuity/NEXT_SESSION.md`, `docs/continuity/OPERATIONAL_DASHBOARD.md` |
| Documentation tree | `docs/DOCUMENTATION_TREE.md` |

## 7. When you are stuck

- Read the matching frozen specification under `docs/specifications/`.
- Consult `docs/continuity/ARCHITECTURE_GUIDE.md` and the invariants in
  `docs/continuity/NEXT_SESSION.md`.
- If a decision is needed: STOP. Do not guess. Consult the Architect through
  the Product Owner (see [CONTRIBUTION.md](CONTRIBUTION.md) — "Questions").

## See also

- [CONTRIBUTION.md](CONTRIBUTION.md) — principles, branches, commits, review.
- [PERFORMANCE_GUIDE.md](PERFORMANCE_GUIDE.md) — benchmarks and profiling.
- [DEBUGGING_GUIDE.md](DEBUGGING_GUIDE.md) — SQLite and dataset troubleshooting.
- [EXTENSION_PATTERNS.md](EXTENSION_PATTERNS.md) — how to add features.