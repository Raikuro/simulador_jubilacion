# Documentation Governance

**Document Type:** Governance  
**Status:** Active  
**Last Updated:** 2026-07-23

---

## 1. Core Principle

> **Every important project question must have exactly one canonical source of truth.**
> 
> Other documents may summarize or reference it, but must not redefine it.

This principle ensures documentation is authoritative, predictable, and maintainable for many years.

---

## 2. Documentation Governance Rules (Permanent)

### AI Platform Independence
Documentation must never depend on the capabilities of a particular AI platform. Every workflow must be expressed in terms of responsibilities rather than implementation details.

GOOD:
- Discover documentation.
- Recover architectural context.
- Verify canonical sources.

BAD:
- Upload this document.
- Paste this prompt.
- Start a specific AI conversation.

### Explicit Document Metadata
Every permanent documentation file must explicitly define:
- Purpose
- Owner
- Canonical Responsibility
- Update Policy
- Status (Frozen / Mutable)

### Documentation Growth Rule
The documentation system is considered architecturally mature. New permanent documents must not be created merely to simplify a conversation or implementation session. A new permanent document may only be introduced if it owns a genuinely new responsibility that cannot be assigned to an existing document without violating the "one responsibility per document" principle.

**Documentation does not grow by its own initiative. It evolves only when a real architectural need demonstrates that something is missing.**

Default decision process for new requirements:
1. Reuse an existing document.
2. Extend an existing document if it remains within its responsibility.
3. Create a new document only if neither of the previous options is architecturally correct.

### Persistence of Decisions
Architectural decisions are not considered complete until they are persisted in the project's canonical documentation. Assistant responses, conversations and temporary reasoning are never considered the source of truth. Whenever an architectural decision introduces future work, a roadmap item, a governance rule, a design constraint, or a project policy, the Architect must update the corresponding canonical document before considering the task complete.

---

## 3. Documentation Convergence Rules

- **One Responsibility per Document:** Each document must answer a unique, well-defined question.
- **Merge on Overlap:** If two documents cover the same responsibility, they must be merged into the canonical one.
- **Reference, Don't Duplicate:** Information must live in one place; other documents should link to it.
- **Periodic Pruning:** Documentation must be reviewed at milestone boundaries to consolidate or remove redundant files.

## 4. Temporary Document Rules

- **Explicit Labeling:** Documents intended for temporary use must be marked as `Status: Temporary`.
- **Session-Scoped:** Designed to exist only during a specific task, session, or brainstorming phase.
- **Migration Policy:** Valuable insights must be moved to permanent documentation before the task is considered finished.
- **Auto-Deletion:** If content is not migrated to a permanent home, the temporary file must be deleted once its task is complete.

---

## 5. Document Responsibilities

- Reading order
- Working methodology
- Meaning of Frozen specifications
- Decision workflow
- **Must not** become another architecture document

### PROJECT_CONTEXT.md
**Purpose:**
- Mission
- Vision
- Design philosophy
- Architectural principles
- Quality goals
- Non-goals
- **Should be mostly timeless**
- **Must not** describe current implementation status

### CURRENT_STATE.md
**Purpose:**
- Operational status only
- Current version
- Completed milestones
- Active milestone
- Immediate next task
- Blockers
- Current priorities
- **Nothing else**
- **Expected to change frequently**

### ARCHITECTURE_OVERVIEW.md
**Purpose:**
- High-level architectural map only
- Explain major subsystems
- Explain relationships
- Explain responsibilities
- Where detailed specifications are located
- **Must not** duplicate specifications
- **Role is orientation, not specification**

### SOURCE_OF_TRUTH.md
**Purpose:**
- Reference guide for canonical sources
- Answers "where can I find information about X?" questions
- Never contains the information itself
- Always references the canonical document

### GOVERNANCE.md
**Purpose:**
- Documents the documentation governance rules
- Defines document responsibilities
- Establishes canonical source relationships
- Guides future documentation decisions

### Specifications (docs/specifications/*)
**Purpose:**
- Implementation contracts
- Behavioral definitions
- Acceptance criteria
- Test requirements
- **Frozen once approved**

### Architecture Reviews (docs/architecture/reviews/*)
**Purpose:**
- Design decision records
- Architectural rationale
- Decision context and trade-offs
- **Frozen once approved**

### Public APIs (docs/architecture/api/*)
**Purpose:**
- Interface contracts
- Public API documentation
- Integration requirements
- **Frozen once approved**

### Roadmaps (docs/roadmaps/milestones/*)
**Purpose:**
- Approved milestone plans
- Timeline and priorities
- Implementation targets
- **Frozen once approved**

### Reports (docs/reports/*)
**Purpose:**
- Implementation summaries
- Analysis results
- Guidance documents
- **Active and updatable**

### Development Guidelines (docs/development/*)
**Purpose:**
- Contribution guidelines
- Implementation prompts
- Architecture walkthroughs
- **Active and updatable**

---

## 3. Canonical Source Relationships

### PROJECT_CONTEXT.md
**Answers:** What is this project? How should it be built? What are the quality goals?

