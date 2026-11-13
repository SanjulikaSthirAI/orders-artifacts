# Technical design: Record full order refunds in the Orders API

## 1. Context and scope

Support needs to record eligible full Refunds in the existing `SanjulikaSthirAI/orders-api` instead of tracking them in a spreadsheet. This is a brownfield change to the Orders API only.

The approved scope is to record a full Refund for an Order by order ID, expose the Order as `refunded`, expose the Refund time, enforce the approved eligibility rules, and return stable reason codes with non-empty messages when a Refund is not allowed.

The approved exclusions remain in force: no Orders screen changes, no partial refunds, no new database or persistent store changes, no payment provider integration or movement of money, and no change to how API callers authenticate.

This design cannot be completed into an implementable G2 plan yet because every brownfield mismatch was explicitly recorded as a blocker by the solution architect during design grilling. The sections below therefore state the intended design direction traceable to the approved requirements and guardrails, and identify the blocked points that must be resolved before implementation stories proceed.

## 2. Components and changes

### 2.1 SanjulikaSthirAI/orders-api (brownfield)

Planned changes, blocked pending mismatch resolution:

| Component | Change | Trace |
| --- | --- | --- |
| `app/main.py` routes | Add a state-changing refund endpoint using the guardrail sub-resource shape `POST /orders/{order_id}/refunds`. The route validates the path and request, enforces existing authentication and support authorization checks, calls the store/service, and translates domain outcomes to HTTP responses. | FR-1, FR-3, FR-4, FR-5, FR-6, FR-7, FR-8; BR-10; API standards; reference REST design; INT-3-M4 blocker |
| `app/models.py` | Extend the Order response contract to expose `status: refunded` and `refund_time` after a Refund is recorded. Add a refund-not-allowed response model that can carry a stable reason code and a non-empty human-readable message if the guardrail mismatch on error shape is resolved. | FR-2, FR-3, FR-4, FR-5, FR-6, FR-7; BR-4, BR-14, BR-15; INT-3-M1 and INT-3-M5 blockers |
| `app/store.py` or service layer | Add refund-recording behavior and domain outcomes. The store/service owns eligibility rules: missing Order, duplicate Refund, Cancelled order, 30-day UTC cutoff, and priority ordering of blockers. Routes must not hold the business rules. | FR-1 through FR-8; BR-1 through BR-18; reference REST design; INT-3-M2 and INT-3-M9 blockers |
| App factory / collaborators | Add or reuse injected clock support so Refund time and the 30-day UTC cutoff are deterministic in tests and do not call real time directly. | FR-1, FR-2, FR-5; BR-3, BR-7; engineering standards; reference REST design; INT-3-M8 blocker |
| `openapi.yaml` and contract test | Regenerate the committed OpenAPI contract from code and update the contract test in the same change. The committed `openapi.yaml` remains the source of truth. | FR-1 through FR-8; ADR 0002; API standards; INT-3-M1 blocker |
| Automated tests | Add deterministic tests for every acceptance criterion, including happy path, exact cutoff boundary, unauthorized caller, retrieval after refund, duplicate requests, Cancelled orders, old orders, priority ordering, missing Order, and attempts to submit a partial Refund. | All ACs; engineering standards |
| Deployment/release | Deploy a new version after code and contract changes are approved, because deployed version 1.0.0 has no refund functionality. | NFR-1; INT-3-M3 blocker |

Refund eligibility in the store/service must use the API acceptance time as the Refund time, compare Order creation timestamps in UTC against the cutoff exactly 30 days earlier, and allow an Order created exactly at the cutoff. For an existing Order with multiple blockers, the single returned reason priority is: `ORDER_ALREADY_REFUNDED`, then `ORDER_CANCELLED`, then `ORDER_TOO_OLD`.

Repeated refund requests are not successful idempotent replays under the approved requirements; they return `ORDER_ALREADY_REFUNDED` with a non-empty message. This conflicts with the guardrail idempotency rule for operations that move money or cannot be undone and is blocked by INT-3-M6 and INT-3-M7 until resolved.

