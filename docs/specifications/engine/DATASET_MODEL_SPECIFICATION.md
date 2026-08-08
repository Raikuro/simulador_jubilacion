# Dataset Model Specification

**Document Type:** Behavioral Specification (Frozen)  
**Status:** APPROVED & FROZEN  
**Milestone:** v0.4 Infrastructure & Deployment (Multi-cohort slicing support)  
**Responsibility:** Define the complete data contract for the Dataset domain model  

---

## 1. Purpose

This specification defines the **exact behavior and semantics** of the immutable `Dataset` domain model used by the Engine execution layer.

It establishes:
- The complete field structure and invariants of Dataset
- The distinction between external resource identity (`identifier`) and dataset metadata (`version`)
- The `slice()` method contract for cohort-level dataset materialization
- Preservation guarantees across slicing operations
- Integration with persistence and multi-cohort execution

---

## 2. Dataset Model Structure

### 2.1 Core Fields

The `Dataset` is an immutable frozen dataclass with the following fields:

| Field | Type | Mutability | Description |
|-------|------|-----------|-------------|
| `snapshots` | `Sequence[MarketSnapshot]` | Immutable | Ordered market snapshots indexed by chronological date |
| `frequency` | `str` | Immutable | Snapshot frequency descriptor (e.g., `"monthly"`) |
| `version` | `str` | Immutable | Dataset metadata/version identifier (e.g., `"1.0"`) |
| `identifier` | `str \| None` | Immutable | Optional external dataset resource identity (e.g., from file stem) |

### 2.2 Field Semantics

#### `snapshots`
- **Type:** Non-empty sequence of `MarketSnapshot` objects
- **Ordering:** Strictly chronological by `date` (ascending)
- **Uniqueness:** No two snapshots share the same date
- **Access:** Supports indexing (`dataset[i]`), iteration (`for snap in dataset`), and length (`len(dataset)`)
- **Invariant:** At least one snapshot must be present; invariant validated in `__post_init__`

#### `frequency`
- **Purpose:** Semantic descriptor of snapshot spacing (e.g., `"monthly"`, `"daily"`)
- **Storage:** Plain string, not type-validated beyond string type
- **Usage:** Informational; consumed by analysis layers to interpret snapshot spacing
- **Preservation:** Preserved identically through slicing operations

#### `version`
- **Purpose:** Dataset metadata or versioning information
- **Semantics:** **NOT the canonical persistence identity** (that is `identifier`)
- **Distinction:** `version` is attached metadata; `identifier` is external resource identity
- **Usage:** For datasets without an external resource identity, `version` may be used as a fallback persistence key (see §4 Persistence)
- **Preservation:** Preserved identically through slicing operations
- **Example:** `version="ACWI_EUR_2024"` or `version="1.0"`

#### `identifier`
- **Purpose:** External dataset resource identity (optional)
- **Semantics:** Represents the canonical identity of an external data source or file
- **Source:** Typically derived from file path stem when loading from disk (e.g., filename `ACWI_EUR_2024.json` → `identifier="ACWI_EUR_2024"`)
- **Default:** `None` if not provided at construction
- **Preservation:** Preserved identically through slicing operations
- **Distinctness:** **`identifier` is distinct from `version`**:
  - `identifier` = where the data came from (external resource)
  - `version` = metadata about the data (descriptive tag)
- **Persistence:** `identifier` is the primary key for dataset persistence; `version` is a fallback only when `identifier` is `None` or ambiguous

---

## 3. Dataset Invariants

The following invariants are enforced by `Dataset.__post_init__()`:

### Invariant 1: Non-Empty Snapshots
**Rule:** `len(snapshots) > 0`  
**Rationale:** A dataset must contain at least one market snapshot to define a time window.  
**Violation:** Raises `ValueError("Dataset must contain at least one MarketSnapshot")`

### Invariant 2: Chronological Ordering
**Rule:** `snapshots[i].date < snapshots[i+1].date` for all $0 \le i < len(snapshots) - 1$  
**Rationale:** All operations (slicing, access, analysis) assume chronological ordering; unsorted data corrupts execution.  
**Violation:** Raises `ValueError("Dataset snapshots must be ordered by date")`

