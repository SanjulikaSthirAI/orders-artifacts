# 0001. Python and FastAPI for services

- Status: accepted
- Date: 2026-11-01

## Context

New services need one language and framework so people can move between them, review each other's work, and share
tooling. The team writes Python and needs typed request validation and a generated API contract.

## Decision

Services are written in Python 3.12 with FastAPI and Pydantic, tested with pytest and linted with ruff.

## Consequences

- OpenAPI comes from the code (see ADR 0002), which keeps contracts honest.
- Request validation is declared once, in the models.
- A service in another language needs its own ADR before design approval.
- FastAPI and Pydantic upgrades can change the generated contract; they are pinned and upgraded deliberately.
