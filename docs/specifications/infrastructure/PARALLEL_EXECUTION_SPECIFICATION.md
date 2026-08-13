# Parallel Execution Specification

**Document Type:** Behavioral Specification (Frozen)  
**Status:** APPROVED & FROZEN  
**Milestone:** v0.4 Infrastructure & Deployment  
**Responsibility:** Define parallel study execution with ProcessPoolExecutor  

---

## 1. Purpose

This specification defines the **exact behavior** of parallel execution for research studies. It ensures:

- **Determinism:** Parallel results ≡ sequential results
- **Correctness:** All units executed exactly once
- **Isolation:** Unit failures don't cascade
- **Reproducibility:** Same seed → same work distribution
- **Resource safety:** No deadlocks, limited memory growth

---

## 2. Execution Models

### 2.1 Sequential Execution (Baseline)

**Model:** One worker, processes units serially.

```python
def sequential_execute(plan: ResearchPlan) -> ResearchExecutionResult:
    """Execute plan with one worker (baseline)."""
    results = []
    for unit in plan.units:
        result = SimulationRunner.execute(unit)
        results.append(result)
    return aggregate_results(plan, results)
```

**Determinism Guarantee:**

- Input: ResearchPlan (immutable)
- Output: ResearchExecutionResult (identical every time)

### 2.2 Parallel Execution (v0.4)

**Model:** Multiple workers via ProcessPoolExecutor, deterministic work distribution.

```python
def parallel_execute(
    plan: ResearchPlan, 
    max_workers: int
) -> ResearchExecutionResult:
    """Execute plan with multiple workers."""
    # Work is deterministically distributed to workers
    # Results are collected and ordered deterministically
    # Final output ≡ sequential execution
    pass
```

**Critical Invariant:**

$$\text{parallel\_execute}(P, k) = \text{sequential\_execute}(P) \quad \forall k \geq 1$$

---

## 3. Work Distribution Strategy

### 3.1 Granularity: Unit-Level

**Rule:** Work unit is a **PlannedSimulationUnit** (not a simulation step, not a month).

**Rationale:**

- Each unit is independent: no cross-unit state
- Each unit is serializable (frozen dataclass)
- Each unit produces one SimulationResult
- Distribution is straightforward

### 3.2 Batching Strategy

**Rule:** Distribute units in **deterministic batches** to workers.

```python
def create_work_batches(
    plan: ResearchPlan, 
    max_workers: int
) -> Sequence[Sequence[PlannedSimulationUnit]]:
    """
    Create deterministic batches for distribution.
    
    Batch size = ceil(len(plan.units) / max_workers)
    
    Example: 100 units, 4 workers
      Batch 0: units[0:25]   (worker 0)
      Batch 1: units[25:50]  (worker 1)
      Batch 2: units[50:75]  (worker 2)
      Batch 3: units[75:100] (worker 3)
    
    Batches are deterministic: same plan + max_workers → same batches
    """
    batch_size = ceil(len(plan.units) / max_workers)
    batches = []
    for i in range(0, len(plan.units), batch_size):
        batches.append(plan.units[i:i+batch_size])
    return batches
```

**Determinism Guarantee:**

- Same plan + same worker count → same batch assignment
- Batch order is deterministic (0 → batch 0, 1 → batch 1, etc.)
- Results collected in batch order

### 3.3 Worker Function (Pure Function)

**Rule:** Each worker executes **pure function**: units → results.

```python
def worker_execute_units(
    units: Sequence[PlannedSimulationUnit]
) -> Sequence[SimulationResult]:
    """
    Pure function executed by worker process.
    
    Requirements:
    - No side effects
    - No database access
    - No inter-process communication
    - All inputs serializable
    - All outputs serializable
    - Deterministic: same units → same results
    """
    results = []
    for unit in units:
        result = SimulationRunner.execute(unit)
        results.append(result)
    return results
```

**Serialization Contract:**

All inputs and outputs must be pickle-serializable:

- ✅ Serializable: frozen dataclasses, tuples, dicts, strings, Decimals
- ❌ Not serializable: file handles, thread locks, lambda functions

---

## 4. Result Collection & Ordering