### Invariant 3: Date Uniqueness
**Rule:** No two snapshots share the same date value.  
**Rationale:** Slicing and date-based access rely on one-to-one snapshot-to-date mapping.  
**Violation:** Raises `ValueError("Dataset snapshots must have unique dates")`

---

## 4. Public Interface

### 4.1 Structural Access

The Dataset supports the following operations:

```python
def __len__(self) -> int:
    """Return the count of snapshots in this dataset."""
    return len(self.snapshots)

def __getitem__(self, index: int) -> MarketSnapshot:
    """Return the snapshot at integer index."""
    return self.snapshots[index]

def __iter__(self) -> Iterator[MarketSnapshot]:
    """Iterate over snapshots in chronological order."""
    return iter(self.snapshots)

@property
def start_date(self) -> date:
    """The date of the earliest snapshot (first element)."""
    return self.snapshots[0].date

@property
def end_date(self) -> date:
    """The date of the latest snapshot (last element)."""
    return self.snapshots[-1].date
```

### 4.2 Slicing Operation

#### Signature

```python
def slice(self, start_date: date, horizon_months: int) -> Dataset:
    """Return a sliced sub-Dataset starting at *start_date* for *horizon_months*.
    
    Parameters
    ----------
    start_date:
        The date of the first MarketSnapshot in the sliced dataset.
        Must be present in the current dataset.
    horizon_months:
        The exact number of monthly snapshots required in the result.
        Must be a positive integer (> 0).
    
    Returns
    -------
    Dataset
        A new immutable Dataset containing exactly *horizon_months* snapshots
        starting from *start_date* (inclusive).
        
        The returned Dataset has:
        - `snapshots`: subsequence [start_idx, start_idx + horizon_months)
        - `frequency`: identical to source
        - `version`: identical to source
        - `identifier`: identical to source (preservation of external identity)
    
    Raises
    ------
    ValueError
        If start_date is not present in the dataset snapshots.
        If horizon_months is not a positive integer (≤ 0).
        If there are insufficient snapshots available starting from start_date
        (e.g., only 10 snapshots available but 12 requested).
    """
```

#### Behavior

1. **Input Validation:**
   - Validates `start_date` is a `date` instance
   - Validates `horizon_months` is a positive integer (not `bool`, not ≤ 0)

2. **Date Lookup:**
   - Searches the dataset for a snapshot matching `start_date`
   - Raises `ValueError` if not found

3. **Availability Check:**
   - Computes available snapshots from start_idx forward: `len(snapshots) - start_idx`
   - Raises `ValueError` if `available < horizon_months`

4. **Slicing:**
   - Extracts snapshots: `snapshots[start_idx : start_idx + horizon_months]`
   - Constructs a new frozen Dataset instance with:
     - Sliced snapshots tuple
     - Original `frequency`, `version`, `identifier` values

5. **Preservation Semantics:**
   - **Frequency:** Preserved unchanged (assumes monthly data remains monthly after slicing)
   - **Version:** Preserved unchanged (dataset version does not change with subset)
   - **Identifier:** **Preserved unchanged** (the external resource identity remains the same; only the time window changes)

#### Determinism

Given:
- An identical source Dataset
- Identical `start_date` and `horizon_months` parameters
- No side effects or randomness

The `slice()` method returns a Dataset with:
- Identical snapshot values
- Identical frequency, version, identifier
- Identical ordering

---

## 5. Interaction with Cohort-Level Execution

### 5.1 Role in Multi-Cohort Materialization

The `Dataset.slice()` method is designed to support multi-cohort studies:

1. **Cohort Definition:** Each cohort is defined by a `CohortSpecification` with a `start_date`
2. **Slicing:** For each cohort, the full experiment dataset is sliced to the cohort's start date and experiment horizon
3. **Result:** A cohort-aligned dataset containing exactly the market history needed for that cohort's execution
4. **Sharing:** All parameter sweep units within the same cohort share the sliced dataset instance (deduplication by planning component)

### 5.2 Preservation of Identity Through Materialization

The `identifier` field is preserved through slicing to maintain external resource traceability:

