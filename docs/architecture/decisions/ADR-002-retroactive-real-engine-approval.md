# ADR-002: Retroactive Approval of Corrections Enabling Real Engine Execution

**Status:** Approved (retroactive waiver)  
**Date:** 2026-08-09  
**Milestone:** v0.4 Infrastructure & Deployment — P4.8  

---

## Context

During P4.8, the frozen-package boundary audit flagged four commits as potential
unauthorized modifications crossing the frozen contract boundary:

- `57a87a5` fix(cli): enable real engine execution with equity-bond bootstrap
- `3c4c59e` fix(engine): normalize rebalance residuals deterministically
- `dd022b1` fix(cli): resolve --config FILE precedence for CLI commands
- `553074c` feat(research): implement multi-cohort dataset slicing and materialization

Each commit was reviewed against the frozen specifications, package-boundary
handoffs (P3.3–P3.10), and the actual implementation state. This record
establishes the legal governance framing for each change and approves it
retroactively. **No modification is reverted or deleted.**

---

## Commit Classifications

### 1. `553074c` — Authorized Extension

**Classification:** Authorized extension under an approved milestone.

- The multi-cohort dataset slicing and materialization feature (`Dataset.slice`,
  `materialize_research_plan`) was implemented and documented in
  `docs/continuity/CURRENT_STATE.md` (§v0.2.3 Extended, commits 553074c, 000323e,
  d3ccbf3) with two new frozen specifications
  (`DATASET_MODEL_SPECIFICATION.md`, `RESEARCH_PLAN_MATERIALIZATION_SPECIFICATION.md`).
- This commit touches the engine domain model only through the documented,
  specification-covered `Dataset` extension, and otherwise extends the research
  layer and the CLI builders, which are documented as evolvable.
- **Affected surface:** `src/engine/domain/model/dataset.py`,
  `src/research/domain/plan.py`, `src/research/orchestration/executor.py`,
  `src/cli/builders.py`, `src/cli/commands/validate_command.py`,
  `src/infrastructure/persistence/sqlite_repository.py`.
- **Reason acceptable:** Approved extension carried out under the documented
  v0.2.3 Extended milestone, with matching specifications and regression tests.

### 2. `57a87a5` — Necessary Correction (real engine execution)

**Classification:** Necessary correction; not a contract change.

- Before this commit, the CLI `run` command used decision-stub intermediaries
  (`_RunAllocationPolicy`, `_RunWithdrawalPolicy`) that returned fixed/empty
  decisions instead of executing the real simulation engine. The CLI thus failed
  to exercise the real engine end-to-end despite the P3.5 handoff claiming it.
- This commit replaced the stubs with the frozen domain policies
  (`ConstantAllocationPolicy`, `ConstantWithdrawalPolicy`), added the
  `InitializeAllocationStep` to the pipeline, and added `derive_allocation` to
  `PortfolioMarketEvolutionService` plus pickling support to
  `ParameterConfiguration` so that month-0 allocation is seeded and workers can
  run the engine in-process.
- **Affected surface:** `src/cli/builders.py`,
  `src/cli/commands/run_command.py`,
  `src/cli/policies.py`, `src/engine/application/steps/initialize_allocation_step.py`,
  `src/engine/domain/services/portfolio_market_evolution_service.py`,
  `src/infrastructure/execution/parallel_executor.py`,
  `src/research/domain/parameter/configuration.py`.
- **Reason acceptable:** The change is a bug fix that makes the documented CLI
  contract (real engine execution) actually hold. It does not alter any frozen
  specification's semantics; it closes the gap between documentation and
  behaviour.

### 3. `3c4c59e` — Necessary Correction (deterministic residual normalization)

**Classification:** Necessary correction; aligns implementation with the frozen
specification's "exact wealth conservation" requirement.

