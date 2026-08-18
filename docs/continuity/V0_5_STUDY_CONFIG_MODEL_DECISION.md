# v0.5 — Unify and Clarify the Study-Configuration Model

Status: Approved; implementation **COMPLETE / CLOSED**
Date: 2026-08-17 (approved) · 2026-08-18 (closed)
Scope: v0.5 workstream — study YAML configuration model. Also known as
"Study configuration: distinguish required canonical inputs from sweep
parameters".

This record captures the approved v0.5 workstream in the repository as the
authoritative statement of the target configuration model and its acceptance
criteria. **The implementation is complete and the workstream is formally
closed (2026-08-18).** The single normalized interpretation layer
(`StudyConfiguration`) and the uniform plan pipeline are live for `run` /
`validate` / `compare` / `optimize`; the ERN equivalence gate has passed for
the default (Reference Chained) full grid; the Phase E cleanup of the obsolete
grid/family machinery is complete; and the final architectural review was
accepted with all gates green.

**Final verification (2026-08-18):**
- `pytest tests/` — **970 passed, 6 skipped**.
- `ruff check src tests tools` — **clean**.
- `mypy --strict src tests tools` — **Success (201 source files)**.
- ERN full grid reproduced: 313,020 units · 180 parameter cells · 1,739
  cohorts · 78,255 chained families · default (Reference Chained) output
  **byte-identical** against the established v0.5 oracle.
- `src/engine/**` untouched; no compatibility layer introduced; no unrelated
  Phase 5+ work added.

**Closed-out defect (2026-08-18):** a falsy base-scalar regression was found
and fixed during the final architectural review. `build_study_plan` originally
used `scalar or _DEFAULT`, so a legitimate explicit base scalar of `0.0` (100%
bonds / 0% withdrawal) was silently replaced by the 0.75 / 0.04 defaults. The
old `.get(key, default)` semantics preserved `0.0`, so this was a v0.5-introduced
regression affecting `run` / `validate` / `compare` / `optimize` via the unified
builder. Fixed by substituting the falsy check with an explicit `is not None`
fallback; covered by regression tests
(`tests/cli/test_grid_chaining.py::TestBasePolicyScalarPreservation`). The ERN
gate is unaffected (no base scalars are declared in `ern_grid.yaml`).

**Scope correction (2026-08-17):** v0.5 is a **clean breaking change** to the
internal study-configuration format. There are no external users or released
study-configuration API to preserve, so the old plural/fallback model is
removed, not kept alive through aliases, deprecation warnings, or compatibility
shims. `dataset_family` is **not** part of v0.5.

---

## Context

The study YAML format previously mixed three distinct concepts, which made
`examples/studies/ern_grid.yaml` read as if it were redundant:

1. **Canonical runtime inputs** — what the simulation actually needs (dataset
   source, horizon, initial wealth, window).
2. **Base / fallback policy values** — singular policy descriptions whose
   scalar values are, in the grid path, only fallbacks.
3. **Parameter axes** — sweep dimensions that (in the grid path) override the
   base policy scalars per unit.

The old model also had **two materialization paths with divergent semantics**
(grid vs non-grid), and a per-command inconsistency in how policy keys are
read. The following behaviors were verified against the previous
implementation:

- **Grid path ignored base policy scalars:** in the ERN grid, `0 of 313,020`
  units inherit the base `allocation_policies` / `withdrawal_policy` scalar
  values; every unit is driven by the parameter axes.
- **Non-grid path ignored parameter axes:** `sweep_equity_allocation.yaml`
  yielded every unit at one withdrawal-rate value (mislabeled as a sweep), and
  `multi_policy.yaml` yielded every unit at the last-wins value — in both cases
  the axes were collapsed and only one value reached execution.
- **Key-name inconsistency across commands:** `run`/`validate` read singular
  `withdrawal_policy` and `allocation_policies`; `compare` read a plural
  `withdrawal_policies` list; `optimize` read no YAML withdrawal policy at all.
- **`parameters` was required** — an empty or missing section raised
  `ValueError("At least one parameter axis is required")`.
- **Grid-ness was inferred from shape, not intent** — `is_grid_study =
  bool(datasets_data) or "horizon_years" in params_data`, so the grid/non-grid
  split was a side effect of field names rather than a declared property.
- **Dataset-family semantics:** the four ERN datasets (`ern_swr_h360` …
  `ern_swr_h720`) are prefix storage of a single trajectory; only the canonical
  (longest) is ever sliced. The old `datasets:` list was therefore a *family
  declaration*, not a list of independent datasets — and it is removed by v0.5.

## Decisions

### Decision 1 — `dataset:` is the sole runtime dataset source

- A single canonical `dataset:` entry (`dataset.identifier`) is the only
  runtime dataset source. Every unit is sliced from it; per-unit horizons come
  from the `horizon_years` axis (or the study window).
- The old `datasets:` family declaration is **removed**. `dataset_family` is
  **not** part of v0.5.

### Decision 2 — Singular base policies, with `type` required and scalar optional when swept

- `allocation_policy:` / `withdrawal_policy:` are singular base policies.
- `type` is mandatory and meaningful (it is the actual policy used when not
  overridden). Supported types: `ConstantAllocationPolicy`;
  `FixedRealWithdrawalPolicy` or `ConstantWithdrawalPolicy`.
- The base scalar value is optional when a parameter axis supplies it per unit
  (`allocation_policy.equity_allocation` ↔ `parameters.equity_allocation`;
  `withdrawal_policy.withdrawal_rate` ↔ `parameters.withdrawal_rate`).

### Decision 3 — Universal per-unit override rule for parameter axes

- A `parameters.*` axis matching a policy scalar overrides that scalar **per
  unit**.
