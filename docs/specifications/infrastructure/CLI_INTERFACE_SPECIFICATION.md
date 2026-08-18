# CLI Interface Specification

**Document Type:** Behavioral Specification (Frozen)  
**Status:** APPROVED & FROZEN  
**Milestone:** v0.4 Infrastructure & Deployment  
**Responsibility:** Define the complete CLI contract for user interaction  

---

## 1. Purpose

This specification defines the **exact command syntax, argument contracts, help text, error messages, and exit codes** for the FIRE Backtesting Framework CLI.

It serves as the contract between:
- **User** ↔ **CLI** (what users see and type)
- **CLI** ↔ **Application Layer** (how CLI invokes domain logic)

---

## 2. Entry Point & Global Options

### 2.1 Command Syntax

```
sim-retire [GLOBAL_OPTIONS] COMMAND [COMMAND_OPTIONS]
```

### 2.2 Global Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--version` | Flag | — | Print version and exit |
| `--help` | Flag | — | Print help and exit |
| `--verbose` | Flag | False | Enable verbose output |
| `--debug` | Flag | False | Enable debug logging to stderr |
| `--config FILE` | Path | `~/.sim-retire/config.yaml` | Configuration file |

### 2.3 Exit Codes

| Code | Meaning | Examples |
|------|---------|----------|
| `0` | Success | Command executed successfully |
| `1` | Execution Error | Study failed, results invalid, I/O error |
| `2` | Validation Error | Invalid arguments, missing files, bad format |
| `3` | Configuration Error | Invalid config file, missing required setting |
| `4` | Database Error | Corrupted database, permission denied |
| `130` | Interrupted | User pressed Ctrl+C |

---

## 3. Command Specifications

### 3.1 Command: `sim-retire run`

**Purpose:** Execute a research study and persist results.

#### Syntax

```
sim-retire run [OPTIONS] STUDY_FILE
```

#### Arguments

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `STUDY_FILE` | Path | ✅ YES | Path to YAML experiment definition file |

#### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--output-dir` | Path | `./results/` | Directory for output files |
| `--workers` | Integer | 1 | Number of parallel workers (1-N) |
| `--format` | Choice | `csv` | Output format: `csv`, `json`, `sqlite`, `all` |
| `--persist-study` | Flag | True | Save study definition to database |
| `--dry-run` | Flag | False | Validate plan without executing |
| `--resume` | Study ID | None | Resume interrupted execution |
| `--timeout` | Integer | 3600 | Max execution time in seconds |

#### Behavior

**Execution Flow:**

1. Parse and validate STUDY_FILE (YAML)
2. Load ExperimentDefinition from file
3. Create ResearchPlan (if not provided)
4. Validate ResearchPlan completeness
5. If `--dry-run`: print plan and exit 0
6. Execute study (sequential or parallel based on `--workers`)
7. Persist results to database
8. Export results to specified format(s)
9. Print summary and exit 0

**On Failure:**

- Exit code 2 if STUDY_FILE invalid
- Exit code 1 if execution fails
- Exit code 130 if interrupted (Ctrl+C)

#### Example Usage

```bash
# Execute study with 4 workers, output to SQLite
sim-retire run studies/part19.yaml --workers 4 --format sqlite

# Dry-run to validate study
sim-retire run studies/part19.yaml --dry-run

# Execute with timeout
sim-retire run studies/part19.yaml --timeout 7200 --workers 8

# Resume interrupted execution
sim-retire run studies/part19.yaml --resume study-12345
```

#### Output

**Standard Output:**

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Research Study Executor
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Study:          part19_equity_glidepaths (v1.0)
Cohorts:        144 (monthly rolling, 1871-2024)
Parameters:     12 (sweep: equity allocation 0-100% × steps 0-10)
Total Units:    1,728 simulations
Workers:        4 (parallel execution)
Estimated Time: ~8 minutes

Executing...
[█████░░░░░] 50% (870/1,739) [elapsed: 1m 32s] [ETA: 1m 31s]
```

**Progress Updates:**

- Rendered in-place on a single line, at most every ~2 seconds (or per batch when
  batches complete slower than that): `[progress_bar] percentage (current/total) [elapsed: HHh MMm SSs] [ETA: HHh MMm SSs]`
- Percentage is `completed/total × 100` rounded to the nearest integer; the bar is
  10 blocks (filled = percentage of total, `█` = done, `░` = remaining).
- `elapsed` and `ETA` are rendered by the shared duration formatter
  (`Xs`, `Xm Ys`, or `Xh Ym Zs`).
- **ETA is computed from observed throughput** (completed units ÷ elapsed time),
  never from a static per-unit constant. It adapts continuously as execution
  proceeds and converges once enough units have completed.
- Nothing is rendered when stdout is not a TTY (scripts, pipes, subprocesses such
  as the black-box E2E harness): stdout stays machine-parseable.
- The progress line is cleared before the final summary is printed.
- Press Ctrl+C to interrupt (execution can be resumed)

**Final Summary:**

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Execution Complete
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Status:         SUCCESS
Units Run:      1,728
Units Failed:   0
Execution Time: 8m 23s
Results:
  - CSV:    results/part19_results.csv
  - JSON:   results/part19_results.json
  - SQLite: results/part19_results.db

Study ID: study-abc123
Use 'sim-retire export study-abc123' to access stored results.
```

