# v0.6 — Study Configuration Cleanup: Values-Only Configuration Space

Status: Approved; implementation **COMPLETE / CLOSED**
Date: 2026-08-19 (approved · closed)
Scope: v0.6 workstream — study YAML configuration cleanup. Also known as
"Remove the `parameters` section and base/fallback policy-scalar duality".

This record captures the approved v0.6 workstream as the authoritative
statement of the target configuration model and its acceptance criteria. **The
implementation is complete and the workstream is formally closed
(2026-08-19).** The clean-break values-only configuration model is the **only
supported study YAML model**; the legacy `parameters` / `window_years` /
`cohorts.type` forms are rejected with explicit errors. A final architectural
consistency review confirmed: no obsolete v0.5 concepts remain in production
code, tests, or examples; `StudyConfiguration` carries no legacy fields; the
single-value and multi-value paths share one materialization flow; `compare
--strategy` is a pure selector; `optimize` applies candidates through the new
model; the Cartesian-product ordering and per-cell layout are preserved; and
`src/engine/**` is untouched.

**Final verification (2026-08-19):**
- `pytest tests/` — **974 passed, 4 skipped**.
- `ruff check src tests tools` — **clean**.
- `mypy --strict src tests tools` — **Success (199 source files)**.
- ERN full E2E — **2 passed** (smoke + full 180-cell grid), `src/engine/**`
  untouched, Fast Path unchanged, 313,020 units / 180 cells / 1,739 cohorts /
  78,255 families preserved.
- `src/engine/**` — **zero diff**; Reference Chained and Fast Path unchanged;
  persistence semantics unchanged.

## Context

The v0.5 model still carried a duality: policy sections could declare either a
singular base scalar or a matching `parameters.*` axis, with the axis
overriding the base scalar per unit. In practice every value-bearing axis was
declared under `parameters`, the base scalars were redundant fallbacks, and a
falsy base scalar (`0.0`) regressed once already (see the v0.5 record). v0.6
collapses this to a single rule:

> The study configuration space is the Cartesian product of exactly three value
> arrays, each owned by its section: `allocation_policy.equity_allocation`,
> `withdrawal_policy.withdrawal_rate`, and `cohorts.horizon_years`. There are no
> base scalars, no fallbacks, and no `parameters` section.

Observed v0.5 behaviors that motivated the cleanup:

- **Base/fallback duality:** `parameters.*` axes were effectively mandatory for
  any multi-value study; base scalars were unused fallbacks in every grid.
- **Falsy-value hazard:** `scalar or default` handling silently replaced an
  explicit `0.0` (100% bonds / 0% withdrawal) with the defaults; arrays make
  every declared value explicit and require no `or` fallback.
- **Empty/missing arrays:** the old model allowed omission with implicit
  defaults; the new model rejects empty arrays explicitly.

## Decisions

### Decision 1 — Remove `parameters` completely

- The generic `parameters` section is **removed** — no compatibility parsing,
  aliases, or transformation.
- A study declaring `parameters` is rejected with a clear error, not migrated.

### Decision 2 — Arrays only, owned by their sections

- Every value-bearing field is an array declared directly in its owning
  section:
  - `cohorts.horizon_years: [...]`
  - `allocation_policy.equity_allocation: [...]`
  - `withdrawal_policy.withdrawal_rate: [...]`
- A single-value configuration is written as a one-element array
  (`equity_allocation: [0.75]`).
- Empty arrays are invalid; there are **no implicit defaults**.
- `allocation_policy.type` and `withdrawal_policy.type` remain required.

### Decision 3 — Single Cartesian product; no base/fallback/override layer

- The three arrays form **one** Cartesian product (rightmost axis varies
  fastest: `equity_allocation` slowest → `withdrawal_rate` → `horizon_years`
  fastest). Every generated configuration carries all three values.
- There is no base policy, no fallback, and no override rule. Falsy values
  survive because arrays carry values directly.

### Decision 4 — Remove `cohorts.type` and `cohorts.window_years`

- `cohorts.type` is removed; cohorts are generated as rolling monthly windows
  from `cohorts.horizon_years` (window length = longest declared horizon).
- `cohorts.window_years` is removed; `cohorts.horizon_years` declares each
  per-configuration horizon in years (a prefix slice of the canonical dataset).

### Decision 5 — No CLI options create or override values

- No CLI option may create or override equity-allocation, withdrawal-rate, or
  horizon values. The study YAML is the sole source of study-definition
  parameters.
- `--strategy` remains a **filter** over the configurations already declared in
  the YAML; it cannot inject values.
- `--initial-capital` is unrelated (portfolio starting value) and is retained.

### Decision 6 — `optimize` requires exactly one value in each array

