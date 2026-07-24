# Project Context & Philosophy

**Document Type:** Architectural Context  
**Status:** Active  
**Last Updated:** 2026-07-23

---

## 1. Project Mission

**Mission Statement:**

Develop a deterministic financial simulation engine capable of exactly reproducing the Safe Withdrawal Rate (SWR) studies published by EarlyRetirementNow, and extend it to support new research questions about retirement sustainability.

**Why:** Reproducible, independent verification of SWR research is important for retirement planning. Existing studies rely on proprietary software and closed methodologies. This project makes SWR research transparent, testable, and extensible.

---

## 2. Long-Term Vision

### What We're Building (5-Year Horizon)

**Year 1 (v0.1–v0.2) — Foundation**
- Deterministic execution engine
- Research orchestration infrastructure
- Initial strategy implementations

**Year 2 (v0.3–v0.4) — Production Ready**
- Optimization algorithms (SWROptimizer, StrategyComparator)
- Concrete investment strategies (glidepaths, dynamic withdrawal)
- Persistence layer (SQLite, CSV, results export)
- CLI interface for batch experiments
- Parallel execution support

**Year 3+ (v0.5+) — Extended Research**
- Multi-currency support
- Advanced tax modeling
- Behavioral factors (spending adaptability)
- Monte Carlo stochastic simulation
- Open-source release & community contributions

### Target User

- **Researchers:** Reproduce/extend SWR studies
- **Planners:** Validate retirement strategies
- **Developers:** Build domain-specific simulations
- **Community:** Academic research platform

---

## 3. Architectural Philosophy

### Core Principles (Non-Negotiable)

**1. Correctness First**
- Mathematical precision > convenience
- Decimal arithmetic (never float)
- Comprehensive validation
- Determinism guaranteed

**2. Reproducibility**
- Identical inputs → identical outputs (always)
- No randomness except where explicitly modeled
- Audit trails for all decisions
- Hash-based study fingerprints

**3. Separation of Concerns**
- Engine (pure simulation logic)
- Research (study definition & orchestration)
- Infrastructure (external dependencies)
- NO mixing of concerns

**4. Specification-Driven Development**
- Specifications are contracts
- Code implements specs
- Tests validate spec compliance
- Specs don't describe code

**5. Immutability by Default**
- Value objects are frozen
- State transitions are explicit
- No hidden mutations
- Referential transparency

**6. Policy Abstraction**
- Policies make decisions
- Services execute decisions
- Policies never implement actions
- Easy to swap strategies

**7. Unidirectional Dependencies**
```
CLI → Research → Engine → Infrastructure
```
- Never depend inward
- Infrastructure never visible to domain
- Enables testing without I/O

---

## 4. Quality Objectives

### Quantitative Goals

- **Correctness:** 100% specification compliance
- **Test Coverage:** ≥95% (domain logic)
- **Type Safety:** 0 mypy errors
- **Determinism:** Given identical inputs, output ≡ output (within numerical precision)
- **Reproducibility:** Study fingerprints match across reruns

### Qualitative Goals

- Clean Architecture principles observed
- Domain-Driven Design patterns applied
- Self-documenting code (clear names, minimal comments)
- No technical debt blocks forward progress
- Future contributors understand design quickly

---

## 5. Design Principles

### Domain Modeling

**Money**
- Always Decimal (never float)
- Always EUR (for now)
- Immutable value object
- Type-safe arithmetic

**Portfolio**
- Sequence of asset holdings
- Total value is source of truth
- Derived metrics recalculated from holdings
- Supports arbitrary asset count

**Policy Abstraction**
- AllocationPolicy: Decides target weights
- WithdrawalPolicy: Decides withdrawal amount
- DecisionContext: Immutable input to policies
- No state in policies; all state in context

**Pipeline Composition**
- 8-step monthly pipeline (ordered)
- Each step receives state, returns new state
- No cross-step communication
- Stateless steps = easy testing

### Simulation Model

