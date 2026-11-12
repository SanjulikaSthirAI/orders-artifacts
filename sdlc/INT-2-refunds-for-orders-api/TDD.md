# Technical design: Refund Orders through the orders API

## 1. Context and scope

Support needs to complete eligible full-order refunds through the orders API without manual finance handling. The approved scope is limited to orders API support for full-order refunds on recent orders, duplicate prevention, authorization, idempotent retries, clear refund errors, and internal audit/history recording.

This is a brownfield change. `SanjulikaSthirAI/orders-api` receives the implementation and additive API contract change. `SanjulikaSthirAI/orders-ui` is intentionally unchanged because Orders screen changes are excluded from the approved scope.

The design is currently blocked by recorded brownfield mismatches INT-2-M1 through INT-2-M6. The technical design below describes the required target state once those blockers are resolved.

## 2. Components and changes

### 2.1 SanjulikaSthirAI/orders-api (brownfield)

Add `POST /orders/{order_id}/refunds` as an additive FastAPI route following the REST service guardrail layering:

- Route layer: authenticate and authorize first, require `refund:orders`, require the `Idempotency-Key` header, call the refund service/store, and map domain exceptions to declared HTTP errors.
- Models: add a `RefundResponse` model containing only `refund_timestamp` and `refund_amount_cents`; do not expose provider references, audit fields, payment tender/capture fields, or eligibility internals.
- Store/service layer: add refund domain logic, idempotency handling, order-scoped locking, durable refund state, provider adapter calls, and audit/history writes.
- Payment provider boundary: introduce an injected provider adapter interface. For this story use a deterministic fake/test implementation; named real provider wiring is a follow-up blocker.

Request handling order is fixed:

1. Authenticate caller.
2. Authorize `refund:orders` permission/role and record authenticated support user ID only for authorized attempts.
3. Validate required `Idempotency-Key` header.
4. Check global idempotency record by key and replay or reject conflicts.
5. Acquire and persist an order-scoped refund-in-progress lock transactionally before invoking the provider.
6. Evaluate refund eligibility using server/system time and exact order placement timestamp.
7. Call the payment-provider adapter for otherwise eligible orders, passing the same `Idempotency-Key` as provider idempotency key.
8. Persist provider refund/reference details internally as soon as they are available.
9. Mark the order refunded with server/system refund timestamp and full captured amount when the provider accepts or initiates the refund.
10. Persist the idempotency outcome and audit record.

Eligibility failure precedence after authorization and idempotency replay is:

1. `refund already in progress`
2. `order already refunded`
3. `order older than 30 days`
4. `order not refundable or not found`

Provider failure occurs only after an otherwise eligible request reaches the provider, returns `refund payment failed`, does not mark the order refunded, clears the order lock, persists the failed idempotency outcome, and records a failed audit entry. Same-key retries replay that failure; different-key retries may try again if the order remains eligible.

The store must support crash/retry recovery for the case where money refund details were obtained but the order was not marked refunded. Same-key retry uses the stored provider refund/reference details to complete the order refund marker without issuing a second provider refund.

Add internal persisted eligibility data needed by first-version rules: payment capture/tender type, capture count, successful capture amount, refund marker, refund timestamp, refund amount, refund-in-progress lock, prior refund indicator, chargeback indicator, payment dispute indicator, and payment reversal indicator. These are internal only and must not be added to existing order API response schemas.

For orders predating the feature, backfill eligibility data from existing payment/order records during migration. If required eligibility data is unavailable, treat the order as `order not refundable or not found`.

Every acceptance criterion gets automated tests with test names referencing the AC. Tests inject the clock and provider adapter, avoid real time and network, and cover declared failure paths.

### 2.2 SanjulikaSthirAI/orders-ui (brownfield)

No UI changes. Do not add refund endpoint consumption, Orders screen controls, or UI state for refunds in this design because Orders screen changes are excluded.

## 3. API contract changes

`orders-api` changes are additive. The committed `openapi.yaml` remains the source of truth and must be regenerated from FastAPI code with the contract test updated in the same change.

| Operation | Change | Request | Success | Errors |
| --- | --- | --- | --- | --- |
| `POST /orders/{order_id}/refunds` | Added | Path `order_id`, required `Idempotency-Key` header, no request body | `201` with `refund_timestamp`, `refund_amount_cents` | `400` missing idempotency key; `401` unauthenticated; `403` not authorized to refund; `404` order not refundable or not found; `409` older than 30 days, already refunded, already in progress, refund payment failed, idempotency conflict; `422` validation error |

Error bodies follow the API standards shape `{"detail":"<message>"}`. Required detail messages are:

- `missing idempotency key`
- `not authorized to refund`
- `order not refundable or not found`
- `order older than 30 days`
- `order already refunded`
- `refund already in progress`
- `refund payment failed`
- `idempotency key conflict`

No existing endpoint is removed or changed.

## 4. Data changes and migrations