- `optimize` validates that each of the three arrays has exactly one value.
- The optimizer owns the candidate withdrawal rates: each candidate is
  substituted for the declared single `withdrawal_policy.withdrawal_rate`.
- `withdrawal_policy.type` supplies the policy mechanism.

### Decision 7 — Reject old YAML, do not transform

- Old-model YAML (`parameters`, `cohorts.type`, `cohorts.window_years`) is
  rejected with clear, specific errors listing the replacement declarations —
  never silently transformed or defaulted.

### Decision 8 — Preserve ordering, engine, and ERN oracle

- `src/engine/**` is **not modified** by this workstream.
- ERN ordering and the ERN oracle are preserved: 313,020 units / 180 cells /
  1,739 cohorts / 78,255 families; the per-cell layout is unchanged
  (`equity_allocation` slowest → `horizon_years` fastest).
- Reference Chained remains the sole reference strategy; the fast path is
  unchanged.

### Decision 9 — Clean breaking change; no backward compatibility

- v0.6 is a **clean breaking change**. The old `parameters`-based model is
  removed, not kept alive through aliases, deprecation warnings, or
  compatibility shims.
- All affected examples, tests, documentation, and consumers are migrated in
  the same change; the new model is the only supported model afterwards.

### Decision 10 — Keep the v0.5 record historical

- `V0_5_STUDY_CONFIG_MODEL_DECISION.md` remains as a **historical / CLOSED**
  record and is **not rewritten** to describe v0.6.

## Compatibility (breaking change)

- v0.6 deliberately breaks the v0.5 study-YAML format: `parameters`,
  `cohorts.window_years`, and `cohorts.type` are rejected.
- Old-model rejection messages are explicit, e.g.:
  - `parameters is no longer supported; declare values under
    allocation_policy.equity_allocation, withdrawal_policy.withdrawal_rate, and
    cohorts.horizon_years`
  - `cohorts.type is no longer supported; cohorts are generated as rolling
    monthly windows from cohorts.horizon_years`
  - `cohorts.window_years is no longer supported; declare cohorts.horizon_years`
- All examples, tests, and docs are migrated in the same change. There is no
  transitional period.

## Acceptance criteria

- Old-model YAML is rejected with the specific errors above — **PASSED**.
- `parameters` produces no parsed configs anywhere; `*.yaml` fixtures are
  clean of old-model fields — **PASSED**.
- Falsy values survive: `0.0` equity and low rates are preserved as declared —
  **PASSED** (`TestFalsyArrayValuePreservation`).
- Single-value configurations are valid one-element arrays — **PASSED**.
- ERN ordering preserved (5 × 9 × 4 layout, rightmost fastest); smoke grid
  matches the oracle — **PASSED**.
- `src/engine/**` zero-diff — **PASSED**.
- `compare`/`optimize` use the values-only model; `--strategy` filters only —
  **PASSED**.
- Full test suite green — **PASSED** (974 passed, 4 skipped on 2026-08-19).
- `ruff check` / `mypy --strict` clean — **PASSED**.
- Full ERN E2E (`RUN_ERN_E2E_FULL=1`) oracle match — **PASSED** (180-cell
  grid; only the elapsed-time line differs).

## Required documentation

- This decision record (`docs/continuity/V0_6_STUDY_CONFIG_VALUES_ONLY_DECISION.md`) —
  **now marked COMPLETE / CLOSED** with final verification results.
- Registration in the roadmap (`docs/continuity/CURRENT_STATE.md` → Future
  Milestones → v0.6 Study Configuration Cleanup) — **updated to COMPLETE**.
- `docs/development/CLI_USAGE.md`, `docs/specifications/infrastructure/
  CLI_INTERFACE_SPECIFICATION.md`, `docs/development/EXTENSION_PATTERNS.md`,
  and `examples/EXAMPLES.md` describe only the new model.

## Out of scope (explicitly recorded)

- **v0.5+ Community & Extension** (tax modeling, behavioral adaptation,
  multi-currency, open-source release) — **not started**; awaiting stakeholder
  approval.
- **App-configuration abstraction debt** noted in `P4_INTEGRATION_HANDOFF.md`
  (Phase 5+, "Configuration abstraction in Infrastructure layer") — separate
  workstream, **not started**.
- No follow-ups from this workstream are pending beyond the two items above;
  the clean-break configuration model is the only supported study YAML model.

## Risks / edge cases

- **Breaking-change surface:** all examples, tests, docs, and consumers must be
  migrated in a single change; no legacy form remains supported.
- **Falsy arrays:** the three arrays must never flow through `scalar or default`
  style fallbacks; values are read directly from the arrays.
- **Optimize ambiguity:** a multi-value study fed to `optimize` is rejected
  with a clear message; there is no implicit pick of the first value.
- **Reference Chaining independence:** as in v0.5, chaining must not come to
  depend on any family/config declaration for correctness.