### 4.1 Result Collection Pattern

```python
def parallel_execute(
    plan: ResearchPlan,
    max_workers: int
) -> ResearchExecutionResult:
    """
    Collect results in deterministic order.
    """
    batches = create_work_batches(plan, max_workers)
    
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        # map() preserves order: batch_index → batch_results
        batch_results = list(executor.map(worker_execute_units, batches))
    
    # Flatten: sequence of sequences → sequence
    all_results = []
    for batch_results_seq in batch_results:
        all_results.extend(batch_results_seq)
    
    # all_results now in same order as plan.units
    return aggregate_results(plan, all_results)
```

**Ordering Guarantee:**

- Results collected in batch order (not completion order)
- Batch i is processed by executor before batch i+1
- Results within batch preserved in order
- Final ordering matches plan.units ordering exactly

### 4.2 Verification: Determinism Test

```python
def test_parallel_determinism():
    """Verify parallel results ≡ sequential results."""
    
    # Given
    plan = create_test_plan(units=100)
    
    # When: execute sequentially
    seq_result = sequential_execute(plan)
    
    # When: execute with 4 workers (multiple times)
    par_result1 = parallel_execute(plan, max_workers=4)
    par_result2 = parallel_execute(plan, max_workers=4)
    par_result3 = parallel_execute(plan, max_workers=8)
    
    # Then: all results identical
    assert seq_result == par_result1
    assert par_result1 == par_result2
    assert par_result2 == par_result3
```

---

## 5. Error Handling & Failure Isolation

### 5.1 Error Isolation Pattern

**Rule:** One worker failure doesn't stop other workers.

```python
def worker_execute_units_safe(
    units: Sequence[PlannedSimulationUnit]
) -> Sequence[Tuple[Optional[SimulationResult], Optional[Exception]]]:
    """
    Execute units, capturing results and exceptions.
    
    Returns sequence of (result, exception) tuples:
    - Success: (result, None)
    - Failure: (None, exception)
    """
    results = []
    for unit in units:
        try:
            result = SimulationRunner.execute(unit)
            results.append((result, None))
        except Exception as e:
            # Capture error, continue processing
            results.append((None, e))
    
    return results
```

### 5.2 Failure Aggregation

```python
def aggregate_with_errors(
    plan: ResearchPlan,
    batch_results: Sequence[Sequence[Tuple[Result, Exception]]]
) -> ResearchExecutionResult:
    """
    Aggregate results, collecting all errors.
    """
    all_results = []
    all_errors = []
    
    for batch_idx, batch in enumerate(batch_results):
        for unit_idx, (result, error) in enumerate(batch):
            if result is not None:
                all_results.append(result)
            else:
                # Record failure with context
                error_record = ErrorRecord(
                    unit_index=sum(len(b) for b in batch_results[:batch_idx]) + unit_idx,
                    unit=plan.units[unit_idx],
                    error=error,
                    worker_id=batch_idx
                )
                all_errors.append(error_record)
    
    # If any errors, include in result but don't stop execution
    return ResearchExecutionResult(
        results=all_results,
        errors=all_errors,
        success_count=len(all_results),
        failure_count=len(all_errors)
    )
```

### 5.3 Error Types & Handling

| Error Type | Handler | Propagate? | Result |
|-----------|---------|-----------|---------|
| **Unit execution error** | Catch, record, continue | No | Continue execution |
| **Worker crash** | Detect, restart worker | Retry 1x | Retry unit |
| **Worker timeout** | Detect, kill worker | No | Mark units as timeout |
| **Out of memory** | Detect, fail | Yes | Stop execution, report |
| **Disk full** | Detect, fail | Yes | Stop execution, report |

### 5.4 Timeout Handling

```python
def parallel_execute_with_timeout(
    plan: ResearchPlan,
    max_workers: int,
    timeout_seconds: float
) -> ResearchExecutionResult:
    """
    Execute with per-unit timeout.
    
    If any unit takes > timeout_seconds:
    - Interrupt worker
    - Mark unit as TIMEOUT
    - Continue with other units
    """
    # Implementation: Use futures.as_completed with timeout
    pass
```

