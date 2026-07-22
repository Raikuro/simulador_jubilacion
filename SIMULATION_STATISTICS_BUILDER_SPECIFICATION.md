# SimulationStatisticsBuilder Behavioral Specification

## Purpose

The `SimulationStatisticsBuilder` is responsible for constructing `SimulationStatistics` from a completed `SimulationState`.

It translates the execution layer's final state into a reporting layer's immutable result, computing summary metrics that characterize the simulation outcome.

---

## Responsibilities

### Primary
- Accept `SimulationState` representing completed execution
- Extract final execution metrics
- Compute derived statistics (now and future)
- Return immutable `SimulationStatistics`

### Constrained
The builder MUST NOT:
- Depend on execution mechanism or transient implementation details
- Access state during execution (only after completion)
- Modify or affect simulation behavior
- Perform financial calculations beyond metric summarization
- Make assumptions about how pipeline steps populate the state

---

## Current Statistics (Immediately Available)

These statistics are available without specialized calculation:

### `final_wealth: Money`
**Source:** `state.current_wealth` (or `state.context.initial_wealth` if None)

**Meaning:** Portfolio value at simulation end

**Derivation:** No calculation; read from pipeline-produced state

**Constraint:** Must handle None gracefully, fallback to initial wealth

### `success: bool`
**Source:** `state.status == ExecutionStatus.COMPLETED and state.failure_state is None`

**Meaning:** Simulation completed without catastrophic failure

**Derivation:** Logical combination of status and failure_state

**Constraint:** `True` only if both conditions met

### `failure_month: int | None`
**Source:** `state.period_index` if `state.failure_state is not None`, else `None`

**Meaning:** Month index when simulation failed (if applicable)

**Derivation:** Conditional extraction from state

**Constraint:** Only set when failure_state is non-None

### `months_simulated: int`
**Source:** `len(state.monthly_results)`

**Meaning:** Number of completed monthly iterations

**Derivation:** Timeline length

**Constraint:** Must reflect actual executed months, not requested horizon

---

## Deferred Statistics (Require Future Calculators)

These statistics require computation beyond simple state extraction:

### `max_drawdown: float`
**Current Value:** `0.0` (placeholder)

**Meaning:** Maximum percentage decline from peak wealth

**Calculation Required:** Timeline analysis
```python
# Pseudocode
peak = max(month.wealth for month in timeline)
max_dd = max((peak - month.wealth) / peak for month in timeline)
```

**Future Implementation:** Dedicated `DrawdownCalculator`

**Integration Pattern:**
```python
class EnhancedStatisticsBuilder(DefaultStatisticsBuilder):
    def __init__(self, drawdown_calc=None):
        self.drawdown_calc = drawdown_calc or SimpleDrawdown()
    
    def build(self, state):
        stats = super().build(state)
        # Replace placeholder with calculation
        max_dd = self.drawdown_calc.calculate(state.timeline)
        return replace(stats, max_drawdown=max_dd)
```

### `execution_time_seconds: float`
**Current Value:** `0.0` (placeholder)

**Meaning:** Elapsed time for simulation execution

**Calculation Required:** Timing instrumentation

**Dependency:** Must be added to execution layer or state

**Future Implementation:** Dedicated `ExecutionTimeInstrumentor`

---

## Future Statistics (Extensible Pattern)

The builder is designed to support additional statistics without modification:

### Potential Future Metrics

#### CAGR (Compound Annual Growth Rate)
```python
# Requires: years_simulated (derived from months_simulated)
# Formula: (final_wealth / initial_wealth) ^ (1 / years) - 1
# Dependencies: state.context.initial_wealth, state.current_wealth
```

#### Rolling Returns
```python
# Requires: timeline analysis at N-month windows
# Dependencies: state.monthly_results with wealth snapshots
```

#### Sequence of Returns Risk (SWR-related)
```python
# Requires: detailed withdrawal and market data
# Dependencies: state.monthly_results, market snapshots
```

#### Inflation-Adjusted Returns
```python
# Requires: cumulative inflation tracking
# Dependencies: state.monthly_results with inflation data
```

### Extension Contract

New statistics are integrated through:

1. **Calculator Pattern:** Create specialized calculator (immutable, pure function)
2. **Builder Injection:** Pass calculator to builder constructor
3. **Composition:** Builder combines base + specialized metrics
4. **Immutable Result:** Return single frozen `SimulationStatistics`

---

## Input Contract

### SimulationState Requirements

The builder depends on `SimulationState` being:

- **Complete:** All execution finished, final state captured
- **Valid:** Consistent and well-formed
- **Immutable (semantically):** No modifications after builder receives it
- **Public-API-Only:** No assumptions about internal fields beyond public contract

### State Field Expectations

