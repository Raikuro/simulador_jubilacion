# Repository Separation & Documentation Audit — Roadmap

**Document Type:** Roadmap (Future Architectural Workstream)
**Status:** PLANNED
**Date:** 2026-08-19
**Dependency:** v0.6 — COMPLETE / CLOSED (2026-08-19)
**Scope:** Architectural planning only. No implementation is performed by this
document; it registers the future workstream and decomposes it into
independently executable tasks.

---

## 1. Workstream Summary

Title: **Repository Separation & Documentation Audit**

Two strictly sequential phases:

- **PHASE 1 — CORE / CLI Repository Separation:** Split the current single
  repository into two independent Python packages/repositories — `fbf/core`
  and `fbf/cli` — with a defensible, responsibility-based architectural
  boundary and a strictly one-way dependency `CLI → CORE`.
- **PHASE 2 — Aggressive Documentation Audit:** Delete, consolidate, correct,
  and only then rewrite the project documentation to match the post-split
  reality.

Phase 2 MUST NOT start until Phase 1 has been fully implemented, independently
validated, and explicitly approved (P1.12 hard gate).

---

## 2. Current Repository Baseline (2026-08-19)

This section is the factual state the workstream must start from. It is a
planning snapshot; task P1.1 must re-verify it before any change.

### 2.1 Repository structure

- Single Git repository at workspace root. Remote `origin` =
  `https://github.com/Raikuro/simulador_jubilacion.git`. Branch `main`.
  Also present: `recovery/phase2-sqlite-2026-07-25` branch.
- `pyproject.toml`:
  - name = `retirement-simulator`, version `0.1.0`, requires-python `>=3.13`.
  - build backend: setuptools, `package-dir = {"" = "src"}`.
  - runtime dependency: `pyyaml>=6.0`.
  - `[project.optional-dependencies].dev`: pytest, pytest-cov, ruff, black, mypy.
  - `[project.scripts]`: `sim-retire = "cli.main:main"`.
  - pytest, coverage, mypy (`strict = true`), ruff, black configured.
- Source layout: `src/{cli,engine,research,infrastructure}/`.
- Test layout: `tests/` with subdirectories `cli/`, `infrastructure/`,
  `integration/`, `benchmarks/`, `e2e/ern/`, `unit/`, plus top-level
  `tests/test_*.py` domain tests.
- `tools/ern/`: standalone ERN reference oracle tooling
  (`reference_oracle.py`, `mem_probe_*.py`).
- `data/ern/`: ERN dataset CSVs/JSONs and the pinned oracle matrix.
- `examples/`: runnable study YAMLs, dataset, config, scripts.
- `docs/`: large documentation tree (continuity, architecture, specifications,
  development, roadmaps, reports, history). See `docs/DOCUMENTATION_TREE.md`.

### 2.2 Current dependency structure (observed)

Clean-architecture layering documented as `CLI → Research → Engine →
Infrastructure`, but the filesystem carries several cross-cutting facts:

- `src/cli/builders.py` implements the entire study-configuration layer
  (`StudyConfiguration`, YAML parsing/validation, `build_study_plan`,
  `_build_unified_parameter_configs`, policy/horizon resolvers, and the
  Cartesian-product materialization) that every command consumes.
- `src/cli/policies.py` defines the **execution-grade concrete policies**
  (`ConstantAllocationPolicy`, `ConstantWithdrawalPolicy`,
  `FixedRealWithdrawalPolicy`) used by the reference engine path.
- `src/infrastructure/execution/reference_chaining.py` (the sole reference
  execution strategy) imports `from cli.policies import ...` — a confirmed
  `core → cli` dependency leak that MUST be resolved by the split.
- `src/cli/fast_path.py` (Fast Path) imports `cli.policies` and
  `infrastructure.execution.parallel_executor`.
- `src/infrastructure/persistence/**` (SQLite repository, codecs, serializers,
  schema, context, dataset cache) is consumed by CLI commands and by the
  persistence integration tests.