**Referenced by:**
- AI_ARCHITECT_GUIDE.md (for onboarding)
- CURRENT_STATE.md (for context)
- SOURCE_OF_TRUTH.md (as canonical source)
- GOVERNANCE.md (for philosophy)

### CURRENT_STATE.md
**Answers:** What is the current status? What should I implement next?

**Referenced by:**
- AI_ARCHITECT_GUIDE.md (for recovery)
- SOURCE_OF_TRUTH.md (as canonical source)
- GOVERNANCE.md (for operational rules)

### AI_ARCHITECT_GUIDE.md
**Answers:** How do I recover the project? What's the reading order? How do I work?

**Referenced by:**
- SOURCE_OF_TRUTH.md (as canonical source)
- GOVERNANCE.md (for methodology)

### ARCHITECTURE_OVERVIEW.md
**Answers:** How is the system organized? What are the major subsystems?

**Referenced by:**
- AI_ARCHITECT_GUIDE.md (for orientation)
- SOURCE_OF_TRUTH.md (as canonical source)
- GOVERNANCE.md (for overview rules)

### Specifications
**Answers:** How does X work? What are the implementation requirements?

**Referenced by:**
- ARCHITECTURE_OVERVIEW.md (for location)
- Implementation code
- Test files
- SOURCE_OF_TRUTH.md (as canonical source)

### Architecture Reviews
**Answers:** Why was this decision made? What's the design rationale?

**Referenced by:**
- Specifications (for context)
- Implementation code
- SOURCE_OF_TRUTH.md (as canonical source)

### Public APIs
**Answers:** What interfaces must I use? What are the contracts?

**Referenced by:**
- Implementation code
- Integration documentation
- SOURCE_OF_TRUTH.md (as canonical source)

### Roadmaps
**Answers:** What are the priorities? What's the timeline?

**Referenced by:**
- CURRENT_STATE.md (for next tasks)
- Implementation planning
- SOURCE_OF_TRUTH.md (as canonical source)

### Reports
**Answers:** What was implemented? What were the results?

**Referenced by:**
- Historical reference
- Implementation summaries
- SOURCE_OF_TRUTH.md (as canonical source)

### Development Guidelines
**Answers:** How do I contribute? How do I implement?

**Referenced by:**
- New developers
- Implementation teams
- SOURCE_OF_TRUTH.md (as canonical source)

---

## 4. Documentation Lifecycle

### Document Type Status Matrix

| Document Type | Mutable | Frozen | Primary Owner | Purpose |
|---------------|---------|--------|---------------|---------|
| **Overview** | | | | |
| PROJECT_CONTEXT.md | ✅ | ❌ | Architect | Mission, vision, philosophy, quality goals |
| OPERATIONAL_DASHBOARD.md | ✅ | ❌ | Implementer | Operational status, next tasks |
| AI_ARCHITECT_GUIDE.md | ✅ | ❌ | Architect | AI handover methodology |
| ARCHITECTURE_OVERVIEW.md | ✅ | ❌ | Architect | High-level system overview |
| GOVERNANCE.md | ✅ | ❌ | Architect | Documentation governance rules |
| SOURCE_OF_TRUTH.md | ✅ | ❌ | Architect | Canonical source references |
| | | | | |
| **Specifications** | | | | |
| Engine specifications | ❌ | ✅ | Architect | Implementation contracts |
| Research specifications | ❌ | ✅ | Architect | Study composition contracts |
| Optimization specifications | ❌ | ✅ | Architect | Algorithm contracts |
| | | | | |
| **Architecture Reviews** | | | | |
| Design decision records | ❌ | ✅ | Architect | Architectural decisions |
| | | | | |
| **Public APIs** | | | | |
| Interface contracts | ❌ | ✅ | Architect | Public API documentation |
| | | | | |
| **Roadmaps** | | | | |
| Milestone planning | ❌ | ✅ | Architect | Project roadmap |
| | | | | |
| **Reports** | | | | |
| Implementation summaries | ✅ | ❌ | Implementer | Work completion summaries |
| | | | | |
| **Development Guidelines** | | | | |
| Contribution guidelines | ✅ | ❌ | Implementer | Development procedures |
| Architecture walkthroughs | ✅ | ❌ | Implementer | System architecture guide |

### Lifecycle Rules

**For Canonical Documents (Specifications, Architecture Reviews, Public APIs, Roadmaps):**

- **Once approved:** Frozen and cannot be changed without architect approval
- **Can be refactored:** Internal implementation changes allowed
- **Can be clarified:** Minor clarifications and formatting improvements
- **Cannot be modified:** Behavioral changes, scope changes, requirement modifications

### Documentation Growth Rule
The documentation system is considered architecturally mature. New permanent documents must not be created merely to simplify a conversation or implementation session. A new permanent document may only be introduced if it owns a genuinely new responsibility that cannot be assigned to an existing document without violating the "one responsibility per document" principle.

**Documentation does not grow by its own initiative. It evolves only when a real architectural need demonstrates that something is missing.**

