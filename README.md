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
- **AI Contributors** → `docs/continuity/AI_ARCHITECT_GUIDE.md`
- **Documentation** → `docs/DOCUMENTATION_TREE.md`
- **Canonical Sources** → `docs/continuity/SOURCE_OF_TRUTH.md`

---

## Technical Overview
The project follows a clean architectural boundary with unidirectional dependencies:
`CLI` → `Research` → `Engine` → `Infrastructure`

- **Engine:** Pure simulation logic (Domain).
- **Research:** Study definition and orchestration.
- **Infrastructure:** External persistence and interfaces.

## License
This project is part of the FIRE Backtesting Framework initiative. See individual component licenses for specific terms.