# Technical design: Orders API refund action

## 1. Context and scope

Support needs the Orders API to record that an Order has been refunded so refunds are no longer tracked in a spreadsheet. This design is for the brownfield `SanjulikaSthirAI/orders-api` service and is constrained to the approved in-memory-store scope: no payment-provider integration, no partial refunds, no UI changes, and no new persistence beyond the existing in-memory store.

The design cannot proceed to implementation while the recorded G2 blockers remain unresolved. The solution architect recorded all eight brownfield mismatches as blockers, including security/idempotency conflicts, missing contract/code support for refunds, deployment/versioning gaps, and UI deployment/contract assessment gaps.

Traceability: scope and exclusions come from the approved intent; refund business behavior comes from FR-1 through FR-9 and BR-1 through BR-10; blocker status comes from answers INT-4-G2-Q1 through INT-4-G2-Q8.

## 2. Components and changes

### 2.1 SanjulikaSthirAI/orders-api (brownfield)

If the blockers are resolved without changing the approved requirements, implement the refund behavior within the existing FastAPI reference-service layering:

| Component | Planned change | Trace |
| --- | --- | --- |
| `app/models.py` | Extend the `Order` response model with additive fields `refunded: bool` and `refund_time: string date-time or null`. Newly created and non-refunded orders return `refunded: false` and `refund_time: null`. | FR-2, FR-9, API standards: additive response fields and snake_case JSON |
| `app/models.py` | Add a refund success response shape only if it can share the `Order` model or expose the required fields without duplicating conflicting state. | FR-2, FR-9 |
| `app/store.py` | Add refund state to the existing in-memory order record and add a store-level refund operation that applies refund rules without HTTP knowledge. | FR-1, FR-3, FR-4, FR-5, FR-6, FR-7, reference design |
| `app/store.py` | Inject or pass a deterministic clock into refund eligibility checks; do not call real time directly in rules or tests. | FR-1, FR-6, engineering standards, reference design |
| `app/store.py` | Enforce refund blocker priority: already refunded, then cancelled, then refund window expired. Unknown order remains a not-found condition. | FR-3, FR-7, BR-8, BR-9 |
| `app/store.py` | Preserve the original refund time when a repeat refund is rejected. | FR-4 |
| `app/store.py` | Update cancellation rules so a refunded order cannot later be cancelled and the order remains refunded and not cancelled. | FR-8, FR-9 |
| `app/main.py` | Add `POST /orders/{order_id}/refunds` with no required request body. The route delegates rules to the store and maps domain exceptions to declared HTTP responses. | FR-1 through FR-7, API standards, reference design |
| `app/main.py` | Update the existing cancel route to map the refunded-order cancellation blocker to HTTP 409 with `detail: "order already refunded"`. | FR-8, API standards errors |
| `openapi.yaml` | Regenerate the committed OpenAPI contract from code and update the contract test so the generated and committed contracts cannot drift. | FR-1, FR-2, FR-8, FR-9, guardrail ADR 0002 |
| Tests | Add deterministic tests for every acceptance criterion, including exact 30×24-hour boundary behavior and failure paths. | Engineering standards, FR-1 through FR-9 |

The refund action records only refund state and refund time. It does not move money and does not accept or store a Support-provided refund reason or comment.

### 2.2 SanjulikaSthirAI/orders-ui (brownfield)

No UI behavior or screen changes are in scope. The UI repo is listed as affected only because it is part of the known Orders surface and its deployment/contract comparison could not be completed from the supplied evidence. No story should change `orders-ui` behavior for this intent unless a later approved scope change adds UI work.

Any future UI consumption of refund fields must continue to use the Orders API client module and the committed `orders-api/openapi.yaml` contract.

Traceability: UI exclusion comes from the approved intent; API-client constraint comes from the REST reference design; blocker status comes from INT-4-G2-Q7 and INT-4-G2-Q8.

## 3. API contract changes

The intended contract changes are additive, but the contract mismatch is currently recorded as a blocker by INT-4-G2-Q3.