Extend the orders API persistence boundary so refund state is owned with the Order and can be updated transactionally. Use the existing orders-api persistence mechanism if present. If the base app is in-memory only, add SQLite with repository methods and migrations/initialization covered by tests.

Persist at least:

- refund marker, refund timestamp, and refund amount in cents;
- order-scoped refund-in-progress lock;
- global refund idempotency records keyed by `Idempotency-Key`, with order ID, request fingerprint, status, response/error outcome, timestamps, and internal provider refund/reference details when available;
- refund audit records for successful and failed attempts, including support user ID for authorized attempts, request timestamp, order ID for failures, and failure category;
- internal payment/refund eligibility fields needed to enforce first-version refund rules.

Idempotency records must be retained for at least 30 days. Records older than the retention period may expire by scheduled cleanup or lazy deletion on access; an expired key is treated as new.

Migrations must backfill internal eligibility fields for recent historical orders from existing payment/order records. Orders whose required eligibility data cannot be recovered are treated as not refundable or not found.

## 5. Security

Security classification: refunding moves money and is high risk under the security standards.

Authentication and authorization:

- `POST /orders/{order_id}/refunds` requires authentication using the existing orders-api auth dependency.
- The caller must have `refund:orders` permission/role.
- Authorization is checked before idempotency, audit, or lock records are created.
- If the caller has refund permission but cannot access the referenced order, return `order not refundable or not found`.

Input/output controls:

- Validate `order_id` and required `Idempotency-Key` at the FastAPI/Pydantic boundary.
- Return only refund timestamp and amount on success.
- Do not return provider references, audit identifiers, customer personal data, internal eligibility data, stack traces, or database errors.
- Error bodies use only approved clear messages.

Secrets and provider integration:

- This story uses an injected provider adapter with deterministic fake/test implementation.
- Future real provider credentials must come from environment variables and must not be committed.

Threats and mitigations:

- Duplicate money movement: mitigated by required idempotency key, global idempotency records, provider idempotency key pass-through, and persisted order-scoped lock.
- Unauthorized refunds: mitigated by server-side `refund:orders` check before side effects.
- Existence probing: mitigated by returning `order not refundable or not found` for inaccessible, missing, and first-version-ineligible orders.
- Sensitive data leakage: mitigated by minimal response fields and log restrictions.
- Lost recovery after partial failure: mitigated by persisting provider reference details internally and completing refund marking on same-key retry.

## 6. Observability

Record internal audit/history for every authorized refund attempt:

- Successful refund: support user ID, request timestamp, order ID, refund timestamp, refund amount, and internal provider reference if available.
- Failed refund attempt: support user ID, request timestamp, order ID, and failure category.

Log refund attempt outcomes with order ID and category, but do not log customer names, addresses, payment details, provider secrets, or raw sensitive provider payloads.

Expose no refund audit/history retrieval API in the first version.

## 7. Non-functional requirements

NFR-1 target is defined as: during each calendar month, at least 90% of Eligible refund requests recorded for support are completed through the orders API without Manual finance intervention.

The implementation supports this by providing the API path, authorization, idempotency, duplicate prevention, durable state, and audit records needed to complete eligible refunds reliably. The data source for the denominator remains a non-blocking open item from the approved requirements.

## 8. Alternatives considered

- Put `Idempotency-Key` in the JSON body: rejected by technical answer; use a required HTTP header.
- Scope idempotency by `(order_id, key)`: rejected because a global key deterministically catches reuse against a different order as an idempotency conflict.
- Store refund state only in process memory: rejected because refund markers, idempotency records, locks, and audit history must survive restarts.
- Add a separate refund database/service: rejected; refund state remains in the orders API persistence boundary so it is owned with the Order and updated transactionally.
- Add orders-ui refund controls: rejected because Orders screen changes are excluded.
- Expose payment/provider and audit details in the success response: rejected; support receives only refund timestamp and amount.

## 9. Decisions

- Add one additive orders API operation: `POST /orders/{order_id}/refunds`.
- Use required `Idempotency-Key` header and no request body.
- Use an injected payment-provider adapter interface with deterministic fake/test implementation in this story; real provider wiring is a follow-up blocker.
- Use durable persistence for refund marker, in-progress lock, idempotency records, eligibility fields, and audit records.
- Keep missing/inaccessible/first-version-ineligible orders indistinguishable as `order not refundable or not found`.
- Do not change `orders-ui` for this intent.
- If the repo has no existing durable persistence and SQLite is added, record an ADR for that persistence decision. Otherwise no ADR is needed.

## Appendix A. Requirement coverage

