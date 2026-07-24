# SimulationStatisticsBuilder Input - Architectural Analysis

## Field Usage Analysis

### Current Implementation Review

```python
def build(self, state: SimulationState) -> SimulationStatistics:
    from engine.application.simulation import ExecutionStatus
    
    final_wealth = state.current_wealth or state.context.initial_wealth
    success = (
        state.status == ExecutionStatus.COMPLETED
        and state.failure_state is None
    )
    failure_month = state.period_index if state.failure_state else None

    return SimulationStatistics(
        final_wealth=final_wealth,
        max_drawdown=0.0,
        success=success,
        failure_month=failure_month,
        months_simulated=len(state.monthly_results),
        execution_time_seconds=0.0,
    )
```

---

## Fields Consumed vs. Total Fields

### Consumed Fields (Explicitly Used)

| Field | Source | Purpose | Type |
|-------|--------|---------|------|
| `current_wealth` | `state.current_wealth` | Final portfolio value | `Money \| None` |
| `initial_wealth` | `state.context.initial_wealth` | Reference for success | `Money` |
| `status` | `state.status` | Success determination | `ExecutionStatus` |
| `failure_state` | `state.failure_state` | Failure detection | `str \| None` |
| `period_index` | `state.period_index` | Failure month tracking | `int` |
| `monthly_results` | `state.monthly_results` | Timeline length | `list[MonthlyResult]` |

**Total consumed:** 6 fields (directly or through context)

### Ignored Fields (Not Used)

`SimulationState` contains these fields that are **NOT** accessed:

| Field | Type | Reason Ignored |
|-------|------|----------------|
| `context` | `SimulationContext` | Only `.initial_wealth` accessed, rest ignored |
| `current_date` | `date` | Execution state, not needed for statistics |
| `portfolio` | `Portfolio` | Already represented in `current_wealth` |
| `allocation` | `Allocation \| None` | Execution detail, not needed |
| `allocation_target` | `AllocationTarget \| None` | Execution detail, not needed |
| `allocation_drift` | `object \| None` | Execution detail, not needed |
| `withdrawal_decision` | `object \| None` | Execution detail, not needed |
| `allocation_decision` | `object \| None` | Execution detail, not needed |
| `current_withdrawal` | `Money \| None` | Execution detail, not needed |
| `market_snapshot` | `MarketSnapshot \| None` | Execution detail, not needed |
| `peak_wealth` | `Money \| None` | Not currently used (future use?) |
| `decision_context` | `DecisionContext \| None` | Execution detail, not needed |

**Total ignored:** 12 fields

**Utilization ratio:** 6 / 18 fields = 33%

---

## Why Full SimulationState is Justified

### Design Rationale

#### 1. **Conceptual Boundary: Execution Layer Output**

The `SimulationState` represents the **complete final state after execution completes**. It is the natural, canonical output of the execution layer.

`SimulationStatisticsBuilder` consumes this natural boundary object, which is appropriate because:
- The state is fully populated only after execution ends
- The state represents the complete, authoritative result
- No additional information gathering is needed

#### 2. **Future Extensibility**

Current placeholders will be replaced with calculated metrics:

**Max Drawdown Calculator:**
```python
class DrawdownCalculator:
    def calculate(self, timeline: Sequence[MonthlyResult]) -> float:
        # Needs: monthly_results from state
        # Accesses: state.monthly_results
```

**Execution Time Instrumentor:**
```python
class TimingInstrumentor:
    def calculate(self, state: SimulationState) -> float:
        # Future: might add timing to state
        # Accesses: state fields (to be determined)
```

**CAGR Calculator:**
```python
class CAGRCalculator:
    def calculate(self, 
                 initial_wealth: Money,
                 final_wealth: Money, 
                 months: int) -> float:
        # Needs: state.context.initial_wealth
        #        state.current_wealth  
        #        len(state.monthly_results)
```

By accepting the complete state, the builder doesn't need interface changes when new calculators are added.

#### 3. **Practical Convenience without Coupling**

Alternative: Create a dedicated `SimulationExecutionSummary`:

```python
@dataclass(frozen=True)
class SimulationExecutionSummary:
    current_wealth: Money | None
    initial_wealth: Money
    status: ExecutionStatus
    failure_state: str | None
    period_index: int
    monthly_results: Sequence[MonthlyResult]

class SimulationStatisticsBuilder(ABC):
    @abstractmethod
    def build(self, summary: SimulationExecutionSummary) -> SimulationStatistics:
        raise NotImplementedError
```

**Cost:**
- New type to maintain
- Conversion at boundary (5-10 additional lines)
- Separate concerns but added complexity

**Benefit:**
- Explicit dependency documentation
- Narrower interface
- Clearer layer separation

**Verdict:** The marginal benefit doesn't justify the added maintenance cost for an internal library interface.

#### 4. **Read-Only Semantic**

Although `SimulationState` is mutable during execution, by the time it reaches the builder:
- Execution is complete
- All fields are frozen in their final state
- The state is effectively immutable from the builder's perspective
- There is no risk of the state changing during statistics calculation

#### 5. **Single Source of Truth**