| Operation | Change type | Contract change | Trace |
| --- | --- | --- | --- |
| `POST /orders/{order_id}/refunds` | Added | New refund action. Path parameter `order_id`; no required request body; success returns refund information; `404` for unknown order; `409` for state/window refund blockers; `422` for validation. | FR-1, FR-2, FR-3, FR-4, FR-5, FR-6, FR-7, API standards |
| `POST /orders/{order_id}/cancel` | Changed | Existing success `Order` response gains additive refund fields. Existing `409` response also covers refunded-order cancellation with `detail: "order already refunded"`. | FR-8, FR-9, API standards |
| `POST /orders` | Changed | Existing `201` `Order` response gains `refunded: false` and `refund_time: null`. | FR-9, API standards |
| `GET /orders/{order_id}` | Changed | Existing `200` `Order` response gains `refunded` and `refund_time`. | FR-9, NFR-1 |
| `GET /orders` | Changed | Existing `200` list item `Order` response gains `refunded` and `refund_time`. | FR-9, NFR-1 |

Error bodies follow the existing standards shape `{"detail": "<message>"}`. Refund rejection details are:

- `order not found` for `404` unknown order.
- `order already refunded` for `409` repeat refund and refunded-order cancellation.
- `order cancelled` for `409` cancelled order.
- `refund window expired` for `409` outside the Recent order window.

Timestamps are ISO 8601 UTC. JSON field names use snake_case, so the approved `refundTime` business term is represented in the API as `refund_time`.

## 4. Data changes and migrations

No database migration is in scope because persistence remains the existing in-memory store. The in-memory order record must be extended with refund state and refund time:

- `refunded`: boolean, default `false` for new orders.
- `refund_time`: nullable UTC timestamp, default `null` for new orders.

Refund success sets both fields in the existing order record using the refund action processing time from the injected clock. Repeat refund, cancelled-order refund, expired-window refund, and unknown-order refund must not mutate the order store. A successful refund prevents later cancellation so the invariant remains: an order is never both refunded and cancelled.

Traceability: FR-1, FR-3, FR-4, FR-5, FR-6, FR-8, FR-9; approved exclusion for new persistence.

## 5. Security

Security is a blocking issue for this design. The approved intent excludes caller authentication and rules about who may call the API, but the security standards require authentication and record-level authorization for state-changing endpoints, and require refund/credit behavior to have a specific authorization rule, audit trail, and idempotency key.

Until INT-4-M1 and INT-4-M2 are resolved or explicitly waived by the appropriate owners, implementation must not proceed.

If resolved without scope change, the implementation still must follow the applicable non-conflicting security standards:

- Validate path parameters and any request body at the FastAPI/Pydantic boundary.
- Do not accept or log customer names, contact details, payment details, secrets, or real customer data in tests or fixtures.
- Return only the existing order response fields plus the approved refund fields.
- Return caller-safe error messages using `detail`; do not expose stack traces or internal errors.
- Do not add dependencies or secrets for this change.

Threats and mitigations currently unresolved:

| Threat | Status | Trace |
| --- | --- | --- |
| Unauthorized caller records a refund | Blocked pending authentication/authorization resolution | INT-4-M1, security standards |
| Retry or duplicate request creates ambiguous irreversible state | Blocked pending idempotency/audit resolution | INT-4-M2, API standards |
| Refund record lacks actor/audit trail | Blocked pending audit-resolution decision | INT-4-M1, INT-4-M2 |

## 6. Observability

For the in-scope API change, observability is limited to safe application logs and API responses:

- Log successful refund recording with the order ID and refund time, without customer names, addresses, payment details, or secrets.
- Log rejected refund attempts with the order ID and blocker category only.
- Existing read and list responses expose refund state and refund time so Support can verify whether an order has a refund record without a spreadsheet.

No new metrics, dashboards, tracing system, or persistence-backed audit query is designed because no approved technical answer resolved the audit/idempotency security blockers or added observability scope.

Traceability: NFR-1, FR-2, FR-9, engineering logging standard, security data standard.

## 7. Non-functional requirements

| NFR | Target | Design support |
| --- | --- | --- |
| NFR-1 | 100% of successful `POST /orders`, `GET /orders/{order_id}`, `GET /orders`, refund success, and cancellation success Order responses include `refunded` and `refund_time`; no separate spreadsheet is required to determine recorded refund state from the Orders API. | Additive `Order` response fields and refund success information expose refund state through the API. |

Engineering quality targets:

- Every acceptance criterion AC-1.1 through AC-9.7 has at least one deterministic automated test named for the case it covers.
- Contract test fails if `openapi.yaml` differs from generated FastAPI OpenAPI output.
- Refund-window tests use an injected clock and cover earlier than, equal to, and later than the exact 30×24-hour cutoff.

Traceability: NFR-1, engineering standards, guardrail ADR 0002.

## 8. Alternatives considered

| Alternative | Outcome | Reason | Trace |
| --- | --- | --- | --- |
| Track refunds only in the support spreadsheet | Rejected | Does not meet the approved business outcome or NFR-1. | Approved intent, NFR-1 |
| Add refund behavior to `orders-ui` | Rejected for this design | Orders screen changes are explicitly excluded. | Approved intent exclusions |
| Store partial refunds or Support-provided comments | Rejected | Partial refunds and Support-provided refund reasons/comments are excluded. | Approved intent exclusions, BR-10 |
| Add new database persistence | Rejected | New persistence beyond the existing in-memory store is excluded. | Approved intent exclusions |
| Model refund as an `OrderStatus` enum value only | Rejected | Requirements require cancellation state and refund fields to be visible together while preserving the invariant that an order is never both cancelled and refunded. Additive `refunded` and `refund_time` fields satisfy FR-9 without renaming existing status meanings. | FR-8, FR-9, API compatibility standards |
| Make repeat refund idempotently return the original success response | Rejected by approved requirements | Repeat refund must be rejected with reason `order already refunded` and original refund time unchanged. | FR-4 |
| Require a refund request body | Rejected | The approved requirements require processing with only the Order ID and no request body. | FR-1 |

## 9. Decisions

1. Use `POST /orders/{order_id}/refunds` for the refund action, matching the API standard for state changes as sub-resources/actions.
2. Keep refund rules in the store layer and HTTP mapping in the route layer, matching the REST reference design.
3. Represent refund information as additive `Order` response fields `refunded` and `refund_time`, using snake_case per API standards.
4. Use the injected processing clock for both refund eligibility and recorded refund time.
5. Treat unresolved security, idempotency/audit, contract, code, deployment, and UI assessment mismatches as blockers because the solution architect explicitly recorded them as blockers in INT-4-G2-Q1 through INT-4-G2-Q8.

No ADR is proposed by this design. The planned technical choices follow existing guardrails and reference designs; the genuinely hard-to-reverse/security-significant questions are currently blockers rather than accepted decisions.

## Appendix A. Requirement coverage

| Requirement | Section | How |
| --- | --- | --- |
| FR-1 | 2.1 | The design adds a `POST /orders/{order_id}/refunds` route with no required body and a store operation that records refund state and refund time using the processing clock. |
| FR-2 | 3 | The refund success contract returns clear refund information including order ID, refunded state, and refund time. |
| FR-3 | 2.1 | The store rejects unknown order IDs without mutation and the route maps that condition to a 404 response with detail `order not found`. |
| FR-4 | 2.1 | The store checks already-refunded orders before other state blockers, rejects with `order already refunded`, and preserves the original refund time. |
| FR-5 | 2.1 | The store rejects cancelled orders with `order cancelled` and leaves the existing cancelled state unchanged. |
| FR-6 | 4 | Refund eligibility compares the injected processing time to the order creation timestamp plus exactly 30×24 hours, allowing equality and rejecting later times without mutation. |
| FR-7 | 2.1 | The store applies the approved refund reason priority: already refunded, then cancelled, then refund window expired. |
| FR-8 | 2.1 | The cancel path gains a refunded-order blocker that returns `order already refunded` and leaves the order refunded and not cancelled. |
| FR-9 | 3 | The `Order` contract gains additive `refunded` and `refund_time` fields in create, read, list, refund success, and cancellation success responses. |

## Appendix B. NFR targets

| NFR | Requirement | Target |
| --- | --- | --- |
| NFR-1 | Support can determine from the Orders API whether an Order has a Refund recorded without consulting a separate spreadsheet. | 100% of successful `POST /orders`, `GET /orders/{order_id}`, `GET /orders`, refund success, and cancellation success Order responses include `refunded` and `refund_time`. |

## Appendix C. Brownfield mismatches