---

### 3.2 Command: `sim-retire list`

**Purpose:** List all stored studies and their metadata.

#### Syntax

```
sim-retire list [OPTIONS]
```

#### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--format` | Choice | `table` | Output format: `table`, `json`, `csv` |
| `--status` | Choice | `all` | Filter by status: `all`, `completed`, `failed`, `pending` |
| `--sort` | Choice | `date` | Sort by: `date`, `name`, `status` |

#### Behavior

1. Query database for all stored studies
2. Filter by status (if specified)
3. Sort results
4. Format and print

#### Example Output

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Study ID        │ Name                    │ Version │ Status    │ Units │ Date Created
────────────────┼─────────────────────────┼─────────┼───────────┼───────┼──────────────
study-abc123    │ Part 19 Glidepaths      │ 1.0     │ completed │ 1,728 │ 2026-07-20
study-def456    │ Part 40 De-risking      │ 1.0     │ completed │   864 │ 2026-07-19
study-ghi789    │ Dynamic Withdrawals     │ 1.0     │ failed    │ 2,160 │ 2026-07-18
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Total: 3 studies
```

---

### 3.3 Command: `sim-retire validate`

**Purpose:** Validate an experiment definition without executing.

#### Syntax

```
sim-retire validate STUDY_FILE
```

#### Arguments

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `STUDY_FILE` | Path | ✅ YES | Path to YAML experiment definition |

#### Behavior

1. Parse STUDY_FILE
2. Load ExperimentDefinition
3. Create ResearchPlan
4. Validate all components:
   - ✅ Cohorts valid (dates in range)
   - ✅ Parameters valid (ranges make sense)
   - ✅ Policies constructible
   - ✅ No duplicate units
5. Print validation results
6. Exit 0 if valid, 2 if invalid

#### Example Output

```
Validating: studies/part19.yaml

✅ ExperimentDefinition: valid
   Name: Part 19 Equity Glidepaths
   Version: 1.0
   Dataset: ACWI_EUR_2024

✅ Cohorts: 144 valid
   Range: 1871-01-01 to 2024-12-31
   Type: monthly_rolling
   
✅ Parameters: 12 valid
   equity_allocation: 0% to 100% (step 10%)
   glidepath_duration: 5 to 30 years (step 5)

✅ Policies: 12 distinct allocation policies
✅ Policies: 1 withdrawal policy

✅ Plan: 1,728 unique simulation units

Validation: PASSED
```

---

### 3.4 Command: `sim-retire export`

**Purpose:** Export stored study results to file.

#### Syntax

```
sim-retire export [OPTIONS] STUDY_ID
```

#### Arguments

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `STUDY_ID` | String | ✅ YES | Identifier of stored study |

#### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--format` | Choice | `csv` | Export format: `csv`, `json`, `parquet` |
| `--output` | Path | `./results/` | Output file directory or path |
| `--metrics` | Choice | `full` | What to export: `full`, `summary`, `aggregated` |

#### Behavior

1. Load results from database for STUDY_ID
2. Transform to requested format
3. Write to output file
4. Print file location and exit 0

#### Example Output

```
Exporting study-abc123...

Format: CSV
Metrics: full
Output: results/study-abc123_export.csv

Rows Written: 1,868,224 (144 cohorts × 12 parameters × 12 months × 30 years)
File Size: 245 MB
Columns: study_id, cohort_start_date, equity_allocation, month, 
         portfolio_value, withdrawal, success
```

---

### 3.5 Command: `sim-retire optimize`

**Purpose:** Run SWROptimizer to find optimal withdrawal rate.

#### Syntax

```
sim-retire optimize [OPTIONS] STUDY_FILE
```

#### Arguments

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `STUDY_FILE` | Path | ✅ YES | Base experiment definition |

#### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--target-success-rate` | Float | 0.95 | Target success rate (0.0–1.0) |
| `--initial-capital` | Decimal | 1000000 | Starting portfolio value |
| `--workers` | Integer | 1 | Parallel workers for binary search |
| `--tolerance` | Decimal | 0.001 | Withdrawal rate precision |
| `--output-dir` | Path | `./results/` | Output directory |

