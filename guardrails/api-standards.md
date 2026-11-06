# API standards

## Contract first

- Each service publishes its contract as `openapi.yaml` at the repo root. It is the source of truth that other
  teams and the UI build against.
- The file is generated from the code and checked by a contract test, so the two cannot drift. See ADR 0002.
- A change to a route, request or response shape, or status code is a contract change.

## Compatibility

- Changes are additive: new endpoints, new optional fields, new enum values the client can ignore.
- A breaking change (removing or renaming a field, endpoint or status, tightening validation, changing a meaning)
  needs an ADR, a version plan and approval from the solution architect. It is a protected contract change.
- Endpoints that other repos consume are listed as protected contracts in the approved design.

## Shape

- Resource paths are plural nouns: `/orders`, `/orders/{order_id}`. State changes that are not plain updates are
  sub-resources or actions: `POST /orders/{order_id}/cancel`, `POST /orders/{order_id}/refunds`.
- JSON bodies use `snake_case`. Timestamps are ISO 8601 in UTC. Identifiers are opaque strings.
- Money is `*_cents` as an integer, with the currency stated in the contract if more than one is possible.
- List endpoints are ordered deterministically and filter through query parameters. Anything that can grow beyond
  a few hundred rows is paginated.

## Errors

- Error bodies are `{"detail": "<message>"}`.
- 404 unknown resource; 409 the resource's state forbids the action; 422 invalid input; 401 and 403 for
  authentication and authorization. Do not use 200 with an error body.
- Every non-2xx response an endpoint can return is declared in the contract.

## Operations that move money or cannot be undone

- They must be idempotent: a repeated request with the same idempotency key returns the first result and does
  not act twice.
- They record who did what and when, in a form that can be queried afterwards.