- This rule is **identical across all study kinds** — normal studies, sweeps,
  grids, multi-policy, and ERN. The grid/non-grid asymmetry is eliminated.

### Decision 4 — `parameters` becomes optional

- An empty or missing `parameters` section is a **valid single-configuration
  study** (the base policy scalars apply directly as one synthesized
  configuration per cohort). Under the old model this raised an error.

### Decision 5 — Grid-ness is not inferred from shape; `is_grid_study` is removed

- There is exactly **one** policy-resolution rule everywhere. All study kinds
  share one uniform pipeline:
  `StudyConfiguration → parameter configs → ResearchPlan → execution`.
- `is_grid_study` and the grid/non-grid divergence are removed.

### Decision 6 — Normalize policy key names across all commands

- `allocation_policy` and `withdrawal_policy` are the singular canonical keys
  for `run`, `validate`, `compare`, and `optimize`.

### Decision 7 — `compare`: strategies are the generated parameter configurations

- The study's generated parameter configurations are the comparison strategies.
- `--strategy name=value` is an optional repeatable **filter** (AND-ed) that
  selects a subset of configurations; without it every generated configuration
  is compared.
- The old policy-name selection and `--withdrawal-policy` flag are removed.
- Fewer than two selected configurations is a clear validation error.
- One plan is executed once; results are partitioned by configuration.

### Decision 8 — `optimize`: the optimizer owns the candidate withdrawal rates

- A concrete `equity_allocation` is required — from the base scalar or an
  unambiguous single-value `parameters.equity_allocation` axis.
- `parameters.withdrawal_rate` is forbidden (the optimizer owns the candidate
  withdrawal-rate values); every other axis must have exactly one value.
- The YAML `withdrawal_policy.type` supplies the policy mechanism; the optimizer
  supplies the rate via the normalized configuration.

### Decision 9 — Clean replacement; no backward compatibility

- v0.5 is a **clean breaking change** to the internal study-configuration
  format. There is **no backward-compatibility requirement**.
- The old plural/fallback configuration model is **removed**, not kept alive.
- Do **not** preserve the old YAML format, add aliases for legacy keys, or add
  deprecation warnings / compatibility shims.
- All affected examples, tests, documentation, and consumers are updated to the
  new model **as part of the same change**; the new model is the only supported
  model afterwards.

### Decision 10 — No engine changes; ERN datasets retained

- `src/engine/**` is **not modified** by this workstream.
- The four ERN dataset files are **not deleted**; the model change is in how
  their relationship is declared (single canonical `dataset:` + `horizon_years`
  slicing), not in the data itself.

### Decision 11 — Correct the currently-broken examples, do not preserve them

- `sweep_equity_allocation.yaml` and `multi_policy.yaml` are corrected to
  express their **intended** semantics under the new model.
- Their previously-broken behaviour (axes collapsed, all units at one value) is
  **not** preserved.

## Compatibility (breaking change)

- v0.5 **deliberately breaks** the previous study-YAML format. The old
  plural/fallback forms (`datasets:`, `allocation_policies:`, plural or
  misnamed withdrawal keys) are **removed**, not aliased.
- All affected examples, tests, documentation, and consumers are migrated to
  the new model **in the same change**. There is no transitional period.
- The new canonical form works for both single-configuration studies
  (no `parameters`) and parameterized studies.
- Default-vs-new-format ERN output is byte-identical (acceptance criterion).

## Acceptance criteria

- ERN default vs new-format: **byte-identical** — **PASSED** (full 180-cell
  grid; only the elapsed-time line differs).
- `313,020` units and `180` cells reproduced — **PASSED**.
- `ern_grid_smoke.yaml` reproduced — **PASSED** (smoke cell lines
  byte-identical across default / independent / fast-path).
- `basic_minimal.yaml` behavior preserved — **PASSED**.
- `sweep_equity_allocation.yaml` actually sweeps its values — **PASSED**.
- `multi_policy.yaml` actually produces the intended configs (not last-wins) —
  **PASSED**.
- `compare` and `optimize` use the normalized model — **PASSED**.
- No `src/engine/**` changes — **PASSED**.
- The new form works for single-config and parameterized studies; the old
  plural/fallback forms are removed (no compatibility layer) — **PASSED**.
- Full test suite green — **PASSED** (970 passed, 6 skipped on 2026-08-18).

Note: the `--reference-independent` full-grid leg was not re-run in this
session; the earlier smoke gate confirmed cell-line byte-identity across the
independent path, and the accepted gate is the default (Reference Chained)
leg, which is byte-identical at full scale.

## Required documentation

- This decision record (`docs/continuity/V0_5_STUDY_CONFIG_MODEL_DECISION.md`) —
  **now marked COMPLETE / CLOSED** with final verification results.
- Registration in the v0.5 roadmap (`docs/continuity/CURRENT_STATE.md` →
  Future Milestones → v0.5 Study Configuration Model) — **updated to COMPLETE**.

## Risks / edge cases

- **Breaking-change surface:** all examples, tests, docs, and consumers must
  be migrated in a single change; no legacy form remains supported.
- **`type` becoming mandatory** may surface studies that relied on an implicit
  default policy; those must be corrected to state `type` explicitly.
- **Reference Chaining independence:** the runtime identity-prefix checks in
  `src/infrastructure/execution/reference_chaining.py` are an independent
  safeguard; chaining must not come to depend on any family declaration for
  correctness.
- **Related but distinct concern:** the app-configuration abstraction debt
  noted in `P4_INTEGRATION_HANDOFF.md` (Phase 5+, "Configuration abstraction in
  Infrastructure layer") is a separate workstream and is out of scope here.