## 3. API contract changes

The intended contract change is additive except for the open question of whether adding `refunded` to `OrderStatus` is safe for all consumers. It must be reviewed as an API contract change under the API standards.

| Operation | Change type | Response notes | Trace |
| --- | --- | --- | --- |
| `POST /orders/{order_id}/refunds` | Added | Success returns the updated Order exposed as `refunded` with `refund_time`. Missing Order returns `ORDER_NOT_FOUND`. Ineligible existing Order returns one of `ORDER_ALREADY_REFUNDED`, `ORDER_CANCELLED`, or `ORDER_TOO_OLD`. Authentication and authorization failures use existing Orders API behavior. Validation errors use existing FastAPI validation behavior. | FR-1, FR-3, FR-4, FR-5, FR-6, FR-7, FR-8; API standards; INT-3-M1, M4, M5 blockers |
| `GET /orders/{order_id}` | Changed response shape | Retrieved refunded Orders expose status `refunded` and include `refund_time`. | FR-2; INT-3-M1 blocker |
| `GET /orders` | Changed response shape if it returns refunded Orders | Listed Orders use the same Order model, so refunded Orders expose status `refunded` and include `refund_time`. | FR-2; API contract consistency; INT-3-M1 blocker |
| `POST /orders` | Changed response shape only through shared Order model | New Orders are not refunded and do not have a Refund time. The response model change must remain backward compatible, for example by making `refund_time` nullable or absent for non-refunded Orders, subject to contract review. | FR-2; API standards; INT-3-M1 blocker |
| `POST /orders/{order_id}/cancel` | Changed response shape only through shared Order model | Existing cancellation rules are not changed; any shared Order model change must not add new cancellation restrictions. | FR-2; BR-11; API standards |

No operations are removed.

Contract blockers:

- INT-3-M1: deployed and published contract has no refund endpoint, no `refunded` status, and no Refund time field.
- INT-3-M5: current guardrail error shape is `{"detail":"<message>"}`, but approved requirements require stable reason codes plus non-empty messages.
- INT-3-M6 and INT-3-M7: security/API guardrails may require an idempotency key and queryable audit trail unless the non-money Refund record is explicitly accepted as outside those rules.

## 4. Data changes and migrations

No new database or persistent store is in scope, per BR-18 and the approved exclusions.

The design intent is to record the Refund on the existing Order representation used by the current store, exposing `status: refunded` and the API-generated `refund_time`. Because the project is brownfield and the assessment states no persistent-store change is allowed, any implementation must fit the existing storage mechanism and must not introduce a new database, table, collection, external service, or persistent audit store.

There is no migration planned in this design. If the existing implementation cannot persist `refunded` state and `refund_time` without a store change, that is a scope conflict and must be resolved before implementation.

## 5. Security

Authentication must remain unchanged. The refund endpoint must use the existing Orders API authentication behavior and must not introduce a new authentication mechanism.

Authorization must use the existing appropriate Orders API access for support users and the existing Orders API support authorization marker. A caller who is authenticated but does not have that support access must be rejected and must not cause the Order to be newly refunded.

Data classification: Order data may include customer data. Logs, tests, and error messages must not include customer names, addresses, payment details, secrets, tokens, or real customer data. Refund-not-allowed messages must be useful but must not disclose internal implementation details.

Secrets handling: no new secrets are introduced. Any existing environment-specific configuration continues to come from environment variables.

Threats and mitigations:

| Threat | Mitigation | Trace |
| --- | --- | --- |
| Unauthorized caller records a Refund | Server-side authorization check using the existing support authorization marker before store mutation. | FR-1 AC-1.3; BR-10; security standards |
| Duplicate Refund records | Store/service enforces already-refunded rule before recording. | FR-3; BR-5 |
| Refund for Cancelled or too-old Order | Store/service enforces Cancelled and 30-day UTC cutoff rules. | FR-4, FR-5; BR-6, BR-7 |
| Caller supplies Refund time or partial-refund details | Boundary model does not accept caller-provided Refund time or partial amount; API sets Refund time itself. | FR-2, FR-8; BR-3, BR-9, BR-16 |
| Sensitive data leakage in logs or errors | Log record identifiers and outcome codes only; do not log customer names, contact details, payment data, stack traces, secrets, or real customer data. | security standards; engineering standards |

Security blocker: INT-3-M6 and INT-3-M7 must be resolved by the security specialist and solution architect before implementation, because guardrails treat money-moving or non-undoable refund-like operations as requiring a distinct authorization rule, audit trail, and idempotency key, while approved requirements define this Refund as a non-money record using existing support authorization and duplicate-request rejection.

## 6. Observability

Log each refund-recording attempt with the Order ID, authenticated actor identifier if already available under existing Orders API logging practices, outcome category, stable reason code for not-allowed outcomes, and Refund time for successful outcomes. Logs must exclude customer names, contact details, payment details, secrets, and real customer data.

Expose no new metrics unless the Orders API already has a standard application metrics mechanism. If such a mechanism exists, count successful Refund recordings and not-allowed outcomes by reason code. Do not introduce a new observability backend as part of this scope.

The requirement for a queryable audit trail is blocked by INT-3-M7 because approved requirements exclude new persistent-store changes and do not approve a new audit store.

## 7. Non-functional requirements

NFR-1 is satisfied only after the refund endpoint is implemented, the contract is published, and a new version is deployed: a support user with the existing appropriate Orders API access can complete an eligible refund-recording workflow through the Orders API without using the spreadsheet.

Measurable target: for an eligible Order, a support user can complete the workflow with one authenticated `POST /orders/{order_id}/refunds` call that returns a 2xx response containing the updated Order with `status = refunded` and non-null `refund_time`, without any spreadsheet step.

Engineering targets:

- Every acceptance criterion has at least one automated test named for the AC it covers.
- Time-dependent tests use an injected clock and do not depend on real time.
- The OpenAPI contract test passes after `openapi.yaml` is regenerated from code.
- CI lint and tests pass for `SanjulikaSthirAI/orders-api`.

## 8. Alternatives considered

| Alternative | Decision | Reason | Trace |
| --- | --- | --- | --- |
| Keep spreadsheet tracking and add no API capability | Rejected | Does not meet the approved business outcome or FR-1. | Business outcome; FR-1 |
| Add UI changes to the Orders screen | Rejected | Explicitly excluded from scope. | Approved exclusions |
| Record partial refunds | Rejected | Explicitly excluded and prohibited by BR-16 and FR-8. | FR-8; BR-16 |
| Integrate with a payment provider or move money | Rejected | Explicitly excluded and prohibited by BR-1 and BR-17. | BR-1; BR-17 |
| Add a new persistent store or audit store | Rejected for this scope | Explicitly excluded by BR-18; also blocked by INT-3-M7 if required by guardrails. | BR-18; INT-3-M7 |
| Use `POST /orders/{order_id}/refunds` | Intended design, blocked | Matches API standards for state-changing actions as sub-resources. | FR-1; API standards; INT-3-M4 |
| Use an idempotency key with first-result replay | Not selected in approved requirements | Approved requirements say repeated refund attempts return `ORDER_ALREADY_REFUNDED`, not success replay; guardrail conflict is blocked. | FR-3 AC-3.2; INT-3-M6, M7 |

## 9. Decisions

The following decisions are traceable to approved requirements and guardrails but remain blocked where noted:

