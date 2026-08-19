# P1.6 — Packaging and Dependency Design

**Document Type:** Architectural Design & Packaging Specification  
**Status:** REVISED SPECIFICATION (2026-08-19)  
**Date:** 2026-08-19  
**Workstream:** Repository Separation & Documentation Audit  
**Task:** Phase 1 / P1.6 (Packaging and Dependency Design)  
**Prerequisites:** P1.1 (Repository Baseline) COMPLETE, P1.2 (Core Public API) APPROVED, P1.3 (Core Boundary) APPROVED, P1.4 (CLI Boundary) APPROVED, P1.5 (Dependency Audit) APPROVED  
**Successor:** P1.7 (Test Separation Design)  

---

## 1. Executive Summary

This document establishes the packaging topology, dependency matrix, build configurations, and cross-package versioning policy for separating the framework into two standalone distributions:
- **`fbf-core`**: A pure, zero-dependency foundational simulation and research engine.
- **`fbf-cli`**: The command-line frontend and terminal presentation layer that consumes `fbf-core` within a defined semantic version compatibility range.

### Key Architectural Results
1. **Zero Third-Party Runtime Dependencies for Core:**  
   Empirical audit confirms that `fbf-core` requires **zero external runtime dependencies** (`dependencies = []`). It runs entirely on the Python 3.13 Standard Library (`decimal`, `sqlite3`, `dataclasses`, `concurrent.futures`, `abc`, `typing`, `math`, `datetime`, `pathlib`).
2. **Explicit Dependency Placement:**  
   `pyyaml>=6.0` is owned exclusively by `fbf-cli` for reading YAML files from disk.
3. **Explicit Cross-Package Compatibility Range:**  
   `fbf-cli` declares `fbf-core>=0.1.0,<0.2.0` (pinned to the compatible minor series during pre-1.0 development), preventing cross-package version drift.
4. **Standard PEP 420 Implicit Namespace Packaging:**  
   `fbf` is a pure PEP 420 implicit namespace package (contains no `src/fbf/__init__.py`). `fbf.core` and `fbf.cli` are standard subpackages containing concrete `__init__.py` files and PEP 561 `py.typed` markers.
5. **Authoritative Executable Naming:**  
   `fbf` is the single primary command-line executable (`[project.scripts] fbf = "fbf.cli.main:main"`).

---

## 2. Target Repository & Package Topology

```
fbf/                                    # Umbrella Workspace / Development Directory
├── core/                               # Standalone Git Repository: fbf-core
│   ├── .git/
│   ├── pyproject.toml                  # Distribution: fbf-core (0 runtime dependencies)
│   ├── README.md
│   ├── AGENTS.md
│   ├── src/
│   │   └── fbf/                        # Implicit PEP 420 namespace (NO __init__.py here)
│   │       └── core/                   # Concrete subpackage (HAS __init__.py)
│   │           ├── __init__.py         # Primary Application API Facade
│   │           ├── py.typed            # PEP 561 typing marker
│   │           ├── errors.py
│   │           ├── domain/
│   │           ├── study/
│   │           ├── execution/
│   │           ├── optimization/
│   │           └── persistence/
│   └── tests/                          # Core test suite (~700 tests)
│
└── cli/                                # Standalone Git Repository: fbf-cli
    ├── .git/
    ├── pyproject.toml                  # Distribution: fbf-cli (depends on fbf-core & pyyaml)
    ├── README.md
    ├── AGENTS.md
    ├── src/
    │   └── fbf/                        # Implicit PEP 420 namespace (NO __init__.py here)
    │       └── cli/                    # Concrete subpackage (HAS __init__.py)
    │           ├── __init__.py
    │           ├── py.typed            # PEP 561 typing marker
    │           ├── main.py             # CLI main entry point
    │           ├── error_handling.py
    │           ├── loaders/
    │           ├── presentation/
    │           └── commands/
    └── tests/                          # CLI & E2E test suite (~275 tests)
```

---

## 3. Dependency Ownership & Classification Matrix

### 3.1 Runtime vs. Development Classification

