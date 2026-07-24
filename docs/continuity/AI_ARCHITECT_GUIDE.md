# AI Architect Guide

**Document Type:** AI Onboarding & Reference Guide
**Status:** Active
**Last Updated:** 2026-07-24
**Audience:** AI Developers (ChatGPT and similar)

---

## 1. Purpose

This document is the **canonical guide for AI agents** operating in this project. It defines roles, authority levels, recovery workflows, and documentation responsibilities.

This document must be attached at the beginning of every AI conversation to establish the operating contract.

---

## 2. AI Roles

### Architect (ChatGPT / LLM)
**Responsibilities:**
- Propose architectural designs and design trade-offs.
- Write behavioral specifications and acceptance criteria.
- Perform architecture reviews.
- Approve/Freeze specifications.
- Make final calls on ambiguities.

### Implementer (The Active Agent)
**Responsibilities:**
- Implement specifications exactly as defined.
- Write tests to ensure specification compliance.
- Refactor for clarity and performance (never behavior).
- Raise questions immediately if specifications are unclear.

---

## 3. Decision Authority

### Architect Authority
- **Design proposals** — How components should work.
- **Specification content** — The contract the implementation must follow.
- **Public API contracts** — How subsystems interact.
- **Roadmap priorities** — What gets built and when.

### Implementer Authority
- **Code implementation** — How to fulfill the contract in code.
- **Test strategy** — How to prove the implementation is correct.
- **Internal organization** — Naming and structure within the scope.

---

## 4. Working Workflow & Context Recovery

**When starting a new session, follow this reading order for context recovery:**

1. ✅ **[PROJECT_CONTEXT.md](PROJECT_CONTEXT.md)** (5 min): Mission, vision, and quality principles.
2. ✅ **[OPERATIONAL_DASHBOARD.md](OPERATIONAL_DASHBOARD.md)** (10 min): High-level progress, test status, and quality gates.
3. ✅ **[CURRENT_STATE.md](CURRENT_STATE.md)** (15 min): Detailed technical state of what has been implemented and frozen.
4. ✅ **[NEXT_SESSION.md](NEXT_SESSION.md)** (5 min): The specific operational task for the current session.

---

## 5. Documentation Responsibilities

- **Source of Truth Priority:** Every project question has *one* canonical source. Find it in `SOURCE_OF_TRUTH.md`.
- **Reference Over Duplicate:** Do not copy knowledge across files. Link to the canonical source instead.
- **Consistency First:** If code and documentation disagree, the documentation (Specification) is usually the law. Correct the code to match the spec, or propose a spec update via the Architect.
- **No Residual Knowledge:** Ensure that any temporary insights gained during implementation are migrated to permanent documentation.

   - Exact task to begin with

4. 📖 **README.md** (development setup)

5. 📖 **docs/README.md** (documentation navigation)

### 2. Understanding Frozen vs. Active Documentation

**Frozen Documentation (Immutable Without Architect Approval)**

**Never modify these without explicit architectural approval:**

- **Specifications** (`docs/specifications/*/`)
  - Engine specifications define the monthly simulation execution contract
  - Research specifications define study composition and orchestration
  - Optimization specifications define algorithm behavior
  - Status: Once marked "Approved & Frozen," these are the law

- **Architecture Reviews** (`docs/architecture/reviews/`)
  - Document design decisions that were already made
  - Frozen as records of architectural decisions
  - Reopen only if a decision needs to be reversed

- **Roadmaps** (`docs/roadmaps/milestones/`)
  - RESEARCH_LAYER_FINAL_ROADMAP.md is the authoritative blueprint
  - Defines v0.2, v0.3, v0.4 structure
  - Do not change without architect approval

**Active Documentation (Updatable)**

**Update these as work progresses:**

- **OPERATIONAL_DASHBOARD.md** — Update after each milestone
- **NEXT_SESSION.md** — Update at session boundaries
- **Implementation Reports** (`docs/reports/`) — Add new reports as work completes

