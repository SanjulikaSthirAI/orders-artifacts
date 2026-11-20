# Technical design: Support agents can process eligible order refunds

## 1. Context and scope

This brownfield design adds full-order Refund processing to the existing orders system so Support agents with refund permission can process eligible Refund requests from the orders screen. The design covers `SanjulikaSthirAI/orders-api` and `SanjulikaSthirAI/orders-ui`.

In scope, traced to the approved requirements, is: displaying Refund availability and ineligibility reasons on the orders screen; requiring confirmation before issuing a Full-order refund; issuing a successful Full-order refund for an eligible Order; preventing duplicate Refunds; preserving the Order unchanged when a Refund attempt fails; and recording successful Refund history internally without showing that audit/history record on the orders screen.

Out of scope per the approved intent and requirements: refund reporting, Partial refunds, customer self-service refunds, Refunds for Orders older than 30 days, requiring Support agents to enter a Refund reason, and displaying the internal audit/history record on the orders screen.

The assessment initially recorded blockers for missing API refund capability, missing refunded Order representation, existing customer-name exposure, and cross-repo release sequencing. Per the solution architect answers Q9-Q20, these are resolved by an API-first implementation, additive contract updates, server-side authorization and idempotency, explicit customer-data handling constraints, UI consumption of the committed API contract, and release sequencing where `orders-api` is deployed and verified before `orders-ui` exposes the Refund action.

## 2. Components and changes

### 2.1 SanjulikaSthirAI/orders-api (brownfield)

`orders-api` remains a Python 3.12 FastAPI service following the accepted service guardrails and the existing REST reference design. The implementation adds Refund behavior through the existing route/model/store layering: routes validate HTTP input and translate domain failures to HTTP responses; models define the OpenAPI contract; the store/service owns eligibility, idempotency, state transition, and audit rules.

Changes:

- Add `POST /orders/{order_id}/refunds` as the money-moving operation for Full-order refunds. The route requires authentication, checks the distinct `orders:refund` authorization capability on the server, requires an `Idempotency-Key` header, and returns the updated `Order` on success.
- Extend the `OrderStatus` enum with `refunded`. This is additive under the API compatibility guardrail.
- Extend the `Order` response with nullable `refunded_amount_cents`, nullable `refunded_at`, and nullable `refund_unavailable_reason`.
- Compute Refund eligibility server-side using the Order creation timestamp, the standard order-service clock, current paid status, and existing refunded state. For authorized Support agents, `refund_unavailable_reason` uses stable values for `not_paid`, `older_than_30_days`, and `already_refunded`; eligible Orders have no unavailable reason. The UI renders this value rather than reimplementing business rules.
- Keep the existing `Order` shape, including `customer_name`, for backward compatibility. The Refund path must not add customer names, payment details, or other customer details to audit records, idempotency records, logs, errors, or UI Refund messages.
- Add a `RefundProcessor` collaborator injected into the app/store boundary. The store/service verifies eligibility and idempotency before calling the processor for exactly the Order `total_cents`; it persists refunded state, refund fields, idempotency result, and the successful Refund audit/history record only after processor success.
- Add in-memory Refund state, idempotency replay records, and successful-refund audit/history records behind the current store abstraction for this story. Durable persistence is not introduced in this design.
- On a successful Refund, mark the Order `status` as `refunded`, set `refunded_amount_cents` to the exact full paid Order total in cents, set `refunded_at` using the injected order-service clock in UTC ISO 8601 form, store the processor reference when available, and create the internal audit/history record with Support agent, Order ID, refunded amount, Refund date/time, and processor reference when available.
- Repeated `POST /orders/{order_id}/refunds` with the same `Idempotency-Key` replays the original successful updated `Order` and does not call the Refund processor again. A different or new key after the Order has already been refunded returns `409` with `{"detail":"Order has already been refunded"}` and does not call the processor.
- If the processor fails, leave the Order unchanged, create no successful Refund audit/history record, and return `503` with `{"detail":"The refund could not be completed. Please try again."}`.
- Update paid-Order fulfillment and customer-facing paid-Order action guards so an Order with `status: refunded` cannot proceed through those paid-Order actions. Existing cancel behavior and existing non-refund endpoints are protected except for additive `Order` fields and the new enum value.
- Regenerate and commit `openapi.yaml` from the FastAPI code and update the contract test so code and contract cannot drift.
- Add deterministic tests for every acceptance criterion. Tests inject clock and Refund processor behavior and cover eligibility, authorization, confirmation-driven API use, idempotency replay, duplicate-prevention with different keys, processor failure, audit/history content, and contract generation.