| Dependency | Category | Declaring Package | Purpose & Version Constraint |
| :--- | :---: | :---: | :--- |
| **`python`** | Runtime | `fbf-core` & `fbf-cli` | `>=3.13` (Modern Python 3.13 syntax, performance, typing) |
| **`fbf-core`** | Runtime | `fbf-cli` only | `>=0.1.0,<0.2.0` (Core application engine API contract) |
| **`pyyaml`** | Runtime | `fbf-cli` only | `>=6.0` (Filesystem YAML parsing in CLI loaders) |
| **`pytest`** | Dev / Test | Both | `>=8.0` (Test execution framework) |
| **`pytest-cov`**| Dev / Test | Both | Coverage reporting |
| **`ruff`** | Tooling / Dev| Both | Linting and import sorting |
| **`black`** | Tooling / Dev| Both | Canonical code formatting (line-length 100) |
| **`mypy`** | Tooling / Dev| Both | Strict static type checking (`strict = true`) |

*Standard Library Runtime Footprint (Zero External Bloat):*
- **`fbf-core`:** `decimal`, `sqlite3`, `dataclasses`, `concurrent.futures`, `abc`, `typing`, `math`, `datetime`, `pathlib`, `itertools`, `enum`, `copy`.
- **`fbf-cli`:** `argparse`, `sys`, `pathlib`, `json`, `csv`, `time`, `shutil`.

---

## 4. `pyproject.toml` Specifications

### 4.1 `fbf-core` (`core/pyproject.toml`)

```toml
[build-system]
requires = ["setuptools>=80", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "fbf-core"
version = "0.1.0"
description = "High-performance, deterministic FIRE simulation and safe withdrawal rate research engine."
readme = "README.md"
requires-python = ">=3.13"
license = { text = "MIT" }
authors = [
    { name = "Julio Gracia" }
]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Financial and Insurance Industry",
    "Programming Language :: Python :: 3.13",
    "Typing :: Typed",
]

# Zero third-party runtime dependencies
dependencies = []

[project.optional-dependencies]
dev = [
    "pytest>=8",
    "pytest-cov",
    "ruff",
    "black",
    "mypy",
]

[tool.black]
line-length = 100
target-version = ["py313"]

[tool.ruff]
line-length = 100
target-version = "py313"
exclude = [".venv", "build", "dist"]

[tool.ruff.lint]
select = ["E", "F", "W", "I", "UP", "B", "SIM", "C4"]

[tool.ruff.lint.isort]
combine-as-imports = true

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_functions = ["test_*"]
addopts = ["-ra", "--strict-markers"]

[tool.coverage.run]
branch = true
source = ["src/fbf/core"]

[tool.coverage.report]
show_missing = true
skip_covered = false

[tool.mypy]
python_version = "3.13"
strict = true
warn_return_any = true
warn_unused_configs = true
warn_unused_ignores = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
no_implicit_optional = true
pretty = true

[tool.setuptools]
package-dir = {"" = "src"}

[tool.setuptools.packages.find]
where = ["src"]
namespaces = true

[tool.setuptools.package-data]
"fbf.core" = ["py.typed"]
```

---

### 4.2 `fbf-cli` (`cli/pyproject.toml`)

```toml
[build-system]
requires = ["setuptools>=80", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "fbf-cli"
version = "0.1.0"
description = "Command-line interface and presentation frontend for the FIRE Backtesting Framework (FBF)."
readme = "README.md"
requires-python = ">=3.13"
license = { text = "MIT" }
authors = [
    { name = "Julio Gracia" }
]
classifiers = [
    "Development Status :: 4 - Beta",
    "Environment :: Console",
    "Programming Language :: Python :: 3.13",
    "Typing :: Typed",
]

dependencies = [
    "fbf-core>=0.1.0,<0.2.0",
    "pyyaml>=6.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8",
    "pytest-cov",
    "ruff",
    "black",
    "mypy",
]

[project.scripts]
fbf = "fbf.cli.main:main"

[tool.black]
line-length = 100
target-version = ["py313"]

[tool.ruff]
line-length = 100
target-version = "py313"
exclude = [".venv", "build", "dist"]

[tool.ruff.lint]
select = ["E", "F", "W", "I", "UP", "B", "SIM", "C4"]

[tool.ruff.lint.isort]
combine-as-imports = true

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_functions = ["test_*"]
addopts = ["-ra", "--strict-markers"]

[tool.coverage.run]
branch = true
source = ["src/fbf/cli"]

[tool.coverage.report]
show_missing = true
skip_covered = false

[tool.mypy]
python_version = "3.13"
strict = true
warn_return_any = true
warn_unused_configs = true
warn_unused_ignores = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
no_implicit_optional = true
pretty = true

[tool.setuptools]
package-dir = {"" = "src"}

[tool.setuptools.packages.find]
where = ["src"]
namespaces = true

[tool.setuptools.package-data]
"fbf.cli" = ["py.typed"]
```