1. Refund recording is represented as `POST /orders/{order_id}/refunds`, following the API standards for state-changing sub-resources. Blocked by INT-3-M1 and INT-3-M4 until the contract change is approved.
2. Successful refund recording returns the updated Order with `status: refunded` and `refund_time`; subsequent retrieval exposes the same. Blocked by INT-3-M1 until the Order contract change is approved.
3. Refund business rules live in the store/service layer, not the route. Blocked by INT-3-M2 and INT-3-M9 until implemented.
4. Refund time and the 30-day cutoff use an injected UTC clock. Blocked by INT-3-M8 until the implementation supports clock injection.
5. Not-allowed outcomes use stable reason codes exactly `ORDER_ALREADY_REFUNDED`, `ORDER_CANCELLED`, `ORDER_TOO_OLD`, and `ORDER_NOT_FOUND`, with non-empty human-readable messages. Blocked by INT-3-M5 until the error schema mismatch is resolved.
6. No payment movement, no partial refunds, no new authentication mechanism, and no new persistent store are part of this design. Blocked by INT-3-M6 and INT-3-M7 where security/API guardrails require idempotency or audit treatment for refund-like operations.

No existing guardrail ADR is intentionally contradicted by this design. ADR 0002 is followed by treating committed generated `openapi.yaml` as the contract. No new ADR is proposed until the blockers on error shape, idempotency, and audit treatment are resolved, because the final hard-to-reverse decision has not yet been made.

## Appendix A. Requirement coverage

| Requirement | Section | How |
| --- | --- | --- |
| FR-1 | 2.1 | The design adds `POST /orders/{order_id}/refunds`, existing support authorization, store/service eligibility checks, and an updated Order response, but implementation is blocked by recorded brownfield mismatches. |
| FR-2 | 3 | The design changes the Order response contract so successful refund recording and later retrieval expose `status: refunded` and `refund_time`. |
| FR-3 | 2.1 | The store/service applies the already-refunded rule before recording and returns `ORDER_ALREADY_REFUNDED` for duplicate attempts. |
| FR-4 | 2.1 | The store/service rejects Cancelled orders and maps that domain outcome to `ORDER_CANCELLED`. |
| FR-5 | 2.1 | The store/service compares Order creation time in UTC against an injected-clock cutoff exactly 30 days before the Refund time. |
| FR-6 | 2.1 | The design fixes the priority order for multiple blockers as already refunded, then Cancelled, then too old. |
| FR-7 | 3 | The refund endpoint declares a distinct missing-Order outcome with reason code `ORDER_NOT_FOUND` and a non-empty message. |
| FR-8 | 3 | The refund-recording API accepts no partial amount and rejects attempts to record less than a full Refund without recording a partial Refund. |

## Appendix B. NFR targets

| NFR | Requirement | Target |
| --- | --- | --- |
| NFR-1 | For an Order with an Eligible refund, a support user with the existing appropriate Orders API access can complete the refund-recording workflow through the Orders API without entering the Refund in the spreadsheet. | 1 authenticated `POST /orders/{order_id}/refunds` call returns a 2xx updated Order with `status = refunded` and non-null `refund_time`; 0 spreadsheet steps. |

## Appendix C. Brownfield mismatches