### 2.2 SanjulikaSthirAI/orders-ui (brownfield)

`orders-ui` remains a browser UI using plain HTML and ES modules, with no framework and no build step. It consumes `orders-api/openapi.yaml` through its API client module and must not call refund routes outside that client.

Changes:

- Consume the committed `orders-api/openapi.yaml` after the API adds `POST /orders/{order_id}/refunds`, `status: refunded`, `refunded_amount_cents`, `refunded_at`, and `refund_unavailable_reason`.
- On the orders screen, show the Refund action only when the current Support agent has the `orders:refund` capability. Agents without that capability do not see the Refund action.
- For authorized Support agents, render Refund availability from API-provided Order state and `refund_unavailable_reason`. When unavailable, show a specific reason for not paid, older than 30 days, or already refunded states.
- When an eligible authorized Support agent selects Refund, show a confirmation stating that the full paid Order total will be refunded. The confirmation does not require a Refund reason.
- If the confirmation is cancelled or closed, issue no API request and leave the Order unchanged.
- On confirmation submission, generate one `Idempotency-Key` for that confirmed attempt, disable the submit button while the request is in flight, call `POST /orders/{order_id}/refunds` through the API client, and reuse the same key for retries of the same confirmed attempt.
- On success, refresh or update the Order display to show refunded status, refunded amount, and Refund date/time, and show a message that the Refund completed and that the full paid Order total was refunded.
- On failure from the refund endpoint, show exactly: “The refund could not be completed. Please try again.” The UI must not expose internal audit/history records, processor details, stack traces, customer names, payment details, or raw database errors in Refund messages.
- Use `textContent` for API-provided data and keep tests deterministic.

## 3. API contract changes

All API changes are in `SanjulikaSthirAI/orders-api` and are additive, except for the new behavior of existing paid-Order action guards rejecting `refunded` Orders as ineligible.

| Operation or schema | Change type | Contract change | Trace |
| --- | --- | --- | --- |
| `POST /orders/{order_id}/refunds` | Added | New refund action endpoint requiring `Idempotency-Key`; returns updated `Order`; declares `401`, `403`, `404`, `409`, `422`, and `503`. | FR-2, FR-3, FR-4, FR-5, FR-6; API and security guardrails; Q9, Q11-Q13, Q18 |
| `OrderStatus` | Added enum value | Add `refunded`. | FR-3, FR-4; API guardrail; Q10 |
| `Order` | Added optional fields | Add nullable `refunded_amount_cents`, nullable `refunded_at`, nullable `refund_unavailable_reason`. | FR-1, FR-3; API standards; Q10, Q19 |
| Existing `GET /orders` and `GET /orders/{order_id}` responses | Changed additively | Existing `Order` response includes the new nullable fields and new enum value. | FR-1, FR-3; Q10, Q19 |
| Existing paid-Order actions, including `POST /orders/{order_id}/cancel` where applicable | Behavior constrained | A `refunded` Order is no longer eligible for paid-Order actions. Existing response shape is protected. | FR-3; BR-7 |

The committed `openapi.yaml` remains the source of truth and must be regenerated from code in the same change as the route/model changes.

## 4. Data changes and migrations

The first implementation uses the current in-memory store abstraction. It adds in-memory representations for:

- refunded Order state: `status: refunded`, `refunded_amount_cents`, and `refunded_at`;
- idempotency replay records keyed by Order and `Idempotency-Key`, storing the first successful result for replay;
- successful Refund audit/history records containing Support agent, Order ID, refunded amount, Refund date/time, and processor reference when available.

No durable database migration is included because the solution architect directed that this story keep the existing in-memory store shape. If production requires durable Refund, idempotency, or audit persistence, that must be handled as a separate follow-up design/story. Processor failures must not create successful Refund audit/history records and must not mutate Order state.

All timestamps use the injected standard order-service clock. Money remains integer minor units as `*_cents`; no floating-point money is introduced.

## 5. Security

Refunds move money and are treated as high risk under the security standards.

- Authentication: `POST /orders/{order_id}/refunds` requires an authenticated caller. Unauthenticated requests return `401`.
- Authorization: the API checks the distinct server-side `orders:refund` capability. Missing permission returns `403`. UI button visibility is convenience only and is not the authorization boundary.
- Idempotency: the endpoint requires an `Idempotency-Key` header. Missing or invalid keys return `422`. The same key replays the first successful result; a different/new key after a Refund returns `409` and does not call the processor.
- Data classification: customer names and contact details are personal data; payment details and processor internals are sensitive. The existing `customer_name` field remains for compatibility, but the Refund path must not add customer names, payment details, or customer details to audit records, idempotency records, logs, errors, tests using real data, or UI Refund messages.
- Audit/history: successful Refunds are recorded internally with Support agent, Order ID, amount, Refund timestamp, and processor reference when available. Support agent notes are not recorded for this version.
- Secrets: Refund processor credentials, if configured, come from environment variables and are not stored in the repository, tests, fixtures, logs, or browser code.
- Input/output validation: FastAPI/Pydantic validates route parameters and headers; UI uses `textContent` for API-provided data. Error responses use `{"detail":"..."}` and do not expose stack traces or database errors.
- Threat mitigations: unauthorized Refunds are mitigated by server-side `orders:refund`; duplicate Refunds by idempotency records and refunded-state checks; processor partial failure by only persisting state and audit after processor success; accidental disclosure by excluding customer/payment details from Refund-specific logs, audit, idempotency, errors, and UI messages.

## 6. Observability

`orders-api` logs Refund attempts at outcome level using non-sensitive identifiers only: Order ID, Support agent identifier, outcome, status code, and whether the result was an idempotency replay. Logs must not include customer names, addresses, payment details, processor secrets, or raw processor/database errors.

The API should expose enough operational evidence through existing service logging and tests to distinguish successful Refunds, authorization failures, ineligible-state rejections, duplicate attempts with different keys, idempotency replays, and processor failures. The UI should surface only the approved Support-agent messages and should not log customer/payment details for Refund operations.

## 7. Non-functional requirements

NFR targets are listed in the structured NFR section. The design additionally requires automated tests for each acceptance criterion, deterministic injected clocks, no real network dependency in tests, and contract-test coverage for the regenerated OpenAPI file.

The business success measure is a 50% reduction in average handling time for refund requests, but the approved requirements keep the baseline period and measurement method as a non-blocking open question. This design provides the technical path to measure completion outcomes but does not invent the business measurement method.

## 8. Alternatives considered

- Add Refund as a generic Order update: rejected because Refund is a money-moving, not-plain-update action. API standards call for state-changing actions as sub-resources or actions, and security standards require idempotency and audit.
- Let the UI compute eligibility locally: rejected because authorization and business eligibility must be decided server-side; the UI only renders API-provided state and reasons.
- Hide all ineligible Refund actions without reasons: rejected because FR-1 requires authorized Support agents to see specific reasons for ineligible Orders.
- Require a Refund reason in the confirmation: rejected because BR-11 and FR-2 state no Refund reason is required in this version.
- Durable persistence for Refund, audit, and idempotency records in this story: deferred by solution architect answer Q15 to keep the existing in-memory store abstraction for this implementation.
- Remove `customer_name` from the existing `Order` contract: rejected for this design because Q17 directs compatibility; Refund-specific paths instead exclude customer details from logs, audit, idempotency, errors, and UI messages.