---

## 5. PEP 420 Namespace Package Arrangement

To ensure clean co-existence and avoid namespace conflicts:
1. **Implicit Namespace:** The top directory `src/fbf/` contains **no** `__init__.py` file in either repository.
2. **Explicit Concrete Packages:**
   - In `fbf-core`: `src/fbf/core/__init__.py` defines the Core package.
   - In `fbf-cli`: `src/fbf/cli/__init__.py` defines the CLI package.
3. **Packaging Configuration:** Both `pyproject.toml` files specify `namespaces = true` under `[tool.setuptools.packages.find]`.
4. **Verification Guarantee:** When both packages are installed in the same Python environment:
   ```python
   import fbf.core  # Resolves from core distribution
   import fbf.cli   # Resolves from cli distribution
   ```

---

## 6. Versioning & Cross-Package Compatibility Policy

1. **Semantic Versioning Conventions:** Both packages adhere to Semantic Versioning conventions (`MAJOR.MINOR.PATCH`) with an explicit project-defined pre-1.0 compatibility rule:
   - During `0.x` development:
     - Breaking Public API changes in `fbf-core` increment the **minor** version (e.g. `0.1.0` $\to$ `0.2.0`).
     - Backward-compatible features and fixes in `fbf-core` increment the **patch** version (e.g. `0.1.0` $\to$ `0.1.1`).
     - `fbf-cli` pins its dependency to the compatible minor range: `fbf-core>=0.1.0,<0.2.0`.
2. **Post-1.0 Compatibility Rule:**  
   Following `1.0.0`:
   - `fbf-cli` pins `fbf-core>=1.0.0,<2.0.0`. Breaking Core changes increment `MAJOR`.
3. **Independent Release Control:**  
   `fbf-cli` can release new patches or features (e.g. `fbf-cli 0.1.5`) without requiring a new release of `fbf-core`, as long as the underlying Core Public API contract remains satisfied.

---

## 7. Local Development & Workflow Topology

To allow seamless local development across both packages without publishing wheels:

```bash
# 1. Create a unified virtual environment
python3.13 -m venv .venv
source .venv/bin/activate

# 2. Install fbf-core in editable mode
pip install -e ./core[dev]

# 3. Install fbf-cli in editable mode
pip install -e ./cli[dev]
```

### Verification Commands
- **Core verification:** `(cd core && pytest tests/ && mypy src tests && ruff check .)`
- **CLI verification:** `(cd cli && pytest tests/ && mypy src tests && ruff check .)`

---

## 8. Package Boundary Verification & Acceptance Criteria

P1.6 establishes explicit package installation and boundary verification requirements for the post-extraction gate:

1. **Core Isolation Test:**  
   - In a fresh virtualenv, install `fbf-core` only (`pip install ./core`).
   - Verify `python -c "import fbf.core"` succeeds.
   - Verify `python -c "import fbf.cli"` fails with `ModuleNotFoundError`.
   - Verify `pip list` shows 0 external runtime dependencies.
2. **CLI Integration Test:**  
   - In a fresh virtualenv, install `fbf-cli` (`pip install ./cli`).
   - Verify `pip list` installs both `fbf-core` and `pyyaml`.
   - Verify `fbf --help` executes and returns exit code 0.
3. **Type Checking Test:**  
   - Run `mypy --strict` on an external script importing `from fbf.core import StudyConfiguration` and verify type definitions are resolved via `py.typed`.
4. **Zero Repository-Relative Imports:**  
   - Tests in `cli/tests/` import `from fbf.core import ...` as an installed package, with zero `sys.path.append("..")` hacks.

---

## 9. Implementation Sequencing (Handoff to P1.7–P1.10)

- **P1.7 (Test Separation Design):** Design the physical allocation of test files between `core/tests/` and `cli/tests/`.
- **P1.8 (Git Migration Strategy):** Design the Git history extraction script using `git-filter-repo`.
- **P1.9 (Core Extraction Implementation):** Physically extract `fbf-core` and verify package isolation.
- **P1.10 (CLI Extraction Implementation):** Physically extract `fbf-cli` and verify CLI installation against `fbf-core`.

---

## 10. Architectural Decision

**APPROVE DESIGN**

The revised Packaging and Dependency Design is fully verified, zero-dependency for Core, PEP 420/561 compliant, and ready for test separation design in P1.7.