Default decision process for new requirements:
1. Reuse an existing document.
2. Extend an existing document if it remains within its responsibility.
3. Create a new document only if neither of the previous options is architecturally correct.

**For Active Documents (PROJECT_CONTEXT.md, OPERATIONAL_DASHBOARD.md, etc.):**

- **Regularly updated:** As work progresses and status changes
- **Version controlled:** Track changes over time
- **Always current:** Reflect current project state
- **Never duplicated:** Reference canonical sources instead

**For Governance Documents (GOVERNANCE.md, SOURCE_OF_TRUTH.md):**

- **Updated as needed:** When governance rules require adjustment
- **Version controlled:** Track governance evolution
- **Always current:** Reflect current governance state
- **Reference canonical sources:** Never duplicate canonical content

### When to Update Documents

**Canonical Documents:**

- **Specifications:** Bug fixes, clarifications, formatting improvements
- **Architecture Reviews:** Clarifications, formatting improvements
- **Public APIs:** Clarifications, formatting improvements
- **Roadmaps:** Timeline adjustments, priority changes

**Active Documents:**

- **PROJECT_CONTEXT.md:** Mission, vision, philosophy updates
- **OPERATIONAL_DASHBOARD.md:** Operational status updates
- **AI_ARCHITECT_GUIDET_GUIDE.md:** Onboarding methodology updates
- **ARCHITECTURE_OVERVIEW.md:** High-level overview updates

**Governance Documents:**

- **GOVERNANCE.md:** Governance rule updates
- **SOURCE_OF_TRUTH.md:** Reference updates

### When to Create New Documents

**New Canonical Document:**

1. **Question has no existing answer** in any document
2. **Question is important** for project success
3. **Answer is substantial** and needs its own document
4. **Answer will be frequently referenced** by others

**New Active Document:**

1. **Need to reference** the canonical source
2. **Need to organize** related information
3. **Need to guide** users to the canonical source

**New Governance Document:**

1. **Need to document** new governance rules
2. **Need to establish** new document relationships
3. **Need to guide** future documentation decisions

### Documentation Convergence

**Adding a new document is the last resort.**

**Improving an existing document is the default.**

**Documentation should converge over time instead of expanding indefinitely.**

### Temporary Documents

**Implementation reports,**
**migration reports,**
**audit reports,**
**refactoring summaries,**
**and similar temporary documents**
**must never become permanent project documentation.**

**Git history is the permanent historical record.**

### When to Remove Documents

**Remove when:**

- **Content is duplicated** in another document
- **Purpose is no longer needed**
- **Scope has changed** significantly
- **Governance rules** require removal

**Never remove:**
- **Canonical sources** without architect approval
- **Historical records** without proper archival
- **Critical documentation** without replacement

### Documentation Version Metadata

**Every major document should include:**

```markdown
Status: APPROVED
Version: v0.2.3
Last Reviewed: 2026-07-23
Maintainer: Chief Architect
```

**Metadata fields:**

- **Status:** APPROVED, FROZEN, ACTIVE, DRAFT
- **Version:** Semantic version (v0.2.3)
- **Last Reviewed:** Date of last review
- **Maintainer:** Primary document owner
- **Created:** Creation date
- **Last Updated:** Last modification date

**Example header:**

```markdown
# AI Handover & Continuity Guide

**Document Type:** AI Onboarding Guide  
**Status:** APPROVED  
**Version:** v0.2.3  
**Last Updated:** 2026-07-23  
**Maintainer:** Chief Architect  
**Audience:** AI Developers  

---
```

### Documentation Quality Gates

**Before creating new documents:**

- [ ] Determine if canonical source exists
- [ ] Check if reference document is sufficient
- [ ] Verify governance approval
- [ ] Ensure proper categorization
- [ ] Document purpose and scope

**Before updating documents:**

- [ ] Identify the question being addressed
- [ ] Find the canonical source
- [ ] Reference the canonical source
- [ ] Do not redefine canonical content
- [ ] Update metadata appropriately

** before removing documents:**

- [ ] Verify no other document contains the content
- [ ] Ensure no dependencies on the document
- [ ] Get architect approval
- [ ] Archive historical records
- [ ] Update references

### Documentation Lifecycle Summary

**The documentation lifecycle follows these principles:**

1. **Single Responsibility:** Each document has one clear purpose
2. **Canonical Sources:** Every question has exactly one source of truth
3. **Governance Framework:** Rules guide all documentation decisions
4. **Version Control:** Track changes over time
5. **Quality Assurance:** Maintain high standards
6. **Scalability:** Structure supports growth
7. **Maintainability:** Easy to understand and update

**This lifecycle ensures documentation remains:**

- **Authoritative:** Clear sources of truth
- **Predictable:** Consistent structure and rules
- **Maintainable:** Easy to understand and update
- **Scalable:** Supports project growth
- **Quality:** High standards maintained

---

**Document Status:** Complete & Accurate  
**Last Updated:** 2026-07-23  
**Maintainer:** Chief Architect