- `src/engine/**` is frozen/protected; `src/research/**` is frozen v0.2.3/v0.3
  and v0.5/v0.6 already flowed through `StudyConfiguration` at the CLI boundary.
- The study YAML model is the v0.6 **values-only** model (arrays
  `equity_allocation`, `withdrawal_rate`, `horizon_years`; no `parameters`).

### 2.3 Version / quality baseline

- Latest: v0.6 COMPLETE / CLOSED (2026-08-19). `pytest tests/` = 974 passed,
  4 skipped; ruff clean; `mypy --strict src tests tools` clean (199 files).
- ERN full E2E: 180-cell oracle preserved (313,020 units / 1,739 cohorts /
  78,255 families). Reference Chained is the sole reference strategy; Fast Path
  must remain behaviorally unchanged.

---

## 3. Target Architecture

```
fbf/
├── ARCHITECTURE.md
│
├── core/
│   ├── .git/
│   ├── AGENTS.md
│   ├── README.md
│   ├── src/
│   ├── tests/
│   └── pyproject.toml
│
└── cli/
    ├── .git/
    ├── AGENTS.md
    ├── README.md
    ├── src/
    ├── tests/
    └── pyproject.toml
```

Future (out of scope):

```
fbf/ui/  --  UI frontend, would depend on core only
```

Invariants:

- `fbf/` MUST NOT itself be a Git repository.
- Dependency direction: `CLI → CORE`; `UI (future) → CORE`.
- Never `CORE → CLI`, never `CORE → UI`.
- Core must be an independently installable Python package; CLI consumes core
  as a normal Python dependency (`pip install -e ../core` for local dev).
- No monorepo compatibility layer; no vendored copy of core inside CLI.

---

## 4. Architectural Boundary Principle

Do NOT define the core boundary by moving everything currently under
`src/engine/`, `src/research/`, `src/infrastructure/`, and the CLI boundary by
moving everything under `src/cli/`. The filesystem is evidence, not the
architecture. Determine ownership by **responsibility**.

Central question per component:

> Would a future non-CLI frontend need this functionality?

- Yes → likely core/application functionality.
- Only exists because the user is interacting through a terminal → likely CLI.

Key responsibilities to investigate explicitly (see P1.1):

- `StudyConfiguration` — core application model or CLI transport adapter?
- YAML parsing — is YAML a core format or a CLI transport format?
- study-configuration validation;
- `build_study_plan` / ResearchPlan construction;
- parameter-axis handling (`ParameterAxis`, `ParameterSweepEngine`);
- policy resolution and concrete policy implementations (`cli/policies.py`);
- cohort construction (`CohortGenerator`);
- persistence abstractions vs persistence implementations;
- CLI-specific configuration (`config_command.py`, `load_configuration`);
- command dispatch; terminal presentation; CLI filters (`--strategy`);
- execution controls (`--initial-capital`);
- result formatting / reporting;
- `tools/ern`.

---

## 5. Dependency / Task Graph

```
Repository Separation & Documentation Audit          (Status: PLANNED)
│
├── Phase 1 — Core / CLI Repository Separation
│   │
│   ├── P1.1  Complete Repository Baseline          (no deps)
│   ├── P1.2  Define the CORE Public API            (P1.1)
│   ├── P1.3  Define the Core Boundary              (P1.1, P1.2)
│   ├── P1.4  Define the CLI Boundary               (P1.1, P1.2, P1.3)
│   ├── P1.5  Dependency / Import Audit             (P1.3, P1.4)
│   ├── P1.6  Packaging / Dependency Design         (P1.2, P1.3, P1.4, P1.5)
│   ├── P1.7  Test Separation Design                (P1.1, P1.3, P1.4, P1.6)
│   ├── P1.8  Git Migration Strategy                (P1.1, P1.3, P1.4)
│   ├── P1.9  Core Extraction Implementation        (P1.2, P1.3, P1.5, P1.6, P1.7, P1.8)
│   ├── P1.10 CLI Extraction Implementation         (P1.9)
│   ├── P1.11 Workspace Reconstruction              (P1.9, P1.10)
│   └── P1.12 PHASE 1 VALIDATION GATE               (P1.9, P1.10, P1.11)
│       │
│       ├── approval
│       └── (no Phase 2 task may start before this is approved)
│
└── Phase 2 — Aggressive Documentation Audit
    │
    ├── P2.1  Documentation Inventory               (P1.12)
    ├── P2.2  Code-vs-Documentation Audit           (P2.1)
    ├── P2.3  Aggressive Documentation Deletion     (P2.2)
    ├── P2.4  Documentation Consolidation           (P2.3)
    ├── P2.5  Roadmap / TODO Audit                  (P2.1, P2.2)
    ├── P2.6  Documentation Validation              (P2.2, P2.4, P2.5)
    └── P2.7  FINAL ARCHITECTURAL REVIEW            (P2.6)
```