### 3. Implementation Process

1. **Read the specification** — Every implementation must match its frozen specification exactly
2. **Check architecture review** — Understand design rationale
3. **Review public API** — Know interface contracts
4. **Implement against spec** — Code implements, specs don't describe code
5. **Write tests** — Tests validate spec compliance
6. **Add implementation report** — Document what was implemented

### 4. Quality Gates

**Before starting work:**

- [ ] Read `docs/continuity/AI_SESSION_BOOTSTRAP.md`
- [ ] Read `docs/continuity/PROJECT_CONTEXT.md`
- [ ] Read `docs/continuity/OPERATIONAL_DASHBOARD.md`
- [ ] Read `docs/continuity/NEXT_SESSION.md`
- [ ] Run tests: `pytest tests/ -v`
- [ ] Find your task in `docs/continuity/OPERATIONAL_DASHBOARD.md`
- [ ] Read corresponding specification
- [ ] Start implementation

**Code Quality Standards (No Exceptions):**

Every implementation must:

- ✅ Pass 100% of tests
- ✅ Achieve 0 mypy errors
- ✅ Match specification exactly
- ✅ Use Decimal (never float) for financial values
- ✅ Maintain immutability for domain objects
- ✅ Have comprehensive docstrings
- ✅ Follow Clean Architecture layer boundaries
- ✅ Include architecture review comment linking to spec

## Frozen Documentation Policy

### The Specification Is the Contract

All implementations must comply with their frozen specification:

- **SIMULATION_RUNNER_SPECIFICATION.md** → [../../src/engine/application/runner.py](../../src/engine/application/runner.py)
- **RESEARCH_EXECUTOR_SPECIFICATION.md** → [../../src/research/orchestration/executor.py](../../src/research/orchestration/executor.py)
- Every pipeline step has its frozen specification

### What "Frozen" Means

Once a specification is marked "APPROVED & FROZEN":

- ✅ **Can** refactor code that implements it (internal only)
- ✅ **Can** add tests that validate it
- ✅ **Can** optimize performance (if correctness unchanged)
- ❌ **Cannot** change behavior
- ❌ **Cannot** add/remove responsibilities
- ❌ **Cannot** modify public API
- ❌ **Cannot** rewrite specification without approval

### Where to Find Status

Look at the top of each specification document:

```markdown
# Status: APPROVED & FROZEN
```

If it says "Approved & Frozen," treat it as law.

## Context Recovery

### When Context Is Lost

**If you lose context or start fresh:**

1. **Read this document first** — `docs/continuity/AI_SESSION_BOOTSTRAP.md`
2. **Then read PROJECT_CONTEXT.md** — Understand project purpose
3. **Then read OPERATIONAL_DASHBOARD.md** — Understand current status
4. **Then read NEXT_SESSION.md** — Understand immediate task
5. **Then read docs/README.md** — Understand documentation structure

### If Context Is Incomplete

**When you have incomplete context:**

1. **Stop work immediately** — Don't guess or assume
2. **Document the ambiguity** — Note what's unclear
3. **Ask the Product Owner** — Consult the Chief Architect
4. **Wait for clarification** — Don't proceed until clear

### Determining the Active Milestone

**To understand what's currently being worked on:**

1. **Read OPERATIONAL_DASHBOARD.md** — Shows current milestone
2. **Check specifications** — Look for "APPROVED & FROZEN" status
3. **Identify next task** — From CURRENT_IMPLEMENTATION_TASK section
4. **Find corresponding spec** — In docs/specifications/

### Identifying the Next Implementation Task

**To find what to implement next:**

1. **Read OPERATIONAL_DASHBOARD.md** — Section "Current Implementation Task"
2. **Find the component** — SWROptimizer, StrategyComparator, etc.
3. **Read the specification** — docs/specifications/optimization/
4. **Start implementation** — Against the specification

## Required Documents to Keep Updated

### Documents You Must Update

