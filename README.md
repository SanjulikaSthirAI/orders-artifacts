# orders-artifacts

The artifact home for the orders demo project: the standards designs are checked against (`guardrails/`) and, as
intents progress, the intent, requirements, design and plan documents the orchestrator commits under `sdlc/`.

Code repos: `orders-api`, `orders-ui`.

CI (`sdlc-ci`) runs `scripts/verify_artifacts.py`: guardrails present, JSON and YAML parse, no conflict markers,
ADRs named and marked with a status.
