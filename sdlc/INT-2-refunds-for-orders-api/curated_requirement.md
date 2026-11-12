# Requirements: Refund Orders through the orders API

## Business rules
- BR-1: A Refund is allowed only for a Recent order.
- BR-2: A Refund must be a Full-order refund for the full paid Order total exactly as captured on the original Order.
- BR-3: An Order can be refunded only once.
- BR-4: A Refund is allowed only for an Order with a successfully paid or captured payment.
- BR-5: Only Support staff with the required refund permission or role may request a Refund through the orders API.
- BR-6: Provider acceptance or initiation of the Refund is treated as a successful Refund.
- BR-7: Refund requests must include an idempotency key or request ID so retries can return the original outcome without creating a duplicate Refund.
- BR-8: Idempotency records must remain available for at least 30 days.
- BR-9: The 30-day Refund window is a rolling 30×24-hour period from the exact Order placement timestamp to the Refund request time, inclusive through exactly 30 days, using server/system time.
- BR-10: First-version Refund rules allow only successfully captured external cash or card payments; store-credit, gift-card, promo-credit, mixed-tender, and multi-capture Orders are not refundable.
- BR-11: Orders with any previous refund that was not a Full-order refund, chargeback, payment dispute, or payment reversal are not refundable in the first version.

## Functional requirements
### FR-1: Request a Full-order Refund
The orders API must allow Support staff with the required refund permission or role to request a Refund for an Order. When the request is an Eligible refund request, the system must initiate a Full-order refund for the full paid Order total exactly as captured on the original Order.

Acceptance criteria:
- AC-1.1: Given Support staff with the required refund permission or role, a Recent order, a successfully captured external cash or card payment, no prior Refund, no Refund already being processed, no chargeback, no payment dispute, no payment reversal, and a new idempotency key or request ID, when the Support staff member requests a Refund through the orders API, then the orders API initiates a Full-order refund for the full paid Order total exactly as captured on the original Order.
- AC-1.2: Given an otherwise Eligible refund request for an Order placed exactly 30×24 hours before the Refund request time, when Support staff requests a Refund, then the orders API treats the Order as a Recent order.
- AC-1.3: Given an otherwise Eligible refund request for an Order placed before this feature went live and within the last 30 days, when Support staff requests a Refund, then the orders API allows the Refund.

### FR-2: Mark and return successful Refund details
When a Refund succeeds, the system must mark the Order as refunded and return Refund details to Support staff.

Acceptance criteria:
- AC-2.1: Given the payment provider accepts or initiates a Refund, when the orders API completes the Refund request, then the Order is marked as refunded with a refund timestamp and refund amount.
- AC-2.2: Given a successful Refund, when the orders API returns the success response, then the response includes the refund timestamp and refund amount.
- AC-2.3: Given a successful Refund, when the refund timestamp is recorded, then the timestamp is based on server/system time.

### FR-3: Reject Orders outside the 30-day Refund window
The orders API must reject Refund requests for Orders that are not Recent orders and must return a clear error.

Acceptance criteria:
- AC-3.1: Given Support staff requests a Refund for an Order placed more than a rolling 30×24-hour period before the Refund request time, when the Order is not already refunded and no Refund is already being processed for the Order, then the orders API rejects the request with an “order older than 30 days” error.
- AC-3.2: Given any Refund request, when the orders API evaluates whether the Order is a Recent order, then the evaluation uses server/system time and the exact Order placement timestamp.

### FR-4: Prevent duplicate Refunds
The orders API must prevent the same Order from being refunded twice, including concurrent attempts and safe retries.

Acceptance criteria:
- AC-4.1: Given an Order is already marked as refunded, when Support staff requests a Refund for that Order, then the orders API rejects the request with an “order already refunded” error.
- AC-4.2: Given an Order is both already marked as refunded and older than 30 days, when Support staff requests a Refund for that Order, then the orders API rejects the request with an “order already refunded” error.
- AC-4.3: Given two Refund requests for the same eligible Order with different idempotency keys are made at nearly the same time, when the requests are processed, then exactly one Refund is initiated and the other request is rejected with a “refund already in progress” error while the first Refund is still processing.
- AC-4.4: Given a Refund is already being processed for an Order, when Support staff requests another Refund for that Order, then the orders API rejects the request with a “refund already in progress” error.
- AC-4.5: Given an Order has a Refund already being processed and also has another eligibility issue, when Support staff requests a Refund for that Order, then the orders API rejects the request with a “refund already in progress” error.
- AC-4.6: Given a money Refund has been initiated but the Order has not been marked as refunded due to a later failure, when Support staff retries the same Refund request and the existing Refund details are available, then the orders API does not issue a second money Refund and marks the Order as refunded with the existing Refund details.

