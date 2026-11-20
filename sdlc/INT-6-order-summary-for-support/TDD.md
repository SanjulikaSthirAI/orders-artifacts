# Technical design: Order summary and customer-filtered Order book

## 1. Context and scope

This intent changes `SanjulikaSthirAI/orders-api` only. `SanjulikaSthirAI/orders-ui` is not changed because the approved scope excludes screen changes and the solution architect confirmed that later UI consumption must be a separate intent after the API contract update is merged.

The API remains a Python 3.12 FastAPI service using Pydantic models, pytest and ruff, in line with guardrail ADR 0001. The committed `openapi.yaml` remains the contract and must be regenerated from code with the existing contract test, in line with guardrail ADR 0002.

The design is additive against the deployed and published `orders-api` contract version 1.0.0:

- add `GET /orders/summary` for a read-only global Order book summary;
- add optional query parameter `customer` to existing `GET /orders`;
- do not remove, rename or change existing response fields or existing endpoint meanings;
- do not add storage, authentication, UI screens, order placement behaviour, or order cancellation behaviour.

Existing security and pagination guardrail mismatches are accepted for this intent by the solution architect: the API currently has no authentication and `GET /orders` is currently unpaginated. This design must not expand that scope. Authentication across the orders API and pagination for the order list are follow-up intents.

## 2. Components and changes

### 2.1 SanjulikaSthirAI/orders-api (brownfield)

`orders-api` keeps the existing reference-service layering:

| Component | Change | Trace |
| --- | --- | --- |
| `app/models.py` | Add response models for `OrderBookSummary` and `OrderStatusCounts`. The JSON body is `{"counts": {"placed": int, "shipped": int, "delivered": int, "cancelled": int}, "total_value_cents": int}`. Money remains integer cents. | FR-1, FR-2, FR-3; BR-1 through BR-7; API standards money shape; Q1 |
| `app/store.py` | Add a store-level summary method that scans existing orders and returns counts and the non-cancelled total. It always initializes all four named status buckets to 0; counts only placed, shipped, delivered and cancelled; excludes any other status from counts and total; treats missing or null stored value as 0 for total; includes negative stored values exactly as stored for placed, shipped and delivered. | FR-1, FR-2, FR-3; BR-1 through BR-7; reference design says business rules belong in store; Q1 |
| `app/store.py` | Extend the existing list-orders logic to accept an optional customer filter in addition to the existing status filter. Trim leading/trailing spaces from the supplied `customer` query value. If the trimmed value is empty, apply no customer filter. If non-blank, return only orders whose stored `customer_name` exactly equals the trimmed value with the same casing. Missing or null stored customer names do not match a non-blank customer filter. When both customer and status filters are present, require both predicates to match. | FR-4, FR-5; BR-8 through BR-12; Q2 |
| `app/main.py` | Add `GET /orders/summary` route. The route performs request/response handling only and delegates summary calculation to the store. It returns 200 with the summary model. | FR-1, FR-2, FR-3; reference design routes rule; Q1 |
| `app/main.py` | Add optional `customer` query parameter to existing `GET /orders`, while keeping existing `status` query parameter and response array unchanged. | FR-4, FR-5; Q2; API standards additive compatibility |
| `openapi.yaml` | Regenerate from the FastAPI code and update contract version from 1.0.0 to 1.1.0. The diff must contain only the additive `GET /orders/summary` operation, the additive optional `customer` query parameter on `GET /orders`, and new schemas needed by the summary response. | Guardrail ADR 0002; Q1, Q2, Q3 |
| Tests | Add automated tests named for the relevant acceptance criteria. Cover summary counts, zero summary for no orders, global summary unaffected by list filters, non-cancelled total rules, unknown status exclusion if representable in the store, missing/null and negative stored values if representable in the store, trimmed exact case-sensitive customer filtering, blank customer filter preserving unfiltered behaviour, missing/null customer names, and combination with status filter. Update contract tests with the regenerated OpenAPI file. | Engineering standards tests; all ACs; Q1, Q2 |

