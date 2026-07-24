# FIRE Backtesting Framework

FIRE Backtesting Framework (FBF) is a deterministic financial simulation engine designed to reproduce and extend the Safe Withdrawal Rate (SWR) studies published by EarlyRetirementNow. The project is built on a rigorously defined Clean Architecture that prioritizes correctness, reproducibility, and maintainability.

## Project Mission
To provide a transparent, testable, and extensible platform for academic-grade financial research and retirement strategy validation.

## Architectural Philosophy
- **Deterministic:** Given identical inputs, the system always produces identical outputs.
- **Specification-Driven:** Implementation is strictly governed by frozen specifications.
- **Clean Architecture:** Separation of concerns between domain logic, research orchestration, and infrastructure.

## Documentation Navigation
- **Human Contributors:** Start with `docs/continuity/HUMAN_CONTRIBUTOR_GUIDE.md`.
- **AI Architects:** Start with `docs/continuity/AI_ARCHITECT_GUIDE.md` and follow the context recovery workflow.
- **Project Structure:** Consult `docs/DOCUMENTATION_TREE.md` for the full documentation map and `docs/continuity/SOURCE_OF_TRUTH.md` to locate specific information.

---

## Technical Overview
The project follows a clean architectural boundary with unidirectional dependencies:
`CLI` → `Research` → `Engine` → `Infrastructure`

- **Engine:** Pure simulation logic (Domain).
- **Research:** Study definition and orchestration.
- **Infrastructure:** External persistence and interfaces.

- **Correctness First** — Mathematical precision > convenience
- **Reproducibility** — Identical inputs → identical outputs (always)
- **Immutability** — Domain objects don't mutate; state transitions are explicit
- **Separation of Concerns** — Engine ≠ Research ≠ Infrastructure
- **Specification-Driven** — Code implements specs; specs don't describe code

## Quality Metrics

```
Total Passing Tests:  276
├─ Engine Tests:       200+
├─ Research Tests:      76+
└─ Infrastructure Tests: 0 (pending v0.4)

Type Checking:   0 mypy errors ✅
Specification Compliance: 100% ✅
Determinism: 100% ✅
```

## Current Status

**Milestone Transition Point:**

- ✅ **v0.1 (Execution Engine)** — Complete, frozen, 200+ tests passing
- ✅ **v0.2.3 (Research Infrastructure)** — Complete, frozen, 76+ tests passing
- 📋 **v0.3 (Optimization Layer)** — Specifications approved, ready for implementation
- 📅 **v0.4+ (Infrastructure & Deployment)** — Planned (SQLite, CLI, parallelization)

**Immediate Next Task:** Implement SWROptimizer component using binary search algorithm.

## Getting Help

### For Questions About:

| Question | Resource |
|----------|----------|
| "What should I implement?" | Read `docs/continuity/OPERATIONAL_DASHBOARD.md` |
| "How should it work?" | Read specification in `docs/specifications/` |
| "Why was it designed this way?" | Read architecture review in `docs/architecture/reviews/` |
| "What's the public API?" | Read `docs/architecture/api/` |
| "Is this in scope?" | Check specification scope section |
| "Am I done?" | Check specification's "Acceptance Criteria" section |

### Documentation Navigation

See `docs/README.md` for complete documentation navigation and category overview.

## License

This project is part of the FIRE Backtesting Framework initiative. See individual component licenses for specific terms.

---

**Version:** 1.0  
**Last Updated:** 2026-07-23  
**Maintainer:** Chief Architect