Phase ordering is hard: each task begins only when all of its declared
dependencies are complete. Tasks P1.9 and P1.10 are sequential (P1.10 depends
on P1.9) because the CLI repository must consume the extracted core.

---

## 6. Phase 1 — Core / CLI Repository Separation

### P1.1 — Complete Repository Baseline

- **Dependencies:** None.
- **Objective:** Produce a factual, complete baseline of the current repository
  before any migration. Everything in section 2 above must be re-verified and
  completed with a full inventory.
- **Allowed scope:** Read-only inspection: repository tree, imports, package
  structure, layers, tests, tools, docs, Git status/history, packaging.
  Produce a baseline report document.
- **Prohibited scope:** No file moves, no code changes, no packaging changes,
  no Git rewrites, no documentation cleanup.
- **Expected deliverables:**
  - Current architecture description;
  - full dependency graph (import-level), including the confirmed
    `reference_chaining → cli.policies` leak;
  - ownership map classifying every module/package into the eight categories
    (definitely core; definitely CLI; likely core-but-in-CLI; likely
    CLI-but-shared; ambiguous; obsolete/removable; test-only; tooling-only);
  - dependency classification into A–E (core runtime, core dev/test, CLI
    runtime, CLI dev/test, tooling-only);
  - ambiguous areas list; proposed boundary candidates; dependency/migration
    risks; Git-history considerations; recommended task order.
- **Validation:** Cross-checked by an independent reviewer (different session)
  against the repository; inventory matches `git ls-files` and filesystem.
- **Handoff:** Path to the baseline report; the confirmed import-leak list;
  the classification tables; any new facts not captured in section 2.

### P1.2 — Define the CORE Public API

- **Dependencies:** P1.1.
- **Objective:** Determine the smallest stable public surface external frontends
  (CLI, future UI, library consumers) are allowed to consume from core. Do NOT
  create abstraction layers merely because a future UI is mentioned. Do NOT
  expose every internal module. Do NOT redesign the engine.
- **Allowed scope:** Analysis and a documented API proposal; may evaluate
  current import consumers to derive the minimal surface.
- **Prohibited scope:** Any code changes; new public API implementations;
  interface/adapter layers not required by an actual consumer.
- **Expected deliverables:** Documented core public API proposal and an explicit
  ownership decision for: `StudyConfiguration`; YAML parsing; whether YAML is a
  core format or a CLI transport format; `build_study_plan`; ResearchPlan
  construction; CLI builders (remain CLI adapters?); CLI-specific configuration
  (remain CLI-only?). This is a KEY architectural decision.
- **Validation:** Architectural review sign-off; API is minimal and justified by
  at least one actual consumer (CLI today, UI as a documented future consumer
  only where genuinely shared).
- **Handoff:** Approved API list; the ownership decisions; rationale; open
  questions for P1.3/P1.4.

### P1.3 — Define the Core Boundary

- **Dependencies:** P1.1, P1.2.
- **Objective:** Translate the analysis into an explicit core ownership map
  (which files/modules/packages become core), based on responsibility, not
  filesystem symmetry.
