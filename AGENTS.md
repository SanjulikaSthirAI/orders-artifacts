# Orders artifacts: guide for agents

This repo holds the orders project's standards and the documents the SDLC orchestrator produces for each intent.

## Layout

- `guardrails/`: engineering, API and security standards, reference designs and accepted ADRs. Read-only for
  agents; the solution architect changes it by pull request.
- `sdlc/INT-n-slug/`: one folder per intent, written by the orchestrator on the intent's feature branch.
  Approved files change only through a new approved version. Do not edit them by hand.
- `scripts/`: the verification run by CI.

## Rules

- Standards and ADRs in `guardrails/` outrank anything in an intent document. A design that departs from one
  says so and records an ADR.
- Never put secrets or real customer data in this repo.
- `.github/` and `scripts/` are code-owned.