If we created a separate `SimulationExecutionSummary`, we would have:
- `SimulationState` (execution layer output)
- `SimulationExecutionSummary` (extraction for statistics)
- `SimulationStatistics` (final result)

This creates a three-layer transformation chain. Using `SimulationState` directly simplifies:
- `SimulationState` (execution layer output)
- `SimulationStatistics` (final result)

Single transformation, clearer flow.

---

## Intentionality of Design

### Why This Dependency is INTENTIONAL

The dependency on `SimulationState` is **intentional and justified** because:

1. **Appropriate Boundary:** `SimulationState` is the natural output of execution; statistics computation is its natural consumer
2. **Future-Proof:** Adding new statistics doesn't require builder interface changes
3. **No Coupling Risk:** State is read-only, immutable at the point of consumption
4. **Pragmatic:** Simpler than maintaining separate extraction types
5. **Explicit Output:** Statistics process the authoritative final execution state

### What Is NOT Intentional

The builder does NOT depend on execution-time mutability:
- No during-execution access
- No writes back to state
- No intermediate state inspection
- No execution control based on partial state

---

## Alternative Designs Considered

### Option 1: Full SimulationState (Current)
```python
build(state: SimulationState) -> SimulationStatistics
```
**Pros:** Simple, extensible, no conversion
**Cons:** 12 unused fields visible, seems over-broad
**Decision:** ✓ Selected (justified above)

### Option 2: SimulationExecutionSummary (Dedicated Type)
```python
@dataclass(frozen=True)
class SimulationExecutionSummary:
    current_wealth: Money | None
    initial_wealth: Money
    status: ExecutionStatus
    failure_state: str | None
    period_index: int
    monthly_results: Sequence[MonthlyResult]

build(summary: SimulationExecutionSummary) -> SimulationStatistics
```
**Pros:** Explicit dependencies, clear interface
**Cons:** New type, conversion logic, more maintenance
**Decision:** Rejected (cost not justified for internal interface)

### Option 3: SimulationTimeline + Metadata
```python
@dataclass(frozen=True)
class SimulationMetadata:
    current_wealth: Money | None
    initial_wealth: Money
    status: ExecutionStatus
    failure_state: str | None
    period_index: int

build(timeline: SimulationTimeline, 
      metadata: SimulationMetadata) -> SimulationStatistics
```
**Pros:** Separates data from metadata
**Cons:** Two parameters, inconsistent with single result object
**Decision:** Rejected (less coherent than current design)

---

## Verification of Independence

### Statistics Layer Independence

The builder does NOT depend on:
- ✓ Execution algorithm
- ✓ Pipeline step implementations
- ✓ Policy decisions
- ✓ Portfolio mechanics
- ✓ Market calculations
- ✓ Transient execution fields

The builder ONLY depends on:
- Immutable final state fields
- Read-only execution results
- Completed timeline

### Layer Coupling Assessment

```
Execution Layer (Pipeline Steps)
    ↓ produces
SimulationState (mutable during execution)
    ↓ after execution completes
SimulationStatistics Layer
    ↓ receives (read-only)
SimulationState (frozen at this point)
    ↓ produces
SimulationStatistics (frozen result)
```

**Coupling risk:** MINIMAL
- Builder cannot affect execution (reads after completion)
- Builder cannot affect runner (no back-channel)
- Builder sees only final state snapshot
- No circular dependencies

---

## Conclusion

### Architectural Decision: INTENTIONAL AND JUSTIFIED

The dependency on the complete `SimulationState` is:

1. **Appropriate** - Uses the natural boundary output of execution
2. **Safe** - Read-only consumption of completed, immutable state
3. **Extensible** - Future statistics don't require interface changes
4. **Pragmatic** - Simpler than alternative designs
5. **Decoupled** - Statistics layer depends only on results, not mechanism

### Justification Summary

| Aspect | Assessment |
|--------|-----------|
| Conceptually sound | ✓ Yes - natural boundary |
| Practically sound | ✓ Yes - efficient, simple |
| Future-proof | ✓ Yes - supports new calculators |
| Loosely coupled | ✓ Yes - read-only, immutable consumption |
| Maintainable | ✓ Yes - single type, no conversion |

### Recommendation

**KEEP current design.** The dependency on `SimulationState` is justified and requires no changes.

The alternative of creating a separate summary type would:
- Add 5-10 lines of conversion code
- Introduce a new type to maintain
- Provide marginal benefit in clarity
- Not reduce coupling since the data is the same

The current design achieves appropriate separation of concerns while remaining pragmatic and maintainable.

---

## Future Evolvability

If future developments change this assessment, the design can evolve to:

```python
# Phase 1 (current): Accept full state
class SimulationStatisticsBuilder(ABC):
    def build(self, state: SimulationState) -> SimulationStatistics: ...

# Phase 2 (if needed): Create adapter
def state_to_summary(state: SimulationState) -> SimulationExecutionSummary:
    return SimulationExecutionSummary(...)

# Phase 3 (if justified): Switch to narrower interface
class SimulationStatisticsBuilder(ABC):
    def build(self, summary: SimulationExecutionSummary) -> SimulationStatistics: ...
```

The current design doesn't preclude this evolution. The choice to remain with `SimulationState` is pragmatic, not architectural lock-in.