The study's `allocation_policy` supplies the concrete equity allocation (from
`allocation_policy.equity_allocation` or an unambiguous single-value
`parameters.equity_allocation` axis). The optimizer owns the candidate
withdrawal rates; `parameters.withdrawal_rate` is forbidden.

#### Behavior

1. Parse STUDY_FILE
2. Validate optimization parameters
3. Run SWROptimizer:
   - Binary search for withdrawal rate satisfying target success rate
   - Each iteration: execute study with new rate
4. Persist results
5. Print final optimal withdrawal rate and exit 0

#### Example Output

```
SWR Optimizer: Binary Search
Study: Part 19 Equity Glidepaths
Target Success Rate: 95%
Initial Capital: €1,000,000
Allocation Policy: 75/25 Static

Iteration 1: Testing 4.00% withdrawal rate
  Cohorts: 144 | Success Rate: 91.7% (132/144)
  → Too low, increase rate

Iteration 2: Testing 4.50% withdrawal rate
  Cohorts: 144 | Success Rate: 89.6% (129/144)
  → Too low, increase rate

Iteration 3: Testing 3.75% withdrawal rate
  Cohorts: 144 | Success Rate: 94.4% (136/144)
  → Still low, increase slightly

Iteration 4: Testing 3.95% withdrawal rate
  Cohorts: 144 | Success Rate: 95.1% (137/144)
  → Within tolerance!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Optimization Complete
Optimal Withdrawal Rate: 3.95% ± 0.001%
Success Rate Achieved: 95.1%
Iterations Required: 4
Execution Time: 45m 23s
```

---

### 3.6 Command: `sim-retire compare`

**Purpose:** Comparative analysis of two strategies.

#### Syntax

```
sim-retire compare [OPTIONS] STUDY_FILE
```

#### Arguments

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `STUDY_FILE` | Path | ✅ YES | Base experiment definition |

#### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--strategy` | String | (all) | Configuration filter as `name=value`; repeatable, AND-ed |
| `--group-by` | Choice | `global` | Grouping dimension: `global`, `cohort`, `parameter_config` |
| `--workers` | Integer | 1 | Parallel workers |
| `--initial-capital` | Decimal | 1000000 | Starting portfolio value |

#### Behavior

1. Parse STUDY_FILE
2. Build the study's generated parameter configurations (the comparison strategies)
3. Apply `--strategy name=value` filters (AND-ed); fewer than two selected
   configurations is a validation error
4. Execute the single plan once; partition results by configuration
5. Run StrategyComparator
6. Output comparison table
7. Exit 0

#### Example Output

```
Strategy Comparison
Study: Part 19 Equity Glidepaths
Strategies: 75/25 Static vs. 80/20 Dynamic Glidepath

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Metric              │ Static 75/25 │ Dynamic 80/20 │ Difference
────────────────────┼──────────────┼───────────────┼───────────
Success Rate        │     95.1%    │     96.2%     │  +1.1%
Median Final Wealth │  €2.3M       │  €2.5M        │  +8.7%
Worst-Case Outcome  │  €0.8M       │  €1.1M        │  +37.5%
Max Drawdown (P5)   │   -45.3%     │   -42.1%      │  +3.2pp
Total Return (Mean) │  €1.8M       │  €2.1M        │  +16.7%
────────────────────┼──────────────┼───────────────┼───────────

Winner: Dynamic 80/20 glidepath
Reason: Better terminal wealth, lower downside risk
```

---

## 4. Configuration File Format

### 4.1 File Location

Default: `~/.sim-retire/config.yaml`

Override with `--config FILE`

### 4.2 File Structure

```yaml
# Global settings
database:
  path: ~/.sim-retire/studies.db
  auto_backup: true

output:
  default_format: csv
  default_directory: ./results/
  
execution:
  default_workers: 4
  max_workers: 16
  timeout_seconds: 3600
  
logging:
  level: INFO  # DEBUG, INFO, WARNING, ERROR
  file: ~/.sim-retire/sim-retire.log
```

---

## 5. Error Messages

### 5.1 File Not Found Error

```
ERROR: Study file not found
File: studies/part19.yaml

Checked locations:
  - /home/user/studies/part19.yaml
  - /current/working/dir/studies/part19.yaml

Suggestion: Check file path and ensure it exists.
Exit Code: 2
```

### 5.2 Invalid YAML Error

```
ERROR: Invalid YAML in study file
File: studies/part19.yaml
Line: 42

Problem:
  Invalid indentation or syntax at:
  allocation_policy:
  - type: policy1
   equity_allocation: 0.75  ← Inconsistent indentation

Suggestion: Check YAML syntax and indentation.
Exit Code: 2
```

### 5.3 Invalid Parameter Error

