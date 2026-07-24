# Guide for Human Contributors

**Purpose:** This document defines the collaboration workflow for human stakeholders interacting with the AI Architect.

---

## 1. Initializing an AI Architect
When starting a session with a new AI Architect, follow this procedure:

1. **Check Repository Access:**
   - **If the AI has repository access:** You do not need to provide any files. Simply ask the AI to: *"Bootstrap your context by discovering the `DOCUMENTATION_TREE.md` and following the recovery workflow in `AI_ARCHITECT_GUIDE.md`."*
   - **If the AI lacks repository access:** You must provide the following baseline documents to establish context:
     - `docs/continuity/PROJECT_CONTEXT.md`
     - `docs/continuity/OPERATIONAL_DASHBOARD.md`
     - `docs/continuity/NEXT_SESSION.md`
     - `docs/continuity/AI_ARCHITECT_GUIDE.md`

---

## 2. Collaboration Workflow
- **Roles:**
  - **AI Architect:** Responsible for architectural integrity, specification definition, and design rationales.
  - **Human Stakeholder:** Provides strategic direction, approves architectural plans, and monitors progress.
  - **Implementation Engineer:** Executes specifications provided by the Architect. (Often this is the same AI, but in a different operational mode).

- **The Responsibility Cycle:**
  1. **Initialization:** Human sets context or directs AI to discover it.
  2. **Specification:** Architect produces specifications or designs.
  3. **Implementation:** Implementation agent executes code.
  4. **Validation:** Implementation agent provides review against specification.
  5. **Approval:** Architect confirms compliance; human stakeholder signs off on milestone completion.

---

## 3. Session Recovery
If an AI session loses context, simply repeat the initialization procedure in Section 1. The documentation system is designed to allow the Architect to recover the full architectural state autonomously.

---

## 4. Governance
- All architectural decisions must be persisted in canonical documentation. If you and the AI agree on a new rule or constraint during a conversation, direct the AI to update the relevant document (e.g., `GOVERNANCE.md` or a specification) immediately.
- This documentation is the source of truth, not your conversation history.
