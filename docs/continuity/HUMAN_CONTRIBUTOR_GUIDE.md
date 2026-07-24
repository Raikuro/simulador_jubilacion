# Guide for Human Contributors

**Purpose:** This document defines the collaboration workflow for human stakeholders interacting with the AI Architect.

---

## 1. Initializing an AI Architect
When starting a session with a new AI, you must define its operational mode:

1. **Check Repository Access:**
   - **If the AI has repository access:** Ask it to: *"Bootstrap your context by discovering the `DOCUMENTATION_TREE.md` at the project root and following the recovery workflow in `AI_ARCHITECT_GUIDE.md`."*
   - **If the AI lacks repository access:** Provide these baseline documents: `PROJECT_CONTEXT.md`, `OPERATIONAL_DASHBOARD.md`, `NEXT_SESSION.md`, `AI_ARCHITECT_GUIDE.md`.

2. **Define Session Type:**
   - **Architectural Session:** Direct the AI to focus on `docs/architecture/` and `docs/specifications/`.
   - **Implementation Session:** Direct the AI to follow `NEXT_SESSION.md`, implement against specific `docs/specifications/`, and finalize with an *Implementation Review*.

---

## 2. Collaboration Workflow & Roles
- **Roles:**
  - **AI Architect:** Responsible for architectural integrity, specification definition, and design rationales.
  - **Human Stakeholder:** Provides strategic direction, approves plans, and supervises milestone completion.
  - **Implementation Engineer:** Executes specifications exactly.
- **The Responsibility Cycle:**
  1. Initialization (Set context) → 2. Specification (Architect defines) → 3. Implementation (Engineer executes) → 4. Validation (Tests) → 5. Approval (Architect confirms).

---

## 3. Context & Information Discovery
- **Where to start:** Always use `docs/DOCUMENTATION_TREE.md` as the master navigation index for all project documentation.
- **Where to find information:** If you do not know where a specific project answer lives, consult `docs/continuity/SOURCE_OF_TRUTH.md`. It maps every common question to its canonical document.

---

## 4. Operational Governance
- **Session Recovery:** If context is lost, repeat the Section 1 initialization.
- **Commit/Milestone Boundaries:** All work must be completed in atomic, verified commits. Architectural decisions and milestone completions must be persisted in canonical documentation before the task is considered finished.
- **Truth Source:** This documentation is the source of truth—not your conversation history. If you agree on a change during a session, ensure the AI updates the canonical documentation immediately.