**Monthly Loop**
```
1. Build decision context (from current state)
2. Apply market returns (evolution)
3. Query allocation policy (allocation decision)
4. Execute rebalancing (adjustment)
5. Query withdrawal policy (withdrawal decision)
6. Execute withdrawal (liquidity reduction)
7. Update derived metrics (wealth, ratios)
8. Capture immutable month snapshot
```

Each month is independent; no carry-over assumptions.

### Research Model

**Study Definition → Plan → Execution → Results**
```
ExperimentDefinition    (declarative: what)
    ↓
CohortGenerator         (temporal windows)
ParameterSweepEngine    (parameter grids)
    ↓
ResearchPlan            (fully materialized)
    ↓
ResearchExecutor        (orchestrates)
SimulationExecutor      (batch simulations)
SimulationRunner        (individual execution)
    ↓
ResearchExecutionResult (aggregated results)
```

No plan construction in executor; plans are pre-built.

---

## 6. Non-Goals (Explicitly Out of Scope)

### Explicitly NOT Doing

- ❌ Real-time trading systems
- ❌ Multi-currency foreign exchange
- ❌ Behavioral finance modeling (v0.1–v0.2)
- ❌ Tax optimization (complex rules deferred)
- ❌ Stochastic Monte Carlo (only deterministic historical simulations)
- ❌ Interactive UI (CLI-only for now)
- ❌ Machine learning predictions
- ❌ High-frequency trading data

### Why These Are Out of Scope

Keeping scope tight allows us to:
1. Achieve correctness faster
2. Ship working software iteratively
3. Maintain architectural clarity
4. Enable community contributions
5. Focus on core SWR research questions

---

## 7. Technology Choices

### Python 3.13+

**Why:** Clear syntax, strong data structures, extensive libraries, strong math support.

**Constraints:**
- Decimal arithmetic built-in
- Dataclasses for immutability
- Type hints throughout
- No external dependencies (core domain layer)

### Zero External Dependencies (Domain Layer)

**Philosophy:** Domain logic belongs only to Python standard library.

**Benefits:**
- No version conflicts
- Easy to audit security
- Minimal attack surface
- Maximum portability

**Infrastructure Layer (Future)**
- SQLAlchemy for ORM (when implemented)
- Click for CLI (when implemented)
- Numpy for advanced numerics (optional optimization)

### Clean Architecture

```
Domain              ← Pure business logic
Application         ← Orchestration (no logic)
Infrastructure      ← External dependencies
Presentation        ← CLI, UI, API
```

Each layer has clear responsibilities; no mixing.

---

## 8. Success Criteria

### For v0.1 (Execution Engine) — ✅ ACHIEVED

- [x] 8-step deterministic monthly pipeline
- [x] Reproduce EarlyRetirementNow SWR calculations
- [x] 276+ passing tests
- [x] 0 mypy errors
- [x] Clean Architecture compliance
- [x] Specification-driven development

### For v0.2 (Research Infrastructure) — ✅ ACHIEVED

- [x] ResearchPlan fully materialized
- [x] ResearchExecutor orchestrates studies
- [x] SimulationExecutor coordinates multi-simulation experiments
- [x] Cohort generation and parameter sweeps working
- [x] 76+ research layer tests passing
- [x] All public APIs frozen and published

### For v0.3 (Optimization & Analytics) — 📋 READY TO START

- [ ] SWROptimizer (binary search for safe rates)
- [ ] StrategyComparator (relative analysis)
- [ ] ResultAggregator (statistical synthesis)
- [ ] ResearchReproducibilityManager (audit & verification)

### For v0.4+ (Production & Deployment)

- [ ] SQLite persistence
- [ ] CSV import/export
- [ ] CLI interface
- [ ] Parallel execution (ProcessPoolExecutor)
- [ ] Result visualization
- [ ] Deployment documentation

---

## 9. Stakeholder Roles & Responsibilities

### Chief Architect

- Owns all architectural decisions
- Approves frozen specifications
- Reviews design trade-offs
- Makes final calls on ambiguities

### Engineer (You)

- Implements specifications exactly
- Writes tests for specification compliance
- Refactors for clarity (never behavior)
- Raises questions; never guesses