| ID | Repo | Kind | Detail | Owner | Status | Resolution |
| --- | --- | --- | --- | --- | --- | --- |
| INT-4-M1 | `SanjulikaSthirAI/orders-api` | guardrail | Security standards require every endpoint that returns customer data or changes state to require authentication and an authorization check, and anything involving refunds/credits to have its own authorization rule, audit trail, and idempotency key. The approved intent explicitly excludes caller authentication/rules about who may call the API, while the planned refund action changes order state and represents refund recording. This is a guardrail conflict that matters before design approval. | Product Owner / Security specialist / Solution architect | blocker | recorded as blocker |
| INT-4-M2 | `SanjulikaSthirAI/orders-api` | guardrail | API standards say operations that move money or cannot be undone must be idempotent using an idempotency key and record who did what and when. The requirements make refund recording irreversible in practice by preventing repeat refunds and cancellation afterwards, but do not include an idempotency key or actor/audit trail. Even though moving money is excluded, the refund action is a non-repeatable state change, so the design should resolve whether this guardrail applies and how it is satisfied or waived. | Product Owner / Solution architect | blocker | recorded as blocker |
| INT-4-M3 | `SanjulikaSthirAI/orders-api` | contract | The current published/deployed OpenAPI contract version 1.0.0 has no `POST /orders/{order_id}/refunds` endpoint and the Order schema has no `refunded` or `refundTime`/`refund_time` field. The approved requirements need a new refund action and refund fields in create, read, list, refund success, and cancellation success responses. This is an expected contract gap for the story and requires an additive OpenAPI update plus regenerated contract test. | Orders API team | blocker | recorded as blocker |
| INT-4-M4 | `SanjulikaSthirAI/orders-api` | code | The base-branch code exposes only `GET /orders`, `GET /orders/{order_id}`, `POST /orders`, and `POST /orders/{order_id}/cancel`; it has no refund endpoint or refund state in the known components. This differs from the planned requirements and must be implemented in routes, models, and store while preserving the reference design layering. | Orders API team | blocker | recorded as blocker |
| INT-4-M5 | `SanjulikaSthirAI/orders-api` | code | The existing cancel behavior allows cancellation based on the current cancellability rules only; there is no known base-branch rule preventing cancellation after refund because refund state does not exist. FR-8 requires cancel attempts for refunded orders to return reason `order already refunded`, so the existing cancel path must gain this blocker and expose it in the contract. | Orders API team | blocker | recorded as blocker |
| INT-4-M6 | `SanjulikaSthirAI/orders-api` | deployment | The deployed version and deployed contract are 1.0.0, matching the currently published contract that lacks refund capabilities. After implementation, deployment/versioning must reflect the new additive API surface so consumers are not pointed at a deployed contract that cannot support the approved workflow. | Orders API team / Release owner | blocker | recorded as blocker |
| INT-4-M7 | `SanjulikaSthirAI/orders-ui` | deployment | The UI repo has unknown deployed version and unknown deployed contract version. For a brownfield repo this prevents a complete deployed-vs-base comparison and creates release risk if the UI is expected to consume or display the new refund fields later, even though UI changes are excluded from this intent. | Orders UI team / Release owner | blocker | recorded as blocker |
| INT-4-M8 | `SanjulikaSthirAI/orders-ui` | contract | No API contract is configured for the UI repo, which is acceptable for a browser client but means there is no repo-local contract artifact to compare. Any UI dependency on Orders API must continue to be through the API client module and the Orders API `openapi.yaml`; no UI mismatch with the refund design is otherwise identifiable from the supplied evidence. | Orders UI team | blocker | recorded as blocker |

## Appendix D. Protected contracts

Stories must not change these unless plan.json marks the story as a contract change. Machine-readable copy: `protected-contracts.json`.

| Repo | Files | Endpoints |
| --- | --- | --- |
| `SanjulikaSthirAI/orders-api` | `openapi.yaml` | `GET /orders`, `GET /orders/{order_id}`, `POST /orders`, `POST /orders/{order_id}/cancel`, `POST /orders/{order_id}/refunds` |
| `SanjulikaSthirAI/orders-ui` | `api/**`, `app/**`, `config/**`, `format/**` | - |

## Appendix E. ADRs

_None._

Proposed but not written (an ADR must meet all three tests):

_None._

## Appendix F. Prototypes (throwaway; never used as a starting point at G4)

_None._