| ID | Repo | Kind | Detail | Owner | Status | Resolution |
| --- | --- | --- | --- | --- | --- | --- |
| INT-3-M1 | `SanjulikaSthirAI/orders-api` | contract | The approved refund design requires recording a full refund by order ID and exposing refunded state plus refund time, but the published OpenAPI contract/deployed contract 1.0.0 has no `POST /orders/{order_id}/refunds` endpoint, no `refunded` status in `OrderStatus`, and no refund time field on `Order`. This is an expected required contract change for the design, but it must be added to `openapi.yaml` and reviewed as an API contract change. | Orders API team / Product Owner | blocker | recorded as blocker |
| INT-3-M2 | `SanjulikaSthirAI/orders-api` | code | The base-branch code endpoints are `GET /orders`, `GET /orders/{order_id}`, `POST /orders`, and `POST /orders/{order_id}/cancel`; there is no implemented refund-recording behavior, eligibility rule, duplicate-refund prevention, cancelled-order refund prevention, 30-day UTC cutoff rule, reason-code priority, or missing-order refund outcome. The code therefore does not yet satisfy the approved requirements. | Orders API team | blocker | recorded as blocker |
| INT-3-M3 | `SanjulikaSthirAI/orders-api` | deployment | The deployed version is 1.0.0 and matches the deployed contract version 1.0.0, which lacks refund functionality. Support cannot record refunds through the deployed Orders API until a new version containing the refund endpoint, refunded exposure, and error outcomes is deployed. | Orders API team / Release owner | blocker | recorded as blocker |
| INT-3-M4 | `SanjulikaSthirAI/orders-api` | guardrail | Guardrails require state-changing non-plain updates to use sub-resources/actions such as `POST /orders/{order_id}/refunds`; the current contract only has cancellation as `POST /orders/{order_id}/cancel` and no refund sub-resource. The planned design should follow the sub-resource pattern and declare every non-2xx response, including 404, 409, 422, 401/403 as applicable. | Orders API team / Solution architect | blocker | recorded as blocker |
| INT-3-M5 | `SanjulikaSthirAI/orders-api` | guardrail | API standards define error bodies as `{"detail":"<message>"}`, but requirements require stable reason codes plus non-empty human-readable messages for refund-not-allowed outcomes. The current shared `Error` schema only has `detail` and cannot carry a stable reason code. This is a mismatch between the guardrail error shape/current contract and the approved refund requirements, requiring an approved additive error schema or explicit design decision. | Solution architect / Orders API team | blocker | recorded as blocker |
| INT-3-M6 | `SanjulikaSthirAI/orders-api` | guardrail | Security standards say anything that moves money, including refunds, is high risk and needs its own authorization rule, audit trail, and idempotency key. The approved requirements explicitly say a Refund record does not move money and must use the existing Orders API support authorization marker without changing authentication, and repeated refund requests should return `ORDER_ALREADY_REFUNDED` rather than idempotent first-result replay. This must be resolved/recorded so reviewers know whether this refund record is treated outside the 'moves money' high-risk rule. | Security specialist / Product Owner / Solution architect | blocker | recorded as blocker |
| INT-3-M7 | `SanjulikaSthirAI/orders-api` | guardrail | API standards require operations that move money or cannot be undone to be idempotent with an idempotency key and to record who did what and when in a queryable form. Requirements exclude payment movement and new persistent-store changes, but recording a refund appears not undoable and must expose when it happened. The design must resolve whether no idempotency key and no new persistent/audit store is acceptable for this non-money refund record. | Solution architect / Security specialist | blocker | recorded as blocker |
| INT-3-M8 | `SanjulikaSthirAI/orders-api` | guardrail | Reference design says rules depending on dates take the clock as a parameter and nothing calls `datetime.now()` directly. Requirements need the Orders API to set refund time at acceptance and compare UTC cutoff exactly 30 days earlier. The existing contract/code summary does not show an injected clock for refund behavior, so the implementation plan must add clock injection rather than using real time directly. | Orders API team | blocker | recorded as blocker |
| INT-3-M9 | `SanjulikaSthirAI/orders-api` | guardrail | Reference design says routes parse/validate input and translate domain exceptions, while store/service owns business rules and knows nothing about HTTP. The refund requirements add several domain rules and priority ordering; these must be implemented in the store/service layer, not only in the route. Current components include `main`, `models`, and `store`, but no refund store API is present. | Orders API team | blocker | recorded as blocker |

## Appendix D. Protected contracts

Stories must not change these unless plan.json marks the story as a contract change. Machine-readable copy: `protected-contracts.json`.

| Repo | Files | Endpoints |
| --- | --- | --- |
| `SanjulikaSthirAI/orders-api` | `openapi.yaml` | `GET /orders`, `GET /orders/{order_id}`, `POST /orders`, `POST /orders/{order_id}/cancel` |

## Appendix E. ADRs

_None._

Proposed but not written (an ADR must meet all three tests):

_None._

## Appendix F. Prototypes (throwaway; never used as a starting point at G4)

_None._