### Product Owner

- Communicates with stakeholders
- Decides scope boundaries
- Resolves requirement ambiguities with architect
- Validates completed work

### Community (Future)

- Extends with new strategies
- Reports bugs
- Proposes research studies
- Contributes implementations

---

## 10. Documentation Strategy

### Frozen Documents (Immutable Records)

- **Specifications** — Implementation contracts
- **Architecture Reviews** — Design decisions
- **Roadmaps** — Approved milestones
- **Public API contracts** — Interface guarantees

### Active Documents (Updated as Work Proceeds)

- **CURRENT_STATE.md** — Operational status
- **NEXT_SESSION.md** — Session initialization
- **Implementation Reports** — Completion summaries

### Stakeholder Input Required (TODO)

TODO: Define specific areas where stakeholder input is needed:
- Long-term vision beyond v0.4?
- Tolerance for breaking changes?
- Community governance model?
- Open-source licensing choice?
- Funding/resources for maintenance?

---

## 11. Risk Management

### Known Risks

| Risk | Mitigation | Status |
|------|-----------|--------|
| Specification drift | Frozen specs reviewed before coding | 🟢 Active |
| Architectural decay | Regular Clean Architecture audits | 🟢 Active |
| Testing gaps | Comprehensive test requirements | 🟢 Active |
| Knowledge silos | Extensive documentation | 🟢 Active |
| Performance bottleneck | Optimization deferred; benchmarks ready | 🟢 Managed |

### Operational Constraints

- No breaking changes to frozen specifications without architect approval
- Every change must have accompanying tests
- Determinism must be maintained (no randomness added lightly)
- Dependencies locked to Python standard library in domain layer

---

## 12. Success Metrics

### Technical Metrics

- **Test Pass Rate:** 100% (currently 276/276)
- **Type Checking:** 0 mypy errors (currently 0)
- **Specification Compliance:** 100% (by design)
- **Determinism:** 100% (given same inputs)

### Delivery Metrics

- **v0.1 Completion:** ✅ On time
- **v0.2 Completion:** ✅ On time
- **v0.3 Completion:** TBD (specs ready; implementation pending)
- **v0.4 Production Readiness:** TBD

### Quality Metrics

- **Code Churn:** Low (changes preserve behavior)
- **Defect Rate:** Near-zero (proper testing)
- **Documentation Debt:** None (docs current)

---

## 13. Future Vision (If Approved)

### Phase B: Extended Platform (Years 2–3)

**Possible directions (pending stakeholder decision):**

1. **Tax Modeling**
   - Capital gains tax impact on SWR
   - Tax-loss harvesting effects
   - Roth conversion strategies

2. **Behavioral Adaptation**
   - Spending flexibility models
   - Market timing temptations
   - Retiree psychology

3. **Multiple Geographies**
   - International portfolios
   - Currency hedging
   - Different market histories

4. **Advanced Analytics**
   - Sequence-of-returns risk (Monte Carlo)
   - Drawdown distribution analysis
   - Portfolio longevity curves

### Community Engagement (If Approved)

- Open-source GitHub repository
- Research paper citations
- Academic partnerships
- Community-contributed strategies

---

## Appendix: Key Architectural Decisions (ADRs)

| ADR | Decision | Status |
|-----|----------|--------|
| ADR-001 | Two-layer domain separation (Engine / Research) | ✅ Frozen |
| ADR-002 | Policy-based decision abstraction | ✅ Frozen |
| ADR-003 | Monthly deterministic pipeline | ✅ Frozen |
| ADR-004 | Immutable snapshots (MonthlyResult) | ✅ Frozen |
| ADR-005 | Decimal-based money arithmetic | ✅ Frozen |
| ADR-006 | Injection-based statistics builder | ✅ Frozen |
| ADR-007 | Fully materialized research plans | ✅ Frozen |
| ADR-008 | Stateless research execution | ✅ Frozen |

See `docs/architecture/reviews/` for full ADR details.

---

**Document Status:** Complete & Accurate  
**Next:** Read [CURRENT_STATE.md](CURRENT_STATE.md)
