> **⚠️ Legacy Repository**
>
> This repository is no longer under active development. The FIRE Backtesting Framework has moved to the [`fbf-core`](https://github.com/Raikuro/fbf-core) and [`fbf-cli`](https://github.com/Raikuro/fbf-cli) repositories.
>
> `simulador_jubilacion` is retained for historical and reference purposes only. New development, bug fixes, and feature work should take place in the active repositories listed above. Contributors should not implement new features or architectural changes here.
>
> For the active CLI and application entry point, see [`fbf-cli`](https://github.com/Raikuro/fbf-cli).

---

# FIRE Backtesting Framework

FIRE Backtesting Framework (FBF) is a deterministic financial simulation engine designed to reproduce and extend SWR research. The project is built on a rigorously defined Clean Architecture that prioritizes correctness, reproducibility, and maintainability.

## Project Mission
To provide a transparent, testable, and extensible platform for academic-grade financial research and retirement strategy validation.

## Architectural Philosophy
- **Deterministic:** Given identical inputs, the system always produces identical outputs.
- **Specification-Driven:** Implementation is strictly governed by frozen specifications.
- **Clean Architecture:** Separation of concerns between domain logic, research orchestration, and infrastructure.

## Documentation Navigation
- **Human Contributors** → `docs/continuity/HUMAN_CONTRIBUTOR_GUIDE.md`
- **AI Architects** → `docs/continuity/AI_ARCHITECT_GUIDE.md`
- **Implementation Engineers** → `docs/continuity/NEXT_SESSION.md` & `docs/continuity/CURRENT_STATE.md`
- **Documentation Tree** → `docs/DOCUMENTATION_TREE.md`
- **Canonical Sources** → `docs/continuity/SOURCE_OF_TRUTH.md`
- **Installation & Quickstart** → `docs/development/INSTALLATION_AND_QUICKSTART.md`
- **CLI Reference** → `docs/development/CLI_USAGE.md`
- **Runnable Examples** → `examples/EXAMPLES.md`

---

## Development Lifecycle
The framework strictly separates the **Architectural Workstream** and **Implementation Workstream**.
- **Architectural:** Ends only when specifications, reviews, and API contracts are Approved, Frozen, and committed atomically.
- **Implementation:** Starts only from a frozen architectural package, tracked via `docs/continuity/NEXT_SESSION.md`.

---

## Technical Overview
The project follows a clean architectural boundary with unidirectional dependencies:
`CLI` → `Research` → `Engine` → `Infrastructure`

- **Engine:** Pure simulation logic (Domain).
- **Research:** Study definition and orchestration.
- **Infrastructure:** External persistence and interfaces.

## License
This project is part of the FIRE Backtesting Framework initiative. See individual component licenses for specific terms.