- **Allowed scope:** Boundary proposal; explicit disposition of each module
  including `engine/**`, `research/**`, `infrastructure/**`, `cli/policies.py`,
  `cli/builders.py`, `cli/fast_path.py`, persistence abstractions vs
  implementations.
- **Prohibited scope:** Any code modification; modifying `src/engine/**` unless
  the analysis proves a genuine boundary violation requires it; redesigning
  working architecture for symmetry.
- **Expected deliverables:** Approved core ownership map (path → core decision,
  with rationale); list of pre-existing issues that are explicitly OUT of scope.
- **Validation:** Architectural review sign-off.
- **Handoff:** Core ownership map; boundary decisions feeding P1.5/P1.6/P1.7/P1.8.

### P1.4 — Define the CLI Boundary

- **Dependencies:** P1.1, P1.2, P1.3.
- **Objective:** Define exactly what belongs in the CLI repository. If current
  CLI code contains application/core logic, the responsibility moves to core —
  it is never duplicated into CLI.
- **Allowed scope:** CLI extraction map and required-refactoring list.
- **Prohibited scope:** Code changes; copying core logic into CLI.
- **Expected deliverables:** Concrete CLI extraction map; explicit
  classification of `builders.py`, command modules, `policies.py`, CLI
  output/reporting, compare filtering (`--strategy`), optimize-specific
  behavior, run/validate behavior, `tools/ern`.
- **Validation:** Architectural review sign-off; boundary is responsibility-based.
- **Handoff:** CLI extraction map feeding P1.5/P1.6/P1.7/P1.8.

### P1.5 — Dependency Inversion / Import Audit

- **Dependencies:** P1.3, P1.4.
- **Objective:** Make the one-way dependency `CLI → CORE` structurally
  enforceable. Target never: `CORE → CLI`.
- **Allowed scope:** Complete import/package/reference audit (runtime,
  configuration, tests, scripts, packaging, entry points, type-checking,
  runtime discovery); a concrete change list to remove the known
  `reference_chaining → cli.policies` leak and any other leak found.
- **Prohibited scope:** Fixing unrelated pre-existing problems opportunistically
  (record them as separate follow-up tasks instead); engine redesign.
- **Expected deliverables:** Final dependency graph; concrete list of changes to
  enforce one-way dependency; list of circular/shared infrastructure preventing
  clean separation.
- **Validation:** Grep-level proof that no `core → cli` import remains after the
  boundary; review sign-off.
- **Handoff:** Change list consumed by P1.9/P1.10; follow-up task list.

### P1.6 — Packaging and Dependency Design

- **Dependencies:** P1.2, P1.3, P1.4, P1.5.
- **Objective:** Define the final Python packaging model BEFORE repository
  extraction. Distribution names MUST be derived from existing project naming
  conventions (current: `retirement-simulator`; proposed target distributions
  `fbf-core` / `fbf-cli` or a name derived from the current convention — the
  exact names are decided here, not invented blindly).
- **Allowed scope:** Packaging specification only (pyproject split, entry
  points, optional deps, build backend, pytest/ruff/mypy configs, CI, scripts);
  classify every dependency A–E.
- **Prohibited scope:** Any packaging file changes during this design task;
  introducing Docker.
- **Expected deliverables:** Final packaging specification: `fbf-core` and
  `fbf-cli` metadata, dependency split table, editable-install local workflow
  (`pip install -e ../core`), assurance that core does not install CLI deps and
  core never depends on CLI.
- **Validation:** Peer review; spec is implementable by P1.9/P1.10.
- **Handoff:** Packaging spec; dependency classification tables.

### P1.7 — Test Separation Design

- **Dependencies:** P1.1, P1.3, P1.4, P1.6.
- **Objective:** Design independent test suites. Core testable with only core
  installed; CLI may depend on core. Avoid duplicating tests; preserve current
  behavioral coverage (974 passed / 4 skipped + ERN E2E).
- **Allowed scope:** Test migration matrix and post-split validation plan;
  classification of every test (core / CLI / cross-repository integration /
  tooling / obsolete), including how E2E/oracle tests and tests currently
  importing `cli.policies`/`cli.builders` from non-CLI suites are rehomed.
