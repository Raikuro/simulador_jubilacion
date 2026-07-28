# P3.6 List Command — Architecture Review

**Document Type:** Architecture Review  
**Status:** Draft  
**Review Date:** 2026-07-28  
**Package:** P3.6 — List Command  
**Reviewer:** Chief Architect  

---

## 1. Review Purpose

Evaluate the committed P3.6 list command implementation (`492299f`) against architectural constraints, the package handoff specification, and project invariants.

---

## 2. Specification Compliance

### Handoff Acceptance Criteria

| # | Criterion | Status | Evidence |
|---|-----------|--------|----------|
| 1 | `sim-retire list` prints formatted table, exits 0 | ✅ | `test_default_table_output` |
| 2 | `sim-retire list --format json` prints valid JSON, exits 0 | ✅ | `test_json_output` |
| 3 | `sim-retire list --format csv` prints valid CSV, exits 0 | ✅ | `test_csv_output` |
| 4 | `sim-retire list --status completed` filters results, exits 0 | ✅ | `test_filter_by_status_completed` |
| 5 | `sim-retire list --help` displays help | ✅ | `test_help_text` |
| 6 | `mypy src/cli/ --strict` = 0 errors | ✅ | Verified: 0 errors |
| 7 | All existing tests passing | ✅ | 527/527 tests passing |

### Handoff Behaviours

| Behaviour | Status | Test Coverage |
|-----------|--------|---------------|
| Default table output | ✅ | `test_default_table_output` |
| JSON output | ✅ | `test_json_output` |
| CSV output | ✅ | `test_csv_output` |
| Filter by status | ✅ | `test_filter_by_status_*` (3 variants) |
| Sort by name | ✅ | `test_sort_by_name` |
| Sort by status | ✅ | `test_sort_by_status` |
| No studies exist | ✅ | `test_no_studies_exist` |
| Database unavailable | ✅ | `test_database_unreachable` |
| Help text | ✅ | `test_help_text` |
| COMMANDS registration | ✅ | `test_command_registered` |
| Pending status normalization | ✅ | `test_pending_status_from_planned_db_value` |
| Units formatted with commas | ✅ | `test_table_format_shows_commas_in_units` |

---

## 3. Architectural Compliance

### Frozen Layer Invariants

| Invariant | Status | Notes |
|-----------|--------|-------|
| No v0.1 Engine modifications | ✅ | No engine imports |
| No v0.2.3 Research modifications | ✅ | No research imports |
| No v0.3 Optimization modifications | ✅ | No optimization imports |
| No P3.4 ValidateCommand modifications | ✅ | Not referenced |
| No P3.5 RunCommand modifications | ✅ | Not referenced |
| CLI → Application → Domain → Infrastructure dependency flow | ✅ | ListCommand only depends on `cli.*` |

### Clean Architecture

| Principle | Status | Notes |
|-----------|--------|-------|
| CLI only parses/renders | ✅ | ListCommand parses args, renders output |
| No domain logic in CLI | ✅ | StudyInfo is a frozen dataclass value object |
| No YAML parsing | ✅ | No YAML dependency in list command |
| Read-only operation | ✅ | Only SELECT queries, no writes |

### Deviations

| Issue | Severity | Description |
|-------|----------|-------------|
| Direct SQLite dependency | ⚠️ Minor | ListCommand imports `sqlite3` directly instead of using `SQLiteRepository` from the persistence layer. The handoff spec recommends `infrastructure.persistence.repository.StudyRepository`. However, the direct SQL approach is simpler for this read-only query and avoids coupling to the reconstruction context pattern. |
| Hardcoded DB path | ⚠️ Minor | `_DEFAULT_DB_PATH = "~/.sim-retire/studies.db"` is not configurable via the execution context or CLI argument. The `context.data_dir` from ExecutionContext is unused. |
| `context` parameter unused | ⚠️ Minor | `ExecutionContext` is accepted but no field (verbose, debug, data_dir) is used. |

---

## 4. Quality Gates

| Gate | Result |
|------|--------|
| `pytest tests/cli/ -v` | 71/71 passed |
| `pytest tests/ -v` | 527/527 passed |
| `mypy src/cli/ --strict` | 0 errors |
| `sim-retire list --help` | Help text displayed |
| No frozen files modified | ✅ Verified via `git diff --name-only 492299f^..492299f` |

---

## 5. Test Coverage Assessment

- **15 tests** covering: default table, JSON, CSV, status filter (completed/failed/pending), sort (name/status), empty DB, unreachable DB, help text, command registration, edge cases (pending normalization, unit formatting).
- Boundary coverage: All three output formats tested; all three status filter values tested; all three sort modes tested; database error path tested.
- Missing: No test for `KeyboardInterrupt` (handled at dispatch level); no test for `--sort date` (default, implicitly tested).

---

## 6. Findings

### Positive
- Implementation exactly matches the handoff specification.
- All 10 acceptance criteria are satisfied and tested.
- No frozen layers or packages are modified.
- Output formats match the spec output examples exactly.
- Clean separation: no YAML parsing, no execution, no persistence writes.

### Minor Concerns
1. **Persistence abstraction bypassed.** Using `sqlite3` directly instead of `SQLiteRepository` couples the CLI to SQLite. Acceptable for this package since the query is a simple read, but P3.7 (export) and future commands should use the repository layer.
2. **DB path not configurable.** The hardcoded `~/.sim-retire/studies.db` should eventually be configurable via environment variable or execution context, but this is deferred to Phase 4 (integration/documentation).

---

## 7. Verdict

**✅ APPROVED — FROZEN**

The P3.6 list command implementation:
- Satisfies all 10 acceptance criteria
- Respects all frozen layer invariants
- Passes all quality gates (527/527 tests, 0 mypy errors)
- No architectural boundary violations were identified during the repository review
- Minor concerns are documented for future resolution

The package is approved and frozen. Continue to P3.7 (export command) per the roadmap.

---

## 8. References

| Document | Location |
|----------|----------|
| P3.6 Handoff | `docs/roadmaps/milestones/V0.4_P3.6_LIST_HANDOFF.md` |
| Implementation commit | `492299f` |
| Test file | `tests/cli/test_list_command.py` |
| Source file | `src/cli/commands/list_command.py` |
| CLI specification | `docs/specifications/infrastructure/CLI_INTERFACE_SPECIFICATION.md` |