| Field | Required | Usage | Constraint |
|-------|----------|-------|-----------|
| `status` | Yes | Success determination | Must be ExecutionStatus.COMPLETED or .FAILED |
| `failure_state` | Yes | Failure detection | None if successful, string description if failed |
| `current_wealth` | Yes | Final value | May be None (uses fallback) |
| `context.initial_wealth` | Yes | Success reference | Used as fallback and baseline |
| `period_index` | Yes | Failure month tracking | Reflects actual execution count |
| `monthly_results` | Yes | Timeline length | List of completed months |

### Constraints

The builder MUST:
- ✓ Treat state as read-only
- ✓ Not depend on execution details
- ✓ Handle edge cases (None values, zero months)
- ✓ Produce deterministic output
- ✓ Support future extension without modification

---

## Output Contract

### SimulationStatistics Requirements

The builder produces immutable `SimulationStatistics` with:

- **Type Safety:** Frozen dataclass, no mutation
- **Completeness:** All required fields populated
- **Accuracy:** Derived correctly from state
- **Consistency:** All fields logically coherent

### Field Accuracy

| Field | Rule | Examples |
|-------|------|----------|
| `final_wealth` | Must equal final portfolio or initial fallback | $1M → $1.2M or fallback |
| `success` | True only if COMPLETED and no failure_state | ✓ COMPLETED + no failure |
| `failure_month` | Set only if failure_state is non-None | 3 (failed month 3) or None |
| `months_simulated` | Equals timeline length, not requested horizon | Requested 12, executed 10 → 10 |

---

## Testing Requirements

### Unit Tests

#### Immediate Availability Tests
- ✓ `final_wealth` extracted correctly
- ✓ `success` computed correctly (completed + no failure)
- ✓ `failure_month` set only on failure
- ✓ `months_simulated` matches timeline length

#### Edge Case Tests
- ✓ Handle `current_wealth = None` (fallback to initial)
- ✓ Handle zero-month simulation
- ✓ Handle immediate failure (month 0)
- ✓ Handle late-stage failure

#### Result Immutability Tests
- ✓ Returned `SimulationStatistics` is frozen
- ✓ No field modification possible
- ✓ No side effects on input state

#### Placeholder Behavior Tests
- ✓ `max_drawdown` returns `0.0`
- ✓ `execution_time_seconds` returns `0.0`
- ✓ Placeholder values documented in docstrings

### Integration Tests

- ✓ Builder works with `DefaultStatisticsBuilder` injection
- ✓ Custom builder injection works
- ✓ Statistics accurate for various simulation outcomes

### Regression Tests

- ✓ No changes to existing field computations
- ✓ Backward compatibility maintained
- ✓ No behavioral changes in current metrics

---

## Determinism

The builder MUST produce identical `SimulationStatistics` given:
- Identical `SimulationState` input
- Same `SimulationState` reference (not copied)

The builder MUST NOT depend on:
- System time
- Randomness
- Filesystem
- Environment
- Execution order (beyond state content)

---

## Error Handling

### Programming Errors (Raise Exception)
- None context
- Missing required fields
- Invalid state (inconsistent status/failure_state)
- Malformed timeline

### Expected Outcomes (Terminate Normally)
- Zero-month simulation (return valid stats)
- Immediate failure (return stats with failure_month=0)
- Portfolio depletion (return stats with success=False)

---

## Future Evolution Path

### Phase 1: Current (Approved)
```python
class SimulationStatisticsBuilder(ABC):
    def build(self, state: SimulationState) -> SimulationStatistics:
        # Returns 4 computed metrics, 2 placeholders
```

### Phase 2: Enhanced (Future)
```python
class EnhancedStatisticsBuilder(SimulationStatisticsBuilder):
    def __init__(self, calculators=None):
        self.drawdown = calculators.get('drawdown') or DefaultDrawdown()
        self.timing = calculators.get('timing') or DefaultTiming()
    
    def build(self, state):
        # Returns 4 computed + 2 calculated metrics
```

### Phase 3: Specialized (Future)
```python
class ResearchStatisticsBuilder(SimulationStatisticsBuilder):
    def build(self, state):
        # Returns 10+ metrics including SWR analysis, rolling returns, etc.
```

**Design Goal:** Allow all three without modifying `SimulationRunner`

---

## Approval Criteria

The specification is approved when:

- ✓ Current statistics are well-defined
- ✓ Placeholder metrics are clearly marked
- ✓ Extension pattern is clear
- ✓ Input/output contracts are explicit
- ✓ Testing strategy is complete
- ✓ Error handling is specified

---

## Recommendation

Proceed with:

1. **Implementation** of `DefaultSimulationStatisticsBuilder` (already complete, review for completeness)
2. **Unit Tests** covering all current metrics and edge cases
3. **Integration Tests** with `SimulationRunner`
4. **Documentation** of placeholder metrics and future extension pattern
5. **Approval** of implementation before proceeding to specialized calculators