No `orders-ui` files are changed. The UI currently has no API contract configured and this design does not rely on its deployed version.

## 3. API contract changes

Contract version changes from `1.0.0` to `1.1.0` for `SanjulikaSthirAI/orders-api`.

| Operation | Change type | Contract change | Trace |
| --- | --- | --- | --- |
| `GET /orders/summary` | Added | New read-only operation returning `OrderBookSummary`. Status 200 returns counts and `total_value_cents`. | FR-1, FR-2, FR-3; Q1 |
| `GET /orders` | Changed additively | Add optional query parameter `customer` of type string. Existing optional `status` parameter and array-of-`Order` 200 response remain. | FR-4, FR-5; Q2 |
| `GET /orders/{order_id}` | Unchanged | Protected. | Exclusion: no changes to existing endpoints or fields |
| `POST /orders` | Unchanged | Protected. | Exclusion: no changes to order placement |
| `POST /orders/{order_id}/cancel` | Unchanged | Protected. | Exclusion: no changes to order cancellation |

`GET /orders/summary` response body:

```json
{
  "counts": {
    "placed": 0,
    "shipped": 0,
    "delivered": 0,
    "cancelled": 0
  },
  "total_value_cents": 0
}
```

The summary endpoint accepts no customer or status filters. Its result is always global across all existing orders.

## 4. Data changes and migrations

No new storage, persistence mechanism, migration, table, collection, or record type is added. The summary is computed from the existing in-memory order store, as confirmed by the solution architect.

The customer filter uses the existing stored customer name on each order. The non-cancelled total uses the existing stored order value in cents. No stored data is rewritten or normalized.

## 5. Security

Authentication and authorization are unchanged because the approved scope excludes authentication changes and the solution architect accepted the existing gap for this intent.

Security handling for this design:

- `GET /orders/summary` returns aggregate counts and a total value only; it does not return customer names, order IDs, addresses, payment details, or item details.
- `GET /orders?customer=...` narrows the existing `GET /orders` response and does not add fields to the response.
- Customer names are personal data under the security standards. The implementation must not log the supplied `customer` query value, stored customer names, or returned customer names beyond the existing response body.
- Query parameters are validated at the FastAPI/Pydantic boundary. The optional `customer` value is a string query parameter; trimming and blank handling are performed before store filtering.
- No new secrets, dependencies, or environment configuration are introduced.
- The accepted risk is that existing order-reading endpoints have no declared authentication or authorization. A follow-up intent is needed for authentication and authorization across the orders API.

## 6. Observability

No new customer-data logging is added. If request logging is already present, it must not be expanded to include customer filter values.

Useful operational signals for this change are limited to existing HTTP request metrics and error logs without personal data. The new endpoint and the changed list endpoint should be distinguishable by route in existing access metrics if such metrics are already collected.

Contract drift remains observable through the existing OpenAPI contract test required by guardrail ADR 0002.

## 7. Non-functional requirements

The implementation must meet the measurable targets in the structured NFR list. The key design constraints are:

- contract compatibility: only additive contract changes relative to version 1.0.0;
- deterministic behaviour: summary and filtering tests do not depend on wall-clock time, network, or random ordering;
- privacy: customer names are not added to logs or error messages;
- maintainability: rules live in the store and HTTP handling stays in routes, following the REST service reference design.

The existing unpaginated `GET /orders` endpoint remains unpaginated for this intent because the solution architect accepted the current demo-store limitation and customer filtering only reduces the returned set. Pagination is a follow-up intent.

## 8. Alternatives considered

