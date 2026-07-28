# ADR-001: CLI Framework Selection

**Status:** Accepted  
**Date:** 2026-07-27  
**Milestone:** v0.4 Infrastructure & Deployment — P3.3

---

## Context

The v0.4 milestone architecture ([INFRASTRUCTURE_DEPLOYMENT_ARCHITECTURE_V0.4.md](../../roadmaps/milestones/INFRASTRUCTURE_DEPLOYMENT_ARCHITECTURE_V0.4.md)) specified `click` as an allowed dependency for the CLI framework.

During P3.3 implementation, the team evaluated whether to use `click` or the standard library `argparse` module.

## Decision

Use `argparse` (Python stdlib) instead of `click`.

## Rationale

- **Zero external dependencies.** The CLI framework should not require third-party packages. `argparse` is available in all supported Python versions.
- **Sufficient for the required feature set.** The CLI needs subcommand dispatch, global options, and help text generation — all natively supported by `argparse`.
- **Simpler dependency management.** Avoiding `click` eliminates a dependency for end users who only invoke the CLI through the installed `sim-retire` script.
- **Reduced maintenance burden.** No need to track `click` version updates or compatibility issues.

## Consequences

- The implementation uses `argparse.ArgumentParser` with `add_subparsers()` for command dispatch.
- All six planned commands (`run`, `list`, `validate`, `export`, `optimize`, `compare`) share a consistent argument interface through `BaseCommand.configure_parser()`.
- The `argparse` decision is enforced by the P3.3 handoff and has been verified: 0 mypy errors, 26 CLI tests passing.
- If future requirements demand advanced CLI features (nested subcommands, auto-generated shell completion), `click` or `typer` may be reconsidered as a v0.5+ enhancement — but any future migration will require a new ADR.

## Affected Documents

| Document | Nature of Impact |
|----------|-----------------|
| [INFRASTRUCTURE_DEPLOYMENT_ARCHITECTURE_V0.4.md](../../roadmaps/milestones/INFRASTRUCTURE_DEPLOYMENT_ARCHITECTURE_V0.4.md) | §7.2 listed `click` as allowed — this ADR documents the refined decision to use `argparse` |
| [V0.4_P3.3_CLI_FRAMEWORK_HANDOFF.md](../../roadmaps/milestones/V0.4_P3.3_CLI_FRAMEWORK_HANDOFF.md) | Specifies `argparse` only — consistent with this ADR |
| [CLI_INTERFACE_SPECIFICATION.md](../../specifications/infrastructure/CLI_INTERFACE_SPECIFICATION.md) | Defines user-facing CLI behavior — unaffected by framework choice |

## Implementation Milestone

P3.3 CLI Entry Point & Framework (commit `90eafbb`)

---

*This ADR was created retrospectively during the 2026-07-27 documentation consistency audit to formally record the architectural refinement.*
