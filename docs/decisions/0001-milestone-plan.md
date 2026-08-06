# ADR 0001: Milestone Plan and Packaging Layout

## Status

Accepted

## Date

2026-08-06

## Context

This project will be developed through incremental milestones. The goal is to establish a stable foundation before adding advanced retrieval capabilities.

The initial scope decision is to define M0–M6 as the first complete v1.0 release. This prioritizes a working, understandable system over premature complexity.

## Milestone Plan

### M0 — Foundation

- Repository setup
- Development workflow
- Documentation
- Branch protection
- Initial architecture decisions

### M1 — Application Skeleton

- Project structure
- Configuration
- Basic application setup

### M2 — Data and Storage Foundation

- Database integration
- Persistence layer
- Local development environment

### M3 — Ingestion Pipeline

- Document ingestion
- Processing workflow
- Data preparation

### M4 — Retrieval Foundation

- Search capabilities
- Retrieval pipeline
- Evaluation of retrieval quality

### M5 — Application Features

- User-facing functionality
- Integration between components

### M6 — v1.0 Release

- Stable workflow
- Tested functionality
- Documented deployment process

## Decision: M0–M6 Defines v1.0 Scope

Advanced capabilities beyond M6 are intentionally excluded from the first release.

The purpose of v1.0 is to prove the core architecture, workflow, and reliability of the system before adding additional complexity.

## Decision: Evaluation Before Advanced Retrieval

Evaluation is prioritized before implementing advanced retrieval strategies.

Without measurable evaluation criteria, improvements to retrieval systems cannot be objectively compared. Establishing evaluation first allows future retrieval improvements to be measured rather than judged by intuition.

## Packaging Decision

The project will use:

- `src/` layout
- A single installable Python package
- `rag/` and `ingestion/` as subpackages

Example structure:
```
src/
├── app/
│   ├── rag/
│   ├── ingestion/
    └── ...
```

## Rationale

The project will remain a single package rather than splitting components into separate services.

Separate services introduce additional operational complexity:

- deployment overhead
- version coordination
- network boundaries
- additional infrastructure requirements

The current stage does not require these tradeoffs.

Distribution and service separation are deferred until there is a demonstrated need.

## Consequences

The project gains:

- simpler development workflow
- easier local execution
- clearer ownership of components
- fewer infrastructure concerns

Future separation into services remains possible if scaling requirements justify it.