| Alternative | Decision | Reason |
| --- | --- | --- |
| Add summary fields to `GET /orders` | Rejected | The approved scope requires no changes to existing fields and the solution architect selected a new read-only endpoint. |
| Apply `customer` or `status` filters to the summary | Rejected | FR-1 and BR-1 require a global summary across all existing orders, and AC-1.3 says list filters do not apply. |
| Use a path such as `/order-summary` | Rejected | API standards prefer plural resource paths under the resource area; `/orders/summary` was selected by the solution architect. |
| Add new storage for precomputed counts | Rejected | Approved exclusions say no new storage, and the solution architect confirmed computation from the existing in-memory store. |
| Add authentication in this intent | Rejected for this intent | Approved exclusions say no authentication changes, and the solution architect accepted the existing gap with a follow-up intent. |
| Add pagination to `GET /orders` now | Rejected for this intent | The solution architect accepted the existing unpaginated list for the demo store and identified pagination as a separate follow-up intent. |

## 9. Decisions

No new ADR is proposed. The design follows existing accepted guardrail ADRs for Python/FastAPI and committed OpenAPI contracts. The selected API changes are additive and conventional for this service, and the accepted security and pagination gaps are scope decisions for this intent rather than hard-to-reverse architectural choices.

The implementation must not contradict guardrail ADR 0001 or ADR 0002. Any contract-breaking change discovered during implementation would require solution architect approval, a version plan, and an ADR under the API standards.

## Appendix A. Requirement coverage

| Requirement | Section | How |
| --- | --- | --- |
| FR-1 | 2.1 | Adds `GET /orders/summary` as a read-only additive API capability returning a global summary with zero-filled counts and total. |
| FR-2 | 2.1 | Store summary logic initializes and reports placed, shipped, delivered and cancelled counts while excluding any other status. |
| FR-3 | 2.1 | Store summary logic sums stored `total_cents` for placed, shipped and delivered orders, excludes cancelled and unknown statuses, and handles null and negative values as required. |
| FR-4 | 2.1 | Extends `GET /orders` with optional `customer` filtering using trimmed, exact, case-sensitive matching while preserving behaviour when absent or blank. |
| FR-5 | 2.1 | List-orders logic applies both the optional customer predicate and existing status predicate when both filters are supplied. |

## Appendix B. NFR targets

| NFR | Requirement | Target |
| --- | --- | --- |
| NFR-1 | API contract compatibility | 0 removed or renamed paths, parameters, response fields, schemas, enum values, or status codes relative to orders-api openapi.yaml version 1.0.0. |
| NFR-2 | Automated acceptance coverage | 100% of approved acceptance criteria AC-1.1 through AC-5.3 have at least 1 deterministic automated test named with the AC id. |
| NFR-3 | Contract generation consistency | 1 committed openapi.yaml generated from code, with contract test passing in CI for 100% of changed API operations. |
| NFR-4 | Customer data logging | 0 new log statements include customer query values, stored customer names, addresses, payment details, or item details. |

## Appendix C. Brownfield mismatches

