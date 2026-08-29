# Feature Specification: [FEATURE NAME]

## [Short subtitle — what this feature does for the user]

**Feature Branch**: `[###-feature-name]`

**Created**: [DATE]

**Last updated**: [DATE]

**Status**: Draft

**Input**: User description: "$ARGUMENTS"

> **Agent note:** This is a plan-stage document. When editing, follow `.specify/memory/standards/readme_standards_plan.json`.
> For Module READMEs documenting shipped code, use `.specify/memory/standards/readme_standards_shipped.json`.

---

## Index

| # | Section | Summary |
|---|---------|---------|
| 1 | [Applicable Constitution Principles](#applicable-constitution-principles) | Which of the 9 project principles this feature touches |
| 2 | [User Scenarios & Testing](#user-scenarios--testing) | User stories with acceptance criteria and priorities |
| 3 | [Requirements](#requirements) | Functional requirements (FR-*) and key entities |
| 4 | [Success Criteria](#success-criteria) | Measurable outcomes |
| 5 | [Assumptions](#assumptions) | Scope boundaries and dependencies |

---

## Applicable Constitution Principles

*Per project governance: every spec.md MUST reference which principles apply. Read `.specify/memory/constitution.md` first.*

| Principle | Applies? | Notes |
|-----------|----------|-------|
| I. Two-Layer Architecture | YES / NO / N/A | Does this feature add business logic to forms_toolkit/? |
| II. Spec-Driven Development | YES — this doc | This spec IS the Principle II artifact |
| III. Bottom-Up Test-First | YES / NO / N/A | Does this feature need new forms_toolkit/ or Django tests? |
| IV. HTMX-First Frontend | YES / NO / N/A | Does this feature add UI templates or JS? |
| V. Python Code Quality | YES / NO / N/A | Does this feature add new Python modules or functions? |
| VI. Frontend Component Catalog | YES / NO / N/A | Does this feature add new CSS classes or components? |
| VII. Documentation Lifecycle | YES — always | A Module README must be written after ship |
| VIII. Schema Versioning & Immutability | YES / NO / N/A | Does this feature touch forms, responses, or schema? If yes: does it respect draft/published split, FormVersion immutability, soft-delete, UUID stability? |
| IX. Auditability | YES / NO / N/A | Does this feature trigger auditable events (publish, archive, delete, collaborator change, ownership transfer; group create/soft-delete/clone/visibility/clonable/member/access changes; or user permission grant/revoke)? If yes: does services.py write to portal_core_auditlog? |

---

## User Scenarios & Testing *(mandatory)*

<!--
  IMPORTANT: User stories should be PRIORITIZED as user journeys ordered by importance.
  Each user story/journey must be INDEPENDENTLY TESTABLE - meaning if you implement just ONE of them,
  you should still have a viable MVP (Minimum Viable Product) that delivers value.

  Assign priorities (P1, P2, P3, etc.) to each story, where P1 is the most critical.
  Think of each story as a standalone slice of functionality that can be:
  - Developed independently
  - Tested independently
  - Deployed independently
  - Demonstrated to users independently
-->

### User Story 1 - [Brief Title] (Priority: P1)

[Describe this user journey in plain language]

**Why this priority**: [Explain the value and why it has this priority level]

**Independent Test**: [Describe how this can be tested independently - e.g., "Can be fully tested by [specific action] and delivers [specific value]"]

**Acceptance Scenarios**:

1. **Given** [initial state], **When** [action], **Then** [expected outcome]
2. **Given** [initial state], **When** [action], **Then** [expected outcome]

---

### User Story 2 - [Brief Title] (Priority: P2)

[Describe this user journey in plain language]

**Why this priority**: [Explain the value and why it has this priority level]

**Independent Test**: [Describe how this can be tested independently]

**Acceptance Scenarios**:

1. **Given** [initial state], **When** [action], **Then** [expected outcome]

---

### User Story 3 - [Brief Title] (Priority: P3)

[Describe this user journey in plain language]

**Why this priority**: [Explain the value and why it has this priority level]

**Independent Test**: [Describe how this can be tested independently]

**Acceptance Scenarios**:

1. **Given** [initial state], **When** [action], **Then** [expected outcome]

---

[Add more user stories as needed, each with an assigned priority]

### Edge Cases

<!--
  ACTION REQUIRED: The content in this section represents placeholders.
  Fill them out with the right edge cases.
-->

- What happens when [boundary condition]?
- How does system handle [error scenario]?

## Requirements *(mandatory)*

<!--
  ACTION REQUIRED: The content in this section represents placeholders.
  Fill them out with the right functional requirements.
-->

### Functional Requirements

- **FR-001**: System MUST [specific capability, e.g., "allow users to create accounts"]
- **FR-002**: System MUST [specific capability, e.g., "validate email addresses"]
- **FR-003**: Users MUST be able to [key interaction, e.g., "reset their password"]
- **FR-004**: System MUST [data requirement, e.g., "persist user preferences"]
- **FR-005**: System MUST [behavior, e.g., "log all security events"]

*Example of marking unclear requirements:*

- **FR-006**: System MUST authenticate users via [NEEDS CLARIFICATION: auth method not specified - email/password, SSO, OAuth?]
- **FR-007**: System MUST retain user data for [NEEDS CLARIFICATION: retention period not specified]

### Key Entities *(include if feature involves data)*

- **[Entity 1]**: [What it represents, key attributes without implementation]
- **[Entity 2]**: [What it represents, relationships to other entities]

## Success Criteria *(mandatory)*

<!--
  ACTION REQUIRED: Define measurable success criteria.
  These must be technology-agnostic and measurable.
-->

### Measurable Outcomes

- **SC-001**: [Measurable metric, e.g., "Users can complete account creation in under 2 minutes"]
- **SC-002**: [Measurable metric, e.g., "System handles 1000 concurrent users without degradation"]
- **SC-003**: [User satisfaction metric, e.g., "90% of users successfully complete primary task on first attempt"]
- **SC-004**: [Business metric, e.g., "Reduce support tickets related to [X] by 50%"]

## Assumptions

<!--
  ACTION REQUIRED: The content in this section represents placeholders.
  Fill them out with the right assumptions based on reasonable defaults
  chosen when the feature description did not specify certain details.
-->

- [Assumption about target users, e.g., "Users have stable internet connectivity"]
- [Assumption about scope boundaries, e.g., "Mobile support is out of scope for v1"]
- [Assumption about data/environment, e.g., "Existing authentication system will be reused"]
- [Dependency on existing system/service, e.g., "Requires access to the existing user profile API"]
