# Contributing Guide

## Overview

This project follows a Specification-Driven Development process.

Implementation is guided by two documents:

- PROJECT_PLAN.md
- IMPLEMENTATION_PROMPT.md

The implementation must follow these documents exactly.

---

# Development Principles

The priorities of this project are:

1. Correctness
2. Determinism
3. Reproducibility
4. Maintainability
5. Extensibility
6. Performance

Performance is never more important than correctness.

---

# Branch Strategy

Feature branches are recommended.

Examples:

feature/domain-money

feature/simulation-runner

feature/binary-search

bugfix/rebalance-rounding

refactor/pipeline

---

# Commit Messages

Commits should be small and atomic.

Examples:

Implement Money value object

Add Allocation validation

Implement Binary Search optimizer

Refactor SimulationPipeline

Add regression test for glidepath

Avoid commits such as:

misc changes

updates

work in progress

fixes

---

# Formatting

The project should use automatic formatting.

Recommended:

black

isort

ruff

Formatting changes should be isolated from functional changes whenever possible.

---

# Static Analysis

Recommended tools:

ruff

mypy

Warnings should be fixed rather than ignored.

---

# Testing

Every new feature must include tests.

Priority:

1. Unit tests
2. Integration tests
3. Regression tests

A feature without tests is not complete.

---

# Pull Requests

Every Pull Request should contain:

- Summary
- Affected PROJECT_PLAN sections
- Tests added
- Breaking changes (if any)

---

# Code Review

Every review should verify:

- PROJECT_PLAN compliance
- IMPLEMENTATION_PROMPT compliance
- Correctness
- Tests
- Architecture
- Readability

---

# Performance

Never optimize before profiling.

Document every optimization.

Benchmark after major optimizations.

---

# Dependencies

New dependencies require justification.

Prefer the Python standard library whenever practical.

---

# Documentation

Whenever public behaviour changes:

Update:

- PROJECT_PLAN.md (if specification changes)
- IMPLEMENTATION_PROMPT.md (if implementation rules change)
- README.md (if user-visible behaviour changes)

---

# Specification

PROJECT_PLAN.md is the source of truth.

If code and specification disagree:

The code is wrong.

---

# Questions

If implementation requires a design decision:

STOP.

Do not guess.

Consult the Architect through the Product Owner.

Never invent behaviour.