- **Prohibited scope:** Moving/editing tests during this design task.
- **Expected deliverables:** Test migration matrix; post-split validation plan;
  decision on which core invariants remain tested in core even if currently
  triggered through CLI.
- **Validation:** Review sign-off; matrix complete (no test left unclassified).
- **Handoff:** Test matrix consumed by P1.9/P1.10.

### P1.8 — Git Migration Strategy

- **Dependencies:** P1.1, P1.3, P1.4.
- **Objective:** Design the safest Git migration to
  `fbf/core/.git` + `fbf/cli/.git` with NO `fbf/.git`. Original history stays
  associated with core; CLI history preserved as reasonably as possible; no
  accidental duplication; no destructive rewrite without explicit
  justification; rollback/recovery defined.
- **Allowed scope:** Evaluation of `git filter-repo`, subtree/filter approaches,
  history-preserving extraction, repository relocation; step-by-step strategy
  document. NO migration execution.
- **Prohibited scope:** Performing the migration; deleting history; creating
  `fbf/.git`.
- **Expected deliverables:** Step-by-step Git migration strategy incl. validation
  and rollback.
- **Validation:** Dry-run rehearsal documented on a throwaway clone in
  `/tmp` (allowed — no workspace changes).
- **Handoff:** Approved migration runbook for P1.9/P1.10.

### P1.9 — Core Extraction Implementation

- **Dependencies:** P1.2, P1.3, P1.5, P1.6, P1.7, P1.8.
- **Objective:** Turn the existing project into the independent core repository
  (files, imports, pyproject, tests, tooling, CI, dependencies, minimal core
  documentation). History preserved per P1.8.
- **Allowed scope:** Repository relocation; core-owned file migration; imports;
  package metadata; pyproject; tests; tooling; CI; dependency declarations;
  documentation necessary for core operation; moving concrete policy
  implementations out of the old `cli/policies.py` where the boundary requires.
- **Prohibited scope:** Redesigning simulation algorithms; introducing
  frameworks; unnecessary behavior changes; UI abstractions; duplicating CLI
  code; documentation cleanup (Phase 2).
- **Expected deliverables:** Independent core repo: installs alone; pytest
  without CLI; ruff/mypy; core E2E/oracle gates; zero CLI runtime dependency;
  zero CLI imports.
- **Validation:** `pip install .` clean; `pytest` green without CLI installed;
  ruff clean; mypy strict clean; ERN oracle gates pass; grep proves no
  `cli` imports in core.
- **Handoff:** Core repo state; remaining CLI-ward surface; any deviations.

### P1.10 — CLI Extraction Implementation

- **Dependencies:** P1.9.
- **Objective:** Create the independent CLI repository consuming core as a
  normal dependency.
- **Allowed scope:** CLI repo files, own `.git`, own pyproject; CLI tests; CLI
  scripts/docs; entry point wiring; editable core install for local dev.
- **Prohibited scope:** Introducing a compatibility monorepo layer; vendoring or
  copying core; duplicating core business logic; any code required by core.
- **Expected deliverables:** CLI repo: installs against versioned core AND local
  editable core; CLI entry point works; CLI tests pass; ruff/mypy; representative
  commands work; core remains independently usable.
- **Validation:** fresh venv install against local editable core; `sim-retire`
  run/validate/compare/optimize representative smoke; CLI pytest; ruff/mypy.
- **Handoff:** CLI repo state; any deviation from P1.6/P1.7.

### P1.11 — Workspace Reconstruction

- **Dependencies:** P1.9, P1.10.
- **Objective:** Build the developer workspace: `fbf/ARCHITECTURE.md`,
  `fbf/core/{README,AGENTS}.md`, `fbf/cli/{README,AGENTS}.md`. NO `fbf/.git`.
- **Allowed scope:** Creating only the minimum necessary workspace-level
  documentation. ARCHITECTURE.md concisely describes FBF, core/CLI/future-UI
  responsibilities, repository boundaries, dependency direction, local
  development, key invariants. AGENTS.md files concise and repo-specific.