## 9. Decisions

- Use `POST /orders/{order_id}/refunds` with required `Idempotency-Key`, server-side `orders:refund`, and internal successful-refund audit/history records. This follows the API and security guardrails for money-moving operations.
- Represent successful Refunds with `status: refunded`, nullable `refunded_amount_cents`, nullable `refunded_at`, and an updated `Order` response.
- Enforce idempotency so the same key replays the original successful result and a different/new key after Refund returns `409` without another processor call.
- Inject a `RefundProcessor`, verify eligibility/idempotency before calling it, and persist refunded state, idempotency result, and audit only after processor success.
- Release `orders-api` first, regenerate and commit its OpenAPI contract, deploy and verify it, then release `orders-ui` consuming that committed contract through its API client module.
- Keep the existing `Order.customer_name` field for compatibility while prohibiting Refund-specific customer/payment details in audit, idempotency, logs, errors, and UI messages.

No new ADR is proposed: the choices follow existing accepted guardrails and solution architect answers, and none simultaneously requires a hard-to-reverse, surprising, real-tradeoff record beyond this design.

## Appendix A. Requirement coverage

| Requirement | Section | How |
| --- | --- | --- |
| FR-1 | 2.1, 2.2, 3 | The API computes eligibility and `refund_unavailable_reason` server-side for authorized agents, while the UI shows or hides the Refund action based on `orders:refund` and renders the specific API-provided reason. |
| FR-2 | 2.2, 3 | The UI requires a confirmation before calling `POST /orders/{order_id}/refunds`, shows the full paid Order total, issues no request on cancel, and does not require a Refund reason. |
| FR-3 | 2.1, 2.2, 3, 4 | A successful endpoint call marks the Order as `refunded`, sets amount and timestamp fields, blocks further paid-Order actions, and the UI displays the refunded status, amount, date/time, and success message. |
| FR-4 | 2.1, 2.2, 3 | The API enforces idempotency by replaying the first successful result for the same key and returning `409` for a new key after refund, while the UI reuses one key per confirmed attempt. |
| FR-5 | 2.1, 2.2, 3, 4 | Processor failure returns `503` with the required message, leaves the Order unchanged, records no successful Refund history, and the UI displays the required failure text. |
| FR-6 | 2.1, 4, 5 | The API creates an internal successful Refund audit/history record with the required fields and excludes notes, while the UI does not display the audit/history record. |

## Appendix B. NFR targets

| NFR | Requirement | Target |
| --- | --- | --- |
| NFR-1 | Refund API latency for Support-agent workflow | p95 < 500 ms for `POST /orders/{order_id}/refunds` excluding external processor time at 20 requests/minute in test environment. |
| NFR-2 | Orders screen refund-state rendering performance | p95 < 300 ms to render Refund availability from an already completed `GET /orders` or `GET /orders/{order_id}` response containing up to 100 Orders in a supported browser. |
| NFR-3 | Duplicate Refund prevention | 0 duplicate processor Refund calls for 1,000 repeated submissions using the same `Idempotency-Key` in automated tests. |
| NFR-4 | Contract consistency | 100% of API contract tests pass and generated `openapi.yaml` has no diff from FastAPI-generated output in CI. |
| NFR-5 | Automated acceptance coverage | 100% of acceptance criteria AC-1.1 through AC-6.4 have at least one deterministic automated test with the AC identifier in the test name. |
| NFR-6 | Sensitive data exclusion for Refund path | 0 occurrences of customer names, addresses, payment details, processor secrets, or raw processor/database errors in Refund audit records, idempotency records, error responses, UI Refund messages, and Refund logs in automated security tests. |

## Appendix C. Brownfield mismatches