### FR-5: Enforce Refund authorization
The orders API must allow Refund requests only from Support staff with the required refund permission or role.

Acceptance criteria:
- AC-5.1: Given Support staff without the required refund permission or role, when they request a Refund, then the orders API rejects the request with a “not authorized to refund” error.
- AC-5.2: Given Support staff has the required refund permission or role but cannot access the referenced Order, when they request a Refund, then the orders API rejects the request with an “order not refundable or not found” error.

### FR-6: Reject non-refundable or unavailable Orders
The orders API must reject Refund requests that do not meet the first-version Refund rules and must return a clear error.

Acceptance criteria:
- AC-6.1: Given a Refund request for an Order that is not found, when the request is processed, then the orders API rejects the request with an “order not refundable or not found” error.
- AC-6.2: Given a Refund request for an Order with unpaid, cancelled-before-payment, failed-payment, or pending-payment status, when the request is processed, then the orders API rejects the request with an “order not refundable or not found” error.
- AC-6.3: Given a Refund request for an Order that does not have a successfully captured external cash or card payment, when the request is processed, then the orders API rejects the request with an “order not refundable or not found” error.
- AC-6.4: Given a Refund request for an Order with more than one successful external payment capture, when the request is processed, then the orders API rejects the request with an “order not refundable or not found” error.
- AC-6.5: Given a Refund request for an Order with a previous refund that was not a Full-order refund, chargeback, payment dispute, or payment reversal, when the request is processed, then the orders API rejects the request with an “order not refundable or not found” error.
- AC-6.6: Given a Refund request for a fulfilled, shipped, or delivered Order that is otherwise an Eligible refund request, when the request is processed, then the orders API does not reject the request because the Order is fulfilled, shipped, or delivered.

### FR-7: Handle payment provider Refund failures
The orders API must return a distinct failure when the payment provider does not accept or initiate the Refund, and the Order must not be marked as refunded.

Acceptance criteria:
- AC-7.1: Given an otherwise Eligible refund request, when the payment provider refuses or fails the Refund attempt, then the orders API rejects the request with a “refund payment failed” error.
- AC-7.2: Given the payment provider refuses or fails the Refund attempt, when the Refund request ends, then the Order is not marked as refunded.

### FR-8: Support idempotent Refund retries
The orders API must use a request idempotency key or request ID to make Refund retries safe.

Acceptance criteria:
- AC-8.1: Given a Refund request without an idempotency key or request ID, when the request is processed, then the orders API rejects the request.
- AC-8.2: Given a Refund request with a new idempotency key or request ID, when the request is processed, then the orders API records the key or request ID with the request details and outcome for at least 30 days.
- AC-8.3: Given a repeated Refund request with the same idempotency key or request ID and the same request details after the original outcome is known, when the request is processed within the idempotency record retention period, then the orders API returns the original outcome.
- AC-8.4: Given a repeated Refund request with the same idempotency key or request ID while the original request is still processing, when the request is processed, then the orders API returns a “refund already in progress” error until the original outcome is known.
- AC-8.5: Given a Refund request reuses an idempotency key or request ID for a different Order or different Refund request details, when the request is processed, then the orders API rejects the request with an “idempotency key conflict” error.

### FR-9: Record Refund audit history internally
The system must internally record successful and failed Refund attempts for audit/history without adding a refund history retrieval API in the first version.

Acceptance criteria:
- AC-9.1: Given a successful Refund, when the request completes, then the system records the requesting Support staff member and request timestamp internally.
- AC-9.2: Given a failed Refund attempt, when the request completes, then the system records the requesting Support staff member, request timestamp, Order ID, and failure category internally.
- AC-9.3: Given any Refund audit/history timestamp is recorded, when the timestamp is set, then it uses server/system time.
- AC-9.4: Given Support staff uses the orders API in the first version, when they look for Refund audit/history retrieval, then the orders API provides no Refund audit/history retrieval capability.

## Non-functional requirements (business level)
- NFR-1: Support can complete Eligible refund requests through the orders API without Manual finance intervention for at least 90% of refund requests during each calendar month, measured as the number of Eligible refund requests completed through the orders API divided by all Eligible refund requests recorded for support.

## Open questions
- [non-blocking] What data source should be used to measure all Eligible refund requests recorded for support for NFR-1?

## Sources

- Knowledge graph: consulted