- **Prohibited scope:** Phase 2 documentation cleanup; creating `fbf/.git`;
  creating docs dirs for symmetry.
- **Expected deliverables:** The workspace tree as specified.
- **Validation:** Tree shape matches target; no parent `.git`; README/AGENTS
  factual against the split repos.
- **Handoff:** Workspace layout; pointers for P1.12.

### P1.12 — Phase 1 Full Validation Gate (HARD GATE)

- **Dependencies:** P1.9, P1.10, P1.11.
- **Objective:** Verify all Phase 1 acceptance conditions (the 24-point list in
  section 6.1 below). Produce the formal Phase 1 completion report. Phase 2 MUST
  NOT start without explicit approval of this gate.
- **Allowed scope:** Verification, reporting; fixing only gate-failing defects
  directly attributable to the split.
- **Prohibited scope:** Starting Phase 2; opportunistic changes; engine redesign.
- **Expected deliverables:** Formal Phase 1 completion report; explicit
  approval record.
- **Validation:** All 24 points verified with evidence.
- **Handoff:** Approval decision → Phase 2 may begin.

### 6.1 Phase 1 acceptance checklist (P1.12)

1. core is an independent Git repository;
2. CLI is an independent Git repository;
3. no parent Git repository covers both;
4. core installs independently;
5. core tests run without CLI installed;
6. CLI consumes core as a normal Python package;
7. local editable core installation works;
8. core installation does not install CLI;
9. core has no CLI dependency;
10. core has no CLI imports;
11. core contains no terminal presentation;
12. CLI does not duplicate core business logic;
13. core tests pass;
14. CLI tests pass;
15. ruff passes;
16. mypy passes where required;
17. project-specific E2E/oracle tests pass;
18. Fast Path remains unchanged unless explicitly justified;
19. `src/engine/**` has no unnecessary changes;
20. no functional behavior changed except unavoidable packaging/repository
    effects;
21. Git history preserved appropriately;
22. package metadata correct;
23. local development workflow straightforward;
24. minimum documentation required for the split is accurate.

---

## 7. Phase 2 — Aggressive Documentation Audit

Phase 2 starts ONLY after P1.12 is approved. Method:
`DELETE → CONSOLIDATE → CORRECT → ONLY THEN REWRITE WHERE NECESSARY`. Existing
documentation is treated as potentially stale and partially AI-generated.

### P2.1 — Documentation Inventory

- **Dependencies:** P1.12.
- **Objective:** Inventory every documentation artifact across workspace, core,
  CLI, development tooling, roadmap, continuity, and architectural decisions.
  Classify each as: current&useful / current-but-redundant / historical&valuable
  / historical-but-unnecessary / obsolete / speculative / inaccurate / unclear
  ownership / development-only / delete.
- **Allowed scope:** Inventory and classification; no deletion yet.
- **Prohibited scope:** Rewriting; deleting.
- **Expected deliverables:** Keep/delete/consolidate inventory.

### P2.2 — Code-vs-Documentation Audit

- **Dependencies:** P2.1.
- **Objective:** Verify important claims (repository/package boundaries,
  dependency direction, public API, core/CLI responsibilities, configuration
  flow, persistence, execution architecture, commands, installation, local dev,
  CI, quality gates, test architecture) against the actual repos. For
  conflicts: docs fixed if implementation is correct; if code is
  architecturally wrong, a separate architecture task is created — no
  opportunistic code redesign.
- **Expected deliverables:** Discrepancy report and correction plan.

### P2.3 — Aggressive Documentation Deletion

- **Dependencies:** P2.2.
- **Objective:** Delete docs with no genuine maintenance value (AI filler,
  duplicated explanations, generic advice, completed plans, stale migration
  plans, outdated progress reports, old test-count snapshots, transcripts,
  speculative architecture, completed TODOs, redundant summaries, structure
  parroting). Prefer deletion. Do not replace deleted AI slop with equally
  verbose prose.