---

## 6. Resource Management

### 6.1 Worker Process Pool

**Rule:** Reuse ProcessPoolExecutor; don't create new pools for each execution.

```python
class ParallelExecutor:
    def __init__(self, max_workers: int):
        self.executor = ProcessPoolExecutor(max_workers=max_workers)
    
    def execute_plan(self, plan: ResearchPlan) -> ResearchExecutionResult:
        # Reuse self.executor
        batches = create_work_batches(plan, self.executor._max_workers)
        results = list(self.executor.map(worker_execute_units, batches))
        return aggregate_results(plan, results)
    
    def shutdown(self):
        self.executor.shutdown(wait=True)
```

### 6.2 Memory Constraints

**Rule:** Memory usage must be bounded and predictable.

```
Memory per worker = ~200 MB (baseline) + SimulationState
Total memory = baseline + (workers × per-worker) + result buffer

Example: 8 workers, baseline 1 GB
  Total ≈ 1 GB + (8 × 200 MB) + 100 MB results = ~2.7 GB
```

**Constraint:** If memory usage would exceed available RAM, reduce worker count.

### 6.3 File Descriptor Limits

**Rule:** Don't exceed OS file descriptor limits.

```python
# Check available file descriptors
import resource
soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
# Typical Linux: soft=1024, hard=4096
# Don't allocate more workers than (soft - buffer) / files_per_worker
```

---

## 7. Progress Tracking

### 7.1 Progress Callback

```python
class ProgressCallback(Protocol):
    def __call__(self, completed: int, total: int) -> None:
        """Report progress: completed units of total."""
        pass


def parallel_execute_with_progress(
    plan: ResearchPlan,
    max_workers: int,
    progress_callback: Optional[ProgressCallback] = None
) -> ResearchExecutionResult:
    """
    Execute with progress reporting.
    
    Callback invoked after each worker completes a batch.
    """
    pass
```

### 7.2 Progress Display (CLI)

```
[████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░] 33% (333/1000) [2m 15s]
```

**Update Frequency:** Every 2 seconds or after each batch (whichever is more frequent)

---

## 8. Configuration

### 8.1 ExecutionConfig

```python
@dataclass(frozen=True)
class ExecutionConfig:
    """Configuration for parallel execution."""
    
    max_workers: Optional[int] = None
        # None = conservative default (min(8, os.cpu_count()))
        # 1 = Sequential
        # N = Use N worker processes
    
    timeout_seconds: Optional[float] = None
        # Timeout per unit (seconds)
        # None = No timeout
    
    use_processes: bool = True
        # True = ProcessPoolExecutor (for CPU-bound work)
        # False = ThreadPoolExecutor (for I/O-bound work)
    
    chunk_size: int = 1
        # Units per task (advanced tuning)
    
    enable_progress: bool = True
        # True = Report progress callbacks
```

### 8.2 CLI Integration

```bash
# Sequential execution (default)
sim-retire run study.yaml --workers 1

# Parallel with 4 workers
sim-retire run study.yaml --workers 4

# Parallel with CPU count workers
sim-retire run study.yaml --workers -1
```

---

## 9. Deadlock Prevention

### 9.1 Known Deadlock Patterns (Prohibited)

**❌ Pattern 1: Circular dependencies**

```python
# WRONG: Unit execution waits for other units
worker_execute_units(units):
    for unit in units:
        wait_for_other_units(...)  # Deadlock!
        result = SimulationRunner.execute(unit)
```

**✅ Correct:** Each unit independent; no inter-unit waits.

### 9.2 Known Deadlock Patterns (Prohibited)

**❌ Pattern 2: Shared mutable state**

```python
# WRONG: Multiple workers access shared database
shared_db = connect_to_database()
worker_execute_units(units):
    for unit in units:
        shared_db.lock()  # Contention!
        result = SimulationRunner.execute(unit)
        shared_db.unlock()
```

**✅ Correct:** No shared state; each worker independent.

---

## 10. Determinism Proof

### 10.1 Determinism Assumptions

For parallel execution to be deterministic:

