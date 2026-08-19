# P4.11 Follow-up — Reference Chained Promoted to Default Exact Execution Mode

Status: Approved and implemented
Date: 2026-08-17
Scope: Follow-up to P4.11 (Reference horizon chaining). Supersedes the default
stated in `P4_11_FINALIZATION_DECISION.md` Decision 2 ("the default execution
mode is the independent Reference engine").

This record is the authoritative reference for the CLI execution-mode semantics
after the promotion. The earlier P4.11 decision records remain valid as
historical records of their time; where they describe the *default*, this
document supersedes them.

---

## Context

- The chained Reference executor (`ChainedReferenceSimulationExecutor`) is
  bit-exact with the independent Reference: the full 313,020-unit ERN grid has
  demonstrated 0 mismatches on success, failure month, months simulated, final
  wealth and max drawdown.
- It is materially faster on multi-horizon grids (≈2.6x end-to-end at equal
  worker count; month-work cut exactly 3.0x) and is memory-safe through
  cohort-slice dispatch.
- The independent Reference remains the canonical engine: chaining delegates
  every non-eligible evaluation to it, so no second arithmetic exists.

## Decisions

### Decision 1 — Reference Chained becomes the default exact execution mode, gated on benefit

- With no execution-mode flag, `sim-retire run` routes the plan through the
  chained Reference executor **only when the plan actually benefits from
  horizon chaining** (`expected_reference_chaining_report(plan).derived_results > 0`).
- Multi-horizon, prefix-consistent grid plans therefore run chained by default.
- Single-horizon and other non-chainable plans continue through the existing
  independent Reference dispatch, avoiding grouping/slicing overhead when
  chaining would derive nothing.
- The gate is a pure plan-level computation (no execution); it is deterministic
  and O(plan).

### Decision 2 — The independent Reference is now the oracle/debug/verification mode

- The independent Reference is no longer the normal production execution path.
  It is now explicitly the canonical oracle: the development/verification
  mode against which optimized execution (Reference Chained and Fast Path) is
  tested.
- It remains fully supported and canonical for correctness comparisons and is
  explicitly selectable by users via `--reference-independent`.
- Rationale: users normally should not need it; the exact production path is
  Reference Chained. Keeping it first-class preserves the reference-is-canonical
  invariant and the ability to verify optimization correctness at any time.

### Decision 3 — `--reference-chained` is retained as an explicit force flag

- It remains a valid, accepted flag that explicitly requests the chained
  Reference executor for any plan (even when chaining derives nothing), and is
  kept for backward compatibility with existing scripts.
- After promotion it is semantically equal to the default for eligible plans;
  it is not redundant because it documents intent and mirrors
  `--reference-independent`. Not deprecated.

### Decision 4 — `--fast-path` is unchanged

- Still an explicit, opt-in approximate mode, mutually exclusive with both
  Reference modes.

### Decision 5 — Mutual exclusivity and unchanged correctness invariants

- `--reference-chained`, `--reference-independent` and `--fast-path` are
  mutually exclusive; more than one is rejected explicitly at pre-flight, never
  silently merged.
- No files under `src/engine/**` are changed.
- Fallback semantics are preserved exactly: if Reference Chaining cannot safely
  apply to a unit/family (non-prefix dataset, singleton family, etc.) the
  executor falls back to the independent Reference. Chaining never sacrifices
  correctness for performance.

## Compatibility

- Scripts passing `--reference-chained` keep working unchanged.
- Scripts passing no mode flag get bit-identical results for every plan
  (chained is proven bit-exact with independent); eligible plans run faster and
  the completion summary gains the `Reference Chained:` block.
- `--fast-path` and `--reference-independent` are new/unchanged opt-in flags.

## Required tests

- Default routing: eligible grid → chained executor; non-chainable plan →
  independent dispatch (`simulation_executor is None`).
- `--reference-independent` forces the independent executor on an eligible grid.
- Mutual-exclusion rejection for `--reference-independent` + `--reference-chained`.
- The key contract: **default (Reference Chained) result == independent
  Reference result** on a representative multi-horizon grid, field for field
  (`tests/cli/test_grid_chaining.py::TestGridCliReferenceChained::test_default_chained_equals_independent_reference`).
- E2E: the no-flag default run vs `--reference-independent` on the smoke and
  full ERN grids (opt-in release gates).

## Required documentation

- `docs/development/CLI_USAGE.md`: added `--reference-chained` (previously
  missing from the primary CLI reference) and `--reference-independent`, plus an
  "Execution modes" section describing the default, the oracle, and the fast
  path.

## Risks / edge cases

- The derived-result `max_drawdown` copies the longest-horizon value; safe
  today because the engine's max drawdown is a `0.0` placeholder. If real
  drawdown is ever implemented, derived-horizon semantics must be revisited
  before this default is relied upon.
- Default single-worker chained runs report progress per cohort-slice rather
  than per unit; acceptable and documented.

---

## Status Update (2026-08-19) — Reference Independent removed entirely

Scope: v0.5 follow-up. Two waves: first the public `--reference-independent`
flag was removed (replaced by a test-only switch); then, once the equivalence
was fully established, the independent execution dispatch itself was removed.
Where the sections above describe `--reference-independent` as a
*user-facing execution mode* (Decision 2 "explicitly selectable by users",
Decision 5 mutual-exclusion list, "Compatibility", "Required tests", "Required
documentation"), this section supersedes them.

- The public `--reference-independent` flag is **removed**. The public
  execution model is now exactly two mutually exclusive modes:
  `--reference-chained` (explicit) and `--fast-path` (opt-in approximate), with
  no flag meaning Reference Chained for all plans.
- The independent Reference execution dispatch is **removed entirely**, along
  with the test-only `SIM_RETIRE_FORCE_INDEPENDENT` environment switch that
  previously exposed it. There is no replacement fallback and no compatibility
  path: Reference Chained is the **sole reference execution strategy**.
  - Single-horizon and other non-chainable plans route through Reference
    Chained and are evaluated directly through the canonical Decimal engine
    inside the executor — identical results to the former independent dispatch.
  - The generic execution infrastructure those plans used
    (`parallel_executor.sequential_execute` / `parallel_execute` and the
    default simulation-executor factory) is retained because Reference Chained,
    the fast path, `compare`, and `optimize` all build on it.
- The correctness contract is unchanged and pinned by the chained-vs-canonical
  engine differential tests (`test_reference_chaining.py`,
  `test_grid_chaining.py::test_reference_chained_reproduces_canonical_engine`),
  the fast-path equivalence suite, and the ERN oracle E2E gates.
- Rationale: with Reference Chained proven bit-exact to the canonical engine on
  the full 313,020-unit ERN grid, a separate independent dispatch is redundant
  code and a redundant CLI surface. Removing it eliminates a second execution
  path, its test scaffolding, and its documentation.
- No files under `src/engine/**` changed. All other decisions above (the gated
  default, fallback semantics, bit-exactness) remain in force.