| ID | Repo | Kind | Detail | Owner | Status | Resolution |
| --- | --- | --- | --- | --- | --- | --- |
| INT-6-M1 | `SanjulikaSthirAI/orders-api` | contract | Planned capability requires a new read-only Order book summary API, but the published/deployed contract version 1.0.0 exposes only GET /orders, GET /orders/{order_id}, POST /orders, and POST /orders/{order_id}/cancel. There is no summary endpoint or response model for counts by status and non-cancelled total value, so API consumers cannot build against the planned capability yet. | orders-api code owners / Product Owner | resolved | Resolved in this design: add GET /orders/summary to the orders-api contract as an additive change (contract version 1.0.0 -&gt; 1.1.0). Response: {“counts”: {“placed”: int, “shipped”: int, “delivered”: int, “cancelled”: int}, “total_value_cents”: int}, where total_value_cents is the sum of total_cents of all orders that are not cancelled. With no orders every count and the total are 0. It is computed from the existing in-memory store; no new storage. Testable with the existing test client: create orders with POST /orders, cancel one with POST /orders/{id}/cancel, then call the summary. |
| INT-6-M2 | `SanjulikaSthirAI/orders-api` | contract | Planned customer-name filtering for returned Orders requires a query parameter on the existing order list, but contract 1.0.0 for GET /orders only declares optional status. The contract must add an optional customer-name filter without breaking the existing status filter behavior. | orders-api code owners | resolved | Resolved in this design: add an optional query parameter `customer` (string) to GET /orders as an additive change in contract 1.1.0. Matching follows the approved requirements in curated_requirement.md (the value is trimmed and compared exactly with customer_name; a blank value and a missing value both mean no customer filter). It combines with the existing `status` filter (both must match). Without `customer`, GET /orders behaves exactly as today. No other endpoint or field changes. |
| INT-6-M3 | `SanjulikaSthirAI/orders-api` | deployment | The deployed contract is version 1.0.0 and matches the current published contract that lacks the planned summary endpoint and customer filter. Until a new deployed version exists, production will not support the approved requirements. | orders-api deploy/release owner | resolved | Not a blocker: this is expected for new work. The changes ship as contract version 1.1.0 through the normal G4 flow (feature branch, CI, merge to develop). Nothing changes in production until that release. |
| INT-6-M4 | `SanjulikaSthirAI/orders-api` | guardrail | Security standards say every endpoint that returns customer data requires authentication and authorization against the caller's rights to that record. The current contract and endpoint inventory show order-reading endpoints returning customer_name with no authentication/authorization scheme declared. The new summary/list capabilities must resolve this existing security gap or document approved handling, because they expose order/customer data to Support leads. | Security specialist / solution architect | resolved | Accepted existing gap, out of scope for this intent: the orders API has no authentication today for any endpoint, and this intent must not add authentication. The new summary returns only counts and a total (no customer data), and the customer filter only narrows the existing GET /orders, so neither adds new exposure. Record it as an accepted risk with a follow-up intent for authentication across the orders API. |
| INT-6-M5 | `SanjulikaSthirAI/orders-api` | guardrail | API standards require list endpoints that can grow beyond a few hundred rows to be paginated. GET /orders is an unpaginated array in the current contract. The planned customer filter preserves and extends this list endpoint, so the design must explicitly handle or accept this existing standards mismatch. | orders-api code owners / solution architect | resolved | Accepted for this intent: GET /orders stays an unpaginated array, as today; the demo store holds only a few orders. The customer filter only reduces the result. Pagination is a separate follow-up intent. |
| INT-6-M6 | `SanjulikaSthirAI/orders-ui` | deployment | The UI repo is brownfield but has unknown deployed version and unknown deployed contract version. This prevents a complete deployed-vs-base comparison for G2 and should be resolved before relying on deployed behavior assumptions. | orders-ui deploy/release owner | resolved | Not relevant to this intent: there are no changes to orders-ui. The UI repo is untouched and nothing in this design depends on its deployed version. |
| INT-6-M7 | `SanjulikaSthirAI/orders-ui` | guardrail | Reference design says the UI calls the service only through its API client module and only with operations present in the contract. The approved scope excludes screen changes, but if the UI is changed later to consume the new summary or customer filter, it must wait for the orders-api contract update first. Current API contract does not yet include those operations. | orders-ui code owners | resolved | Agreed and out of scope: this intent makes no UI changes. Any later UI use of the summary or customer filter will be a separate intent after contract 1.1.0 is merged. |

## Appendix D. Protected contracts

Stories must not change these unless plan.json marks the story as a contract change. Machine-readable copy: `protected-contracts.json`.

| Repo | Files | Endpoints |
| --- | --- | --- |
| `SanjulikaSthirAI/orders-api` | `openapi.yaml` | `GET /orders`, `GET /orders/{order_id}`, `POST /orders`, `POST /orders/{order_id}/cancel` |
| `SanjulikaSthirAI/orders-ui` | `**/*` | - |

## Appendix E. ADRs

_None._

Proposed but not written (an ADR must meet all three tests):

_None._

## Appendix F. Prototypes (throwaway; never used as a starting point at G4)

_None._