- **Original load:** `Dataset` loaded from file `ACWI_EUR_2024.json` → `identifier="ACWI_EUR_2024"`
- **Slicing:** `dataset.slice(start_date=1980-01-01, horizon_months=360)` → returns Dataset with `identifier="ACWI_EUR_2024"`
- **Persistence:** When the experiment is saved, the `identifier` persists in the database, allowing reconstruction of the original external dataset

This ensures that dataset provenance is never lost during execution, even after cohort-level materialization.

---

## 6. Persistence Implications

### 6.1 Canonical Persistence Identity

The persistence layer uses Dataset identity as follows:

- **Primary:** `dataset.identifier` (external resource identity)
- **Fallback:** `dataset.version` (only if `identifier` is `None`)

When persisting an experiment:
- If `identifier` is not None: persist `identifier`
- If `identifier` is None: persist `version`

When loading an experiment:
1. First attempt to resolve by canonical `identifier`
2. If not found and `identifier` was actually a version string: resolve by `version` (legacy fallback)
3. Fail with `StudyNotFoundError` if no unique match

### 6.2 Version Fallback Logic

The `DefaultDatasetResolver` implements three-step resolution:

1. **Canonical Identifier Lookup** — Direct key match on `identifier`
2. **Identifier Field Search** — Search all known datasets for matching `dataset.identifier`
3. **Legacy Version Fallback** — If exactly one dataset has `dataset.version == identifier`, resolve it

This fallback preserves backward compatibility with datasets persisted before `identifier` was introduced.

---

## 7. Immutability and Thread Safety

### 7.1 Frozen Dataclass Contract

`Dataset` is a frozen dataclass (`@dataclass(frozen=True)`):

- All fields are immutable after construction
- Attempting to modify any field raises `FrozenInstanceError`
- The sequence of snapshots is immutable (frozen dataclass property)

### 7.2 Snapshot Sequence Mutability

The `snapshots` field is typed as `Sequence[MarketSnapshot]`:

- Immutable abstract type (not `list` or `MutableSequence`)
- Actual implementation uses tuple for frozen safety
- No modification operations are possible through the public interface

### 7.3 Thread Safety Implications

Given the frozen contract:

- Multiple threads can safely hold references to the same Dataset
- No thread-local state or shared mutable fields
- Slicing operations create new immutable Dataset instances (never modify existing ones)

---

## 8. Testing Requirements

### 8.1 Construction and Invariants

- [x] Construction with valid snapshots succeeds
- [x] Empty snapshots raises `ValueError`
- [x] Unordered snapshots raises `ValueError`
- [x] Duplicate-date snapshots raises `ValueError`
- [x] Single snapshot is valid

### 8.2 Structural Access

- [x] `__len__()` returns correct snapshot count
- [x] `__getitem__(i)` returns correct snapshot by index
- [x] `__iter__()` iterates in order
- [x] `start_date` property returns first snapshot date
- [x] `end_date` property returns last snapshot date

### 8.3 Slicing Operations

- [x] Valid slice returns correct sub-sequence
- [x] Valid slice preserves frequency, version, identifier
- [x] `start_date` not in dataset raises `ValueError`
- [x] `horizon_months <= 0` raises `ValueError`
- [x] Insufficient snapshots raises `ValueError`
- [x] Slice with single snapshot (horizon_months=1) succeeds
- [x] Slice at end of dataset with exact horizon succeeds

### 8.4 Determinism and Preservation

- [x] Identical inputs produce identical sliced outputs
- [x] `identifier` preserved through slicing (including when `identifier=None`)
- [x] `version` preserved through slicing
- [x] `frequency` preserved through slicing
- [x] Sliced dataset snapshots are identical copies of original subsequence

---

## 9. Approval Criteria

This specification is approved when `Dataset` is verified to:

1. Enforce all three structural invariants (non-empty, ordered, unique dates)
2. Implement slicing with correct input validation and output materialization
3. Preserve `identifier`, `version`, and `frequency` through slicing
4. Support deterministic, immutable, thread-safe operations
5. Distinguish semantically between `identifier` (external resource) and `version` (metadata)
6. Pass all verification tests without modification to the specification

---

**Specification Status:** APPROVED & FROZEN  
**Implementation Ready:** YES  
**Next Gate:** Cohort-level materialization via `materialize_research_plan()`