### P2.4 — Consolidate Current Documentation

- **Dependencies:** P2.3.
- **Objective:** Reach the small hierarchy: `fbf/ARCHITECTURE.md`,
  `core/{README,AGENTS}.md` + `core/docs/` only if genuinely needed,
  `cli/{README,AGENTS}.md` + `cli/docs/` only if genuinely needed. No doc dirs
  for symmetry. Current docs answer "How does the system work NOW?"; historical
  docs survive only with genuine ADR value.

### P2.5 — Roadmap / TODO Audit

- **Dependencies:** P2.1, P2.2.
- **Objective:** Audit roadmap, CURRENT_STATE, NEXT_SESSION, TODOs, continuity
  docs, implementation plans, ADRs. Classify items (planned / implemented /
  obsolete / superseded / unclear). Delete completed/obsolete items without
  genuine historical value. Establish ONE canonical roadmap; no competing
  roadmaps.

### P2.6 — Documentation Validation

- **Dependencies:** P2.2, P2.4, P2.5.
- **Objective:** Search for stale content (old repo structure, old package
  names, monolithic architecture, outdated commands, stale test counts,
  completed roadmap items, core docs referring to CLI internals, incorrect UI
  assumptions, stale install/dev instructions). Validate README instructions in
  clean environments where practical. Verify the final ARCHITECTURE/README/
  AGENTS set.

### P2.7 — Final Architectural Review

- **Dependencies:** P2.6.
- **Objective:** Independent final review answering the 17 questions (core
  independence; install/test without CLI/UI; dependency direction; CLI as
  frontend; UI consumability; repo/package boundaries; test separation; local
  dev; AI agent context isolation; doc accuracy; deletion over rewriting;
  remaining leaks; migration leftovers; unresolved decisions recorded; single
  canonical roadmap; no parent Git repo). Produce final review, unresolved
  issues, follow-ups, and the Phase 2 closure report.

---

## 8. Global Constraints (whole workstream)

- No Docker; no engine redesign; no unnecessary rewrites; no frameworks; no UI
  implementation; no core duplication; no unnecessary abstraction layers; no
  parent Git monorepo; no speculative architectural changes; no silent behavior
  changes; no preserving obsolete docs merely because they exist; no
  style-only doc rewrites; no over-engineering core for a hypothetical UI.
- Interfaces/adapters/service layers/public APIs are introduced ONLY when an
  actual consumer requires them.
- Prefer: existing architecture where sound; minimal changes; explicit
  boundaries; normal Python packaging; independent repositories; editable
  installs; independent test suites; small public APIs; deletion over
  rewriting; explicit architectural decisions; measurable validation.

## 9. Protected Areas

The following require explicit justification before modification (stop →
explain → identify architectural impact → require an explicit decision):

- `src/engine/**`;
- frozen domain structures;
- persistence model;
- Reference Chained execution architecture;
- Fast Path;
- established research semantics;
- existing oracle behavior.

## 10. AI / Session Handoff Rules

Every implementation task must begin with: current prerequisite state; task
objective; allowed files/repositories; prohibited changes; expected final
state. Each task must finish with: files changed; tests/gates executed;
results; known deviations; remaining risks; exact handoff information. No
reliance on conversational memory. Each AI must inspect the actual repository
before modifying it. For Git migration tasks: inspect `git status` first,
verify repo root/remotes/history, never create `fbf/.git`, never delete
history without the approved procedure, stop on unexpected Git state. For doc
tasks: verify against code, delete before rewriting, do not change application
behavior, do not preserve docs solely because they are historical.

---

## 11. Registration Record

- Title: Repository Separation & Documentation Audit
- Status: **PLANNED** (NOT in progress; NO task executed).
- Dependency: v0.6 — COMPLETE / CLOSED (2026-08-19).
- Registered in: `docs/continuity/CURRENT_STATE.md` (Future Milestones section)
  and this roadmap document.
- Explicit dependency: P1.12 → approval → P2.1. No Phase 2 task may start
  before P1.12 is approved.