| Requirement | Section | How |
| --- | --- | --- |
| FR-1 | 2.1 | The refund route, service, provider adapter, authorization, eligibility checks, and full captured amount refund flow initiate eligible full-order refunds. |
| FR-2 | 2.1 | Provider acceptance marks the order refunded with server-time timestamp and refund amount and returns those two fields. |
| FR-3 | 2.1 | Eligibility uses injected server/system time and exact order placement timestamp and returns the older-than-30-days error at the defined precedence. |
| FR-4 | 2.1 | Global idempotency, persisted order-scoped locks, refund markers, and same-key recovery prevent duplicate refunds and concurrent provider calls. |
| FR-5 | 5 | The endpoint authenticates with the existing dependency, requires `refund:orders`, and hides inaccessible orders behind the not-refundable-or-not-found error. |
| FR-6 | 2.1 | Internal eligibility fields enforce first-version refundable payment, capture, prior refund, chargeback, dispute, and reversal rules without rejecting fulfilled, shipped, or delivered orders solely for fulfillment state. |
| FR-7 | 2.1 | Provider refusal or failure returns `refund payment failed`, records the failed outcome and audit entry, clears the lock, and does not mark the order refunded. |
| FR-8 | 2.1 | The required global `Idempotency-Key` records request fingerprints and outcomes for at least 30 days, replays known outcomes, rejects conflicts, and reports in-progress retries. |
| FR-9 | 6 | The design records successful and failed refund attempts internally with server-time timestamps and exposes no refund history retrieval API. |

## Appendix B. NFR targets

| NFR | Requirement | Target |
| --- | --- | --- |
| NFR-1 | Support can complete Eligible refund requests through the orders API without Manual finance intervention for at least 90% of refund requests during each calendar month. | >= 90% of Eligible refund requests completed through the orders API without Manual finance intervention per calendar month |

## Appendix C. Brownfield mismatches

| ID | Repo | Kind | Detail | Owner | Status | Resolution |
| --- | --- | --- | --- | --- | --- | --- |
| INT-2-M1 | `SanjulikaSthirAI/orders-api` | contract | Approved requirements require a refund API operation for support staff, including idempotency input and declared success/failure responses. The current code and published/deployed OpenAPI 1.0.0 expose only GET /orders, POST /orders, GET /orders/{order_id}, and POST /orders/{order_id}/cancel; there is no POST /orders/{order_id}/refunds endpoint or refund request/response schemas. This blocks the core refund design and is a required additive contract change. | orders-api team | blocker | recorded as blocker |
| INT-2-M2 | `SanjulikaSthirAI/orders-api` | code | Base-branch code has components main, models, and store for listing, placing, getting, and cancelling orders only. There is no refund domain model, store/service rule, payment-provider refund integration boundary, refund-in-progress state, idempotency record storage, or audit/history recording needed by FR-1 through FR-9. | orders-api team | blocker | recorded as blocker |
| INT-2-M3 | `SanjulikaSthirAI/orders-api` | code | Existing Order schema/status model contains id, customer_name, items, total_cents, status, created_at, and delivered_at with statuses placed/shipped/delivered/cancelled. It has no payment capture/tender data, refund marker, refund timestamp, refund amount, prior refund/chargeback/dispute/reversal indicators, or multi-capture information required to evaluate the first-version refund eligibility rules. | orders-api team | blocker | recorded as blocker |
| INT-2-M4 | `SanjulikaSthirAI/orders-api` | deployment | The deployed API contract is version 1.0.0 and matches the current non-refund contract. Deployed version 1.0.0 therefore lacks the refund capability required by the approved intent and requirements; deployment must be updated after the additive API and code changes are implemented. | orders-api team | blocker | recorded as blocker |
| INT-2-M5 | `SanjulikaSthirAI/orders-ui` | contract | orders-ui is a brownfield browser UI repo with no API contract configured, which is consistent for a UI, but the approved scope excludes Orders screen changes. No refund endpoint consumption should be added in this repo for this design unless scope changes. | orders-ui team | blocker | recorded as blocker |
| INT-2-M6 | `SanjulikaSthirAI/orders-ui` | code | Base-branch code has UI components api, app, config, and format, with no known endpoints exposed by the repo. Because the approved scope excludes Orders screen changes, there is no code/contract/deployment mismatch requiring UI implementation for this refund design. | orders-ui team | blocker | recorded as blocker |

## Appendix D. Protected contracts

Stories must not change these unless plan.json marks the story as a contract change. Machine-readable copy: `protected-contracts.json`.

| Repo | Files | Endpoints |
| --- | --- | --- |
| `SanjulikaSthirAI/orders-api` | `app/main.py`, `app/models.py`, `app/store.py`, `openapi.yaml` | `GET /orders`, `GET /orders/{order_id}`, `POST /orders`, `POST /orders/{order_id}/cancel`, `POST /orders/{order_id}/refunds` |
| `SanjulikaSthirAI/orders-ui` | `api/**`, `app/**`, `config/**`, `format/**` | - |

## Appendix E. ADRs

| ADR | Meets |
| --- | --- |
| adr/0001-use-sqlite-for-orders-persistence-when-no-durable-store-exis.md | hard to reverse; surprising without context; the result of a real trade-off |

Proposed but not written (an ADR must meet all three tests):

_None._

## Appendix F. Prototypes (throwaway; never used as a starting point at G4)

_None._
