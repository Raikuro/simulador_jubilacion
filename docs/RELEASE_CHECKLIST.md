# Release Checklist — v0.4 Phase 4

**Document Type:** Release Readiness Artefact  
**Status:** Active  
**Last Updated:** 2026-07-29  
**Maintainer:** Implementation Engineer

---

## 1. Installation Verification

- [x] `pip install -e .` installs without errors
- [x] `sim-retire --help` displays all 7 commands
- [x] `sim-retire --version` prints `0.1.0`
- [x] `pyproject.toml` has correct entry point (`cli.main:main`)
- [x] All dependencies listed in `pyproject.toml` (`pyyaml>=6.0`)

## 2. CLI Documentation vs Behaviour

- [x] `sim-retire --help` lists all commands: compare, config, export, list, optimize, run, validate
- [x] `sim-retire validate --help` matches specification
- [x] `sim-retire run --help` matches specification
- [x] `sim-retire list --help` matches specification
- [x] `sim-retire export --help` matches specification
- [x] `sim-retire optimize --help` matches specification
- [x] `sim-retire compare --help` matches specification
- [x] `sim-retire config --help` matches specification
- [x] Exit codes are correctly documented

## 3. Workflow Verification

- [x] Study definition YAML loading works (`sim-retire validate <file>`)
- [x] Dry-run execution works (`sim-retire run --dry-run <file>`)
- [x] Configuration file loading works (`sim-retire --config <file> validate <study>`)
- [x] Help text is accurate for all subcommands
- [x] Unknown commands produce appropriate error exit

## 4. Test Suite

- [x] All CLI tests pass (165)
- [x] All infrastructure tests pass (96)
- [x] All domain tests pass (360)
- [x] All integration tests pass (87)
- [x] All benchmark tests pass (26)
- [x] Total: **768 tests passing**

## 5. Type Checking

- [x] `mypy src/cli/ --strict`: 0 errors
- [x] `mypy src/infrastructure/persistence/ --strict`: 0 errors
- [x] `mypy tests/benchmarks/`: 36 pre-existing untyped-module errors (baseline)
- [x] No new mypy errors introduced

## 6. Code Quality

- [x] `ruff check tests/benchmarks/`: 0 errors
- [x] `ruff check tests/integration/`: 0 errors (5 E501/F841 fixed during freeze)
- [x] No unused imports
- [x] No fixture-import shadowing
- [x] No `zip()` without `strict=True`

## 7. Documentation Consistency

- [x] `README.md` reflects project purpose (timeless)
- [x] `docs/README.md` reflects documentation navigation
- [x] `docs/DOCUMENTATION_TREE.md` matches actual directory structure
- [x] `docs/continuity/CURRENT_STATE.md` reflects current project state
- [x] `docs/continuity/NEXT_SESSION.md` points to current task
- [x] `docs/continuity/OPERATIONAL_DASHBOARD.md` reflects operational status
- [x] `docs/continuity/SOURCE_OF_TRUTH.md` has accurate references
- [x] `docs/continuity/GOVERNANCE.md` is accurate
- [x] `docs/continuity/P4_INTEGRATION_HANDOFF.md` handoff is current

## 8. Repository Structure

- [x] `src/` contains: cli/, engine/, infrastructure/, research/
- [x] `tests/` contains: test_*.py, cli/, infrastructure/, integration/, benchmarks/
- [x] `docs/` contains: continuity/, architecture/, specifications/, roadmaps/, reports/, development/, history/
- [x] `pyproject.toml` has correct configuration
- [x] No stale or orphaned files

## 9. Frozen Package Integrity

- [x] `src/engine/` — unmodified
- [x] `src/research/` — unmodified
- [x] `src/research/optimization/` — unmodified
- [x] `src/cli/commands/` — unmodified (all frozen P3.3-P3.10)
- [x] `src/cli/builders.py` — unmodified
- [x] `src/cli/main.py` — unmodified
- [x] `src/infrastructure/execution/` — unmodified
- [x] `src/infrastructure/persistence/` — unmodified

## 10. Release Readiness

- [x] Version string is consistent (`0.1.0`)
- [x] No hardcoded paths in production code
- [x] All domain objects use `Decimal` (not float) for financial values
- [x] Clean Architecture boundaries maintained
- [x] No architectural deviations in Phase 4
- [x] Release checklist complete

---

## Sign-off

| Role | Name | Date |
|------|------|------|
| Implementation Engineer | | |
| Chief Architect | | |