1. **Deterministic work distribution:** Same plan + max_workers → same batches ✅
2. **Deterministic batch collection:** executor.map() preserves order ✅
3. **Deterministic per-unit execution:** SimulationRunner deterministic ✅
4. **No inter-unit dependencies:** Units don't communicate ✅
5. **Deterministic aggregation:** Results collected in order ✅

### 10.2 Determinism Invariant

Given:
- Plan P (immutable)
- Configuration C (max_workers, timeout, etc.)
- No randomness in SimulationRunner

Then:
- sequential_execute(P) ≡ parallel_execute(P, C)

**Proof by induction:**
- Base case: 1 worker → sequential execution ✓
- Inductive case: k workers → deterministic batching + ordered collection ✓
- Result: All k > 1 equivalent ✓

---

## 11. Testing Strategy

### 11.1 Determinism Tests

```python
def test_parallel_vs_sequential_identical():
    """Verify parallel ≡ sequential."""
    plan = create_test_plan(units=144)
    
    seq = sequential_execute(plan)
    par = parallel_execute(plan, workers=4)
    
    assert seq.results == par.results
    assert seq.aggregated_stats == par.aggregated_stats

def test_parallel_deterministic_across_runs():
    """Verify parallel deterministic across multiple runs."""
    plan = create_test_plan(units=144)
    
    run1 = parallel_execute(plan, workers=4)
    run2 = parallel_execute(plan, workers=4)
    run3 = parallel_execute(plan, workers=8)
    
    assert run1 == run2
    assert run2 == run3

def test_batching_deterministic():
    """Verify work batching deterministic."""
    plan = create_test_plan(units=144)
    
    batches1 = create_work_batches(plan, max_workers=4)
    batches2 = create_work_batches(plan, max_workers=4)
    
    assert batches1 == batches2
```

### 11.2 Error Isolation Tests

```python
def test_unit_failure_isolation():
    """One unit failure doesn't stop others."""
    plan = create_test_plan_with_failing_unit(units=100, failing_at=50)
    
    result = parallel_execute(plan, workers=4)
    
    assert result.success_count == 99
    assert result.failure_count == 1
    assert result.results contains 99 valid results

def test_worker_failure_recovery():
    """Worker crash triggers retry."""
    plan = create_test_plan(units=100)
    
    result = parallel_execute(plan, workers=4)
    
    # All units should complete despite transient failures
    assert result.success_count == 100
    assert result.failure_count == 0
```

### 11.3 Resource Tests

```python
def test_memory_bounded():
    """Memory usage stays bounded."""
    plan = create_large_test_plan(units=1000)
    
    mem_before = get_memory_usage()
    result = parallel_execute(plan, workers=8)
    mem_after = get_memory_usage()
    
    mem_increase = mem_after - mem_before
    assert mem_increase < 1_000_000_000  # < 1 GB
```

---

## 12. Acceptance Criteria

Parallel execution is complete when:

- [ ] Determinism verified: parallel ≡ sequential
- [ ] Determinism preserved across multiple runs
- [ ] Work batching deterministic and reproducible
- [ ] Error isolation working (no cascading failures)
- [ ] Memory usage bounded and predictable
- [ ] Progress tracking implemented and accurate
- [ ] Timeout handling working
- [ ] 100% of parallel execution tests passing
- [ ] 0 mypy errors
- [ ] Performance acceptable (speedup ≥ (workers - 1) × 0.8)

---

## 13. Implementation Guardrails

### 13.1 MUST

- ✅ Preserve determinism: parallel results ≡ sequential
- ✅ Distribute work in batches (not individual units)
- ✅ Collect results in deterministic order
- ✅ Isolate failures (don't cascade)
- ✅ Preserve all unit ordering
- ✅ Use frozen dataclasses for serialization

### 13.2 MUST NOT

- ❌ Modify SimulationRunner behavior
- ❌ Introduce randomness in work assignment
- ❌ Use shared mutable state between workers
- ❌ Modify plan units during execution
- ❌ Rely on completion order (use batch order)
- ❌ Create circular dependencies between units

---

**Specification Status:** APPROVED & FROZEN  
**Implementation Ready:** YES  
**Next Gate:** Parallel execution implementation