| ID | Repo | Kind | Detail | Owner | Status | Resolution |
| --- | --- | --- | --- | --- | --- | --- |
| INT-5-M1 | `SanjulikaSthirAI/orders-api` | code | The current code/contract/deployed API has no refund capability: endpoints are GET /orders, GET /orders/{order_id}, POST /orders, and POST /orders/{order_id}/cancel only. The approved design needs a money-moving refund operation, likely POST /orders/{order_id}/refunds, plus order fields/status for refunded state, refunded amount, and refund date/time. This matters because the UI cannot implement refund processing until the API contract and code add the operation and response shape. | orders-api team | blocker | recorded as blocker |
| INT-5-M2 | `SanjulikaSthirAI/orders-api` | contract | OrderStatus enum in openapi.yaml is limited to placed, shipped, delivered, and cancelled. Requirements need orders to be marked and shown as refunded. Adding a refunded status is additive as a new enum value under the API standards, but consumers must tolerate it and the contract must be regenerated from code. | orders-api team | blocker | recorded as blocker |
| INT-5-M3 | `SanjulikaSthirAI/orders-api` | contract | The Order schema has no refunded_amount/refunded_amount_cents or refund date/time fields. Requirements AC-3.2 require the orders screen to show refunded status, refunded amount, and Refund date/time. Without these fields in the protected contract, orders-ui cannot display the required information from the API. | orders-api team | blocker | recorded as blocker |
| INT-5-M4 | `SanjulikaSthirAI/orders-api` | guardrail | Refunds move money, and guardrails/security-standards.md plus guardrails/api-standards.md require an idempotency key, a specific server-side authorization rule, and an audit trail. The current contract exposes no refund endpoint, no idempotency-key input/header, and no declared refund authorization behavior. The design must include these before approval because duplicate refunds and unauthorized refunds are high-risk failures. | orders-api team | resolved | handle it yourself |
| INT-5-M5 | `SanjulikaSthirAI/orders-api` | code | The existing API contract exposes customer_name on Order and accepts customer_name in NewOrder. Security standards say return only fields a caller needs and keep customer names out of logs/test fixtures; for this refund design the UI may not need customer data to perform the refund. This is an existing brownfield exposure to be consciously handled so the refund flow does not add logs/errors/audit records containing customer names. | orders-api team | blocker | recorded as blocker |
| INT-5-M6 | `SanjulikaSthirAI/orders-api` | deployment | The deployed contract version is 1.0.0 and contains no refund endpoint or refunded order representation. Any UI design depending on refunds cannot work against the currently deployed API until the API is changed and deployed first, or the UI release is sequenced behind the API deployment. | release owner | blocker | recorded as blocker |
| INT-5-M7 | `SanjulikaSthirAI/orders-ui` | contract | orders-ui has no API contract configured for the repo, while the guardrails say UI clients consume service operations present in the committed service contract and call the service through an API client module. For this design, the UI must depend on orders-api openapi.yaml once the refund endpoint and refunded order fields are added; otherwise the UI could drift from the protected API contract. | orders-ui team | blocker | recorded as blocker |
| INT-5-M8 | `SanjulikaSthirAI/orders-ui` | deployment | orders-ui deployed version and deployed contract version are unknown. This creates release-sequencing risk for a cross-repo refund feature because the UI may expose a Refund action before the deployed orders-api supports it, or may assume fields/status values unavailable in production. | release owner | blocker | recorded as blocker |

## Appendix D. Protected contracts

Stories must not change these unless plan.json marks the story as a contract change. Machine-readable copy: `protected-contracts.json`.

| Repo | Files | Endpoints |
| --- | --- | --- |
| `SanjulikaSthirAI/orders-api` | `app/main.py`, `app/models.py`, `app/store.py`, `openapi.yaml` | `GET /orders`, `GET /orders/{order_id}`, `POST /orders`, `POST /orders/{order_id}/cancel`, `POST /orders/{order_id}/refunds` |
| `SanjulikaSthirAI/orders-ui` | `api/**`, `app/**`, `config/**`, `format/**` | - |

## Appendix E. ADRs

_None._

Proposed but not written (an ADR must meet all three tests):

_None._

## Appendix F. Prototypes (throwaway; never used as a starting point at G4)

_None._