```
ERROR: Invalid parameter configuration
Parameter: equity_allocation

Problem:
  Range: 0.00 to 1.00
  Provided: 1.50
  
Suggestion: Ensure allocation percentages are between 0.0 and 1.0.
Exit Code: 2
```

### 5.4 Database Error

```
ERROR: Database access failed
Database: ~/.sim-retire/studies.db

Problem: Permission denied

Suggestion:
  - Verify file permissions: chmod u+rw ~/.sim-retire/studies.db
  - Ensure ~/.sim-retire/ directory exists and is writable
  - Check available disk space
Exit Code: 4
```

### 5.5 Execution Interrupted

```
Execution interrupted by user.
Progress saved. Resume with:
  sim-retire run studies/part19.yaml --resume study-abc123
Exit Code: 130
```

---

## 6. Help Text

### 6.1 Main Help

```
$ sim-retire --help

FIRE Backtesting Framework CLI

Usage:
  sim-retire [OPTIONS] COMMAND [COMMAND_OPTIONS]

Commands:
  run          Execute a research study
  list         List stored studies
  validate     Validate experiment definition
  export       Export results to file
  optimize     Find optimal withdrawal rate
  compare      Compare two strategies
  
Global Options:
  --version    Show version and exit
  --help       Show this help and exit
  --verbose    Enable verbose output
  --debug      Enable debug logging
  --config     Path to config file

Examples:
  sim-retire run studies/part19.yaml --workers 4
  sim-retire list --status completed
  sim-retire validate studies/part19.yaml
  sim-retire export study-abc123 --format csv
  sim-retire optimize studies/part19.yaml --target-success-rate 0.95

For more help on a command:
  sim-retire COMMAND --help
```

### 6.2 Command-Specific Help

```
$ sim-retire run --help

Execute a research study

Usage:
  sim-retire run [OPTIONS] STUDY_FILE

Arguments:
  STUDY_FILE              Path to YAML experiment definition

Options:
  --output-dir DIR        Directory for results (default: ./results/)
  --workers N             Parallel workers, 1 to CPU count (default: 1)
  --format TYPE           Output format: csv, json, sqlite, all (default: csv)
  --persist-study         Save study to database (default: true)
  --dry-run               Validate plan without executing
  --resume STUDY_ID       Resume interrupted execution
  --timeout SECONDS       Max execution time (default: 3600)
  --help                  Show this help

Examples:
  sim-retire run studies/part19.yaml
  sim-retire run studies/part19.yaml --workers 8 --format sqlite
  sim-retire run studies/part19.yaml --dry-run
  sim-retire run studies/part19.yaml --timeout 7200
```

---

## 7. Input Formats

### 7.1 Experiment Definition (YAML)

```yaml
# studies/part19.yaml
metadata:
  name: "SWR Part 19: Equity Glidepaths"
  version: "1.0"
  description: "Equity glidepath strategies with monthly rebalancing"

dataset:
  identifier: "ACWI_EUR_2024"

cohorts:
  type: "monthly_rolling"
  window_years: 30

allocation_policy:
  type: "ConstantAllocationPolicy"
  equity_allocation: 0.75

withdrawal_policy:
  type: "ConstantWithdrawalPolicy"
  withdrawal_rate: 0.04

parameters:
  equity_allocation: [0.50, 0.75, 0.90]
```

---

## 8. Output Formats

### 8.1 CSV Output

```csv
cohort_start_date,equity_allocation,month_index,portfolio_value,withdrawal,success
2020-01-01,0.75,0,1000000.00,3333.33,1
2020-01-01,0.75,1,1010245.67,3338.41,1
...
```

### 8.2 JSON Output

```json
{
  "study_id": "study-abc123",
  "created_at": "2026-07-25T14:30:00Z",
  "cohorts": 144,
  "success_rate": 0.951,
  "results": [
    {
      "cohort_start_date": "2020-01-01",
      "equity_allocation": 0.75,
      "trajectory": [
        {"month": 0, "portfolio_value": "1000000.00", "withdrawal": "3333.33"},
        {"month": 1, "portfolio_value": "1010245.67", "withdrawal": "3338.41"}
      ]
    }
  ]
}
```

---

## 9. Acceptance Criteria

CLI is complete when:

- [ ] All 6 commands implemented
- [ ] All options and arguments validated
- [ ] Exit codes consistent and correct
- [ ] Help text comprehensive and accurate
- [ ] Error messages clear and actionable
- [ ] Input validation comprehensive
- [ ] Output formatting correct for all formats
- [ ] Configuration file loading working
- [ ] 100% of CLI tests passing
- [ ] 0 mypy errors

---

**Specification Status:** APPROVED & FROZEN  
**Implementation Ready:** YES  
**Next Gate:** CLI command implementation
