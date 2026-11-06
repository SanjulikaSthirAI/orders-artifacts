# 0002. The committed OpenAPI file is the contract

- Status: accepted
- Date: 2026-11-01

## Context

The UI and other services build against an API. A hand-written description drifts from the code, and a description
nobody checks is worse than none.

## Decision

Each service commits `openapi.yaml`, generated from its code by a script. A contract test fails when the file and
the code disagree. Consumers read the file, not the code.

## Consequences

- Changing an API means regenerating the file and reviewing its diff, so contract changes are visible in review.
- The file is code-owned: changes to it need the code owners' review.
- Breaking changes are caught at review, and require an ADR (see the API standards).