**OPERATIONAL_DASHBOARD.md**
- Update after each milestone completion
- When blockers are identified/resolved
- When priorities shift
- At session boundaries (major state changes)

**NEXT_SESSION.md**
- Update at session boundaries
- When test status changes
- When implementation tasks change

**Implementation Reports**
- Add new reports as work completes
- Update existing reports with progress

### Documents You Must NOT Update

**PROJECT_CONTEXT.md**
- Only update mission, vision, philosophy
- Never update current implementation status
- Never update milestone completion
- Never update next tasks

**AI_HANDOVER.md**
- Only update onboarding methodology
- Never update architectural content
- Never update technical specifications

**ARCHITECTURE_OVERVIEW.md**
- Only update high-level system overview
- Never update detailed specifications
- Never update implementation details

## Milestone Completion Workflow

### After Completing a Milestone

1. **Update OPERATIONAL_DASHBOARD.md**
   - Mark milestone as completed
   - Identify next milestone
   - Update next implementation task
   - Note any blockers or issues

2. **Update NEXT_SESSION.md**
   - Document session completion
   - Note test results
   - Identify next session task

3. **Add Implementation Report**
   - Create new report in docs/reports/
   - Document what was implemented
   - Summarize results and quality

4. **Update Governance if Needed**
   - If governance rules need adjustment
   - Update docs/continuity/GOVERNANCE.md

### Before Starting New Work

1. **Read OPERATIONAL_DASHBOARD.md**
   - Understand current status
   - Identify next task
   - Check for blockers

2. **Read corresponding specification**
   - Understand exact requirements
   - Identify test expectations
   - Plan implementation approach

3. **Run tests**
   - Verify baseline
   - Ensure all tests pass
   - Check for mypy errors

## Commit Discipline

### What to Commit

**Always commit:**
- All implementation files
- All test files
- All documentation updates
- All configuration changes

**Never commit:**
- Temporary files
- Debug output
- Build artifacts
- Environment-specific files

### Commit Message Format

```
<type>(<scope>): <description>

- Implement <component> according to <specification>
- Add tests for <component> specification compliance
- Update <document> with <change>

Co-authored-by: Chief Architect <architect@project.com>
```

### When to Ask Questions

**Ask questions when:**

1. **Specification is unclear** — Don't guess, ask for clarification
2. **Ambiguous requirements** — Document the ambiguity, ask for guidance
3. **Design decisions** — Consult architecture review, ask for rationale
4. **Scope changes** — Ask for architect approval before proceeding
5. **Quality standards** — Consult PROJECT_CONTEXT.md, ask for clarification

**Never guess** — Always ask when uncertain.

## Final Notes

### This Document Is Your Compass

- Future work starts here
- Return to this document when confused
- Update it if you discover missing information
- Preserve its structure; don't rewrite it

### Remember the Rules

1. **Always read OPERATIONAL_DASHBOARD.md first** — Understand current status
2. **Always read PROJECT_CONTEXT.md second** — Understand project purpose
3. **Always read NEXT_SESSION.md third** — Understand immediate task
4. **Never guess** — Always ask when unclear
5. **Always follow specifications** — They are the contract
6. **Always write tests** — They validate the specification
7. **Always update documentation** — Keep everyone informed

### Next Steps

1. ✅ You've read this (AI_SESSION_BOOTSTRAP.md)
2. ⬜ Read [PROJECT_CONTEXT.md](PROJECT_CONTEXT.md)
3. ⬜ Read [OPERATIONAL_DASHBOARD.md](OPERATIONAL_DASHBOARD.md)
4. ⬜ Read [NEXT_SESSION.md](NEXT_SESSION.md)
5. ⬜ Run tests: `pytest tests/ -v`
6. ⬜ Find your task in [OPERATIONAL_DASHBOARD.md](OPERATIONAL_DASHBOARD.md)
7. ⬜ Read corresponding specification
8. ⬜ Start implementation

---

**Document Status:** Complete & Accurate  
**Last Updated:** 2026-07-23  
**Maintainer:** Chief Architect