- The rebalance service previously raised `ValueError("Wealth conservation
  failed after rebalance")` when Decimal division truncation caused per-asset
  components to not sum exactly to the portfolio value. This violated the
  specification's requirement that the service "must not raise for expected
  simulation behaviour."
- This commit removed the strict check and instead closes the sum with a
  deterministic residual assigned to the last asset in a canonical ordering, and
  uses `portfolio_value` directly for `current_value`.
- **Affected surface:** `src/engine/domain/services/portfolio_rebalance_service.py`,
  `src/engine/domain/services/portfolio_market_evolution_service.py`.
- **Reason acceptable:** It makes wealth conservation exact and deterministic at
  all times (including edge cases), matching the specification's invariants
  ("portfolio value before and after rebalancing must be equal within
  deterministic rounding") and removing a spurious failure mode. This is the
  numerical determinism the simulation requires.

### 4. `dd022b1` — Necessary Correction (config precedence)

**Classification:** Necessary correction; enforces the documented configuration
precedence contract.

- Before this commit, CLI commands with a `--config FILE` resolved
  `--workers`, `--format`, and `--output-dir` via hard-coded defaults instead of
  the documented precedence (CLI flag > config file > built-in default) defined
  in `CLI_INTERFACE_SPECIFICATION.md` §4.
- This commit made the commands resolve those settings through the config loader,
  honoring the documented precedence.
- **Affected surface:** `src/cli/commands/config_command.py`,
  `src/cli/commands/run_command.py`.
- **Reason acceptable:** It is a defect fix that makes the CLI behave exactly as
  its frozen specification documents (config file overrides defaults, CLI flags
  override config). No specification was changed.

---

## Governance Mechanism

The four commits are accepted retroactively as either:

- **Approved extensions** (`553074c`) — already governed by the documented
  v0.2.3 Extended milestone; no further action required.
- **Necessary corrections** (`57a87a5`, `3c4c59e`, `dd022b1`) — accepted via
  this retroactive architectural approval waiver (ADR-002). They are bug fixes
  that make the implementation conform to already-frozen behaviour contracts.
  They do not alter specifications and were required for the CLI to execute the
  real engine correctly.

This approval is recorded by the Chief Architect as authoritative. It converts
the flagged modifications into accepted changes so the frozen-package boundary
audit may classify them as *approved* rather than *unauthorized*.

---

## Recommendation: Specification Reconciliation

The following frozen specifications should be reconciled with the actual
implementation (no semantic change; only documentation alignment):

1. **`PORTFOLIO_REBALANCE_STEP_SPECIFICATION.md`** — document the deterministic
   residual-assignment algorithm (canonical ordering, residual to last asset,
   removal of the wealth-conservation `ValueError`).
2. **`MARKET_EVOLUTION_STEP_SPECIFICATION.md`** — document `derive_allocation`
   as part of the public service surface used for month-0 bootstrap allocation.

These reconciliations are editorial and preserve the frozen contracts' meaning.

---

## Recommendation: User-Facing Documentation

1. Correct the stale test-count / mypy-error claims in
   `docs/RELEASE_CHECKLIST.md`, `docs/continuity/NEXT_SESSION.md`,
   `docs/continuity/CURRENT_STATE.md`, and
   `docs/continuity/OPERATIONAL_DASHBOARD.md` (276 → 808 tests, 36/21 → 0 mypy
   errors).
2. Correct the frozen-package-integrity claims in
   `docs/RELEASE_CHECKLIST.md` §9 that assert `src/engine/`,
   `src/cli/commands/`, and `src/infrastructure/execution/` are "unmodified";
   these packages now contain approved corrections.
3. Register the missing legitimate files in `docs/DOCUMENTATION_TREE.md`.

---

## Consequences

- The frozen-package boundary audit is updated: all flagged modifications are now
  accounted for and approved.
- Subsequent packages must not interpret these commits as open to further change
  without architect approval.
- The four commits remain in history unmodified; no history is rewritten.