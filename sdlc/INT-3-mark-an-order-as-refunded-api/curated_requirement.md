# Requirements: Record full order refunds in the Orders API

## Business rules
- BR-1: A Refund is a full refund record for an Order and does not move money.
- BR-2: An Eligible refund is allowed only when the Order was created at or after the cutoff exactly 30 days before the Refund time, the Order is not already refunded, and the Order is not a Cancelled order.
- BR-3: The Orders API sets the Refund time when it accepts and records the Refund.
- BR-4: After a Refund is recorded, the Order is exposed as `refunded`.
- BR-5: An Order must not be refunded more than once.
- BR-6: A Cancelled order must not be refunded.
- BR-7: Refund eligibility timestamps are compared using UTC, with the cutoff exactly 30 days before the Refund time.
- BR-8: When more than one rule prevents a Refund for an existing Order, the reason priority is: already refunded, then Cancelled order, then older than 30 days.
- BR-9: A support user does not provide a human-readable refund reason when recording a Refund; the Orders API provides a reason only when a Refund is not allowed.
- BR-10: Only support users with the existing appropriate Orders API access may record Refunds, using the existing Orders API support authorization marker and without changing how API callers authenticate.
- BR-11: Refund recording and retrieval do not add new restrictions on other Order actions.
- BR-12: Any Order that is not a Cancelled order, not already refunded, and within the 30-day cutoff is eligible for a Refund regardless of other current Order condition.
- BR-13: If no Order exists for the provided order ID, the Orders API returns a distinct order-not-found outcome.
- BR-14: Outcomes where a Refund is not allowed, including an order-not-found outcome, include a stable reason code and a non-empty human-readable message.
- BR-15: The stable reason codes are exactly `ORDER_ALREADY_REFUNDED`, `ORDER_CANCELLED`, `ORDER_TOO_OLD`, and `ORDER_NOT_FOUND`.
- BR-16: The Orders API must not record partial refunds.
- BR-17: Recording a Refund does not integrate with a payment provider and does not move money.
- BR-18: This project must not require new database or persistent store changes.

## Functional requirements
### FR-1: Record an Eligible refund
The Orders API must allow a support user with the existing appropriate Orders API access to record a Refund for an Order by order ID when the Order has an Eligible refund.

Acceptance criteria:
- AC-1.1: Given a support user with the existing appropriate Orders API access and an Order that was created after the cutoff exactly 30 days before the Refund time, is not already refunded, and is not a Cancelled order, when the support user records a Refund for the Order by order ID, then the Orders API records the Refund and returns the updated Order exposed as `refunded` with the Refund time.
- AC-1.2: Given a support user with the existing appropriate Orders API access and an Order that was created exactly at the cutoff 30 days before the Refund time, is not already refunded, and is not a Cancelled order, when the support user records a Refund for the Order by order ID, then the Orders API records the Refund and returns the updated Order exposed as `refunded` with the Refund time.
- AC-1.3: Given an authenticated caller who is not a support user with the existing appropriate Orders API access, when the caller attempts to record a Refund for an Order by order ID, then the Orders API rejects the request and the Order is not exposed as newly refunded.

### FR-2: Expose refunded Order and Refund time
The Orders API must show the Order as refunded and expose the Refund time after a Refund is recorded.

Acceptance criteria:
- AC-2.1: Given a Refund has been recorded for an Order, when the refund-recording response is returned, then the response includes the updated Order exposed as `refunded` and includes the Refund time.
- AC-2.2: Given a Refund has been recorded for an Order, when the Order is retrieved afterward through the Orders API, then the retrieved Order is exposed as `refunded` and includes the Refund time.
- AC-2.3: Given a Refund is accepted for an Order, when the Orders API records the Refund, then the Refund time exposed on the Order is set by the Orders API at acceptance time and is not supplied by the support user.

### FR-3: Prevent duplicate Refunds
The Orders API must prevent an Order from being refunded more than once and provide the required reason.

Acceptance criteria:
- AC-3.1: Given an existing Order is already refunded, when a support user with the existing appropriate Orders API access attempts to record a Refund for that Order by order ID, then the Orders API does not record another Refund and returns reason code `ORDER_ALREADY_REFUNDED` with a non-empty human-readable message.
- AC-3.2: Given a support user with the existing appropriate Orders API access repeats the same refund request for an Order that was already successfully refunded, when the repeated request is processed, then the Orders API returns reason code `ORDER_ALREADY_REFUNDED` with a non-empty human-readable message instead of returning success.

### FR-4: Prevent Refunds for Cancelled orders
The Orders API must prevent a Cancelled order from being refunded and provide the required reason.

Acceptance criteria:
- AC-4.1: Given an existing Order is a Cancelled order and is not already refunded, when a support user with the existing appropriate Orders API access attempts to record a Refund for that Order by order ID, then the Orders API does not record a Refund and returns reason code `ORDER_CANCELLED` with a non-empty human-readable message.

### FR-5: Prevent Refunds for Orders older than the 30-day cutoff
The Orders API must prevent a Refund when the Order was created before the cutoff exactly 30 days before the Refund time, comparing timestamps using UTC.

Acceptance criteria:
- AC-5.1: Given an existing Order was created before the cutoff exactly 30 days before the Refund time, is not already refunded, and is not a Cancelled order, when a support user with the existing appropriate Orders API access attempts to record a Refund for that Order by order ID, then the Orders API does not record a Refund and returns reason code `ORDER_TOO_OLD` with a non-empty human-readable message.
- AC-5.2: Given an existing Order was created at or after the cutoff exactly 30 days before the Refund time in UTC, is not already refunded, and is not a Cancelled order, when a support user with the existing appropriate Orders API access records a Refund for that Order by order ID, then the Orders API records the Refund and returns the updated Order exposed as `refunded` with the Refund time.

### FR-6: Return the highest-priority reason
The Orders API must return one stable reason code and non-empty human-readable message for the highest-priority blocker when an existing Order is not eligible for a Refund.

Acceptance criteria:
- AC-6.1: Given an existing Order is already refunded and is also a Cancelled order, when a support user with the existing appropriate Orders API access attempts to record a Refund for that Order by order ID, then the Orders API returns reason code `ORDER_ALREADY_REFUNDED` with a non-empty human-readable message.
- AC-6.2: Given an existing Order is already refunded and was created before the cutoff exactly 30 days before the Refund time, when a support user with the existing appropriate Orders API access attempts to record a Refund for that Order by order ID, then the Orders API returns reason code `ORDER_ALREADY_REFUNDED` with a non-empty human-readable message.
- AC-6.3: Given an existing Order is a Cancelled order, is not already refunded, and was created before the cutoff exactly 30 days before the Refund time, when a support user with the existing appropriate Orders API access attempts to record a Refund for that Order by order ID, then the Orders API returns reason code `ORDER_CANCELLED` with a non-empty human-readable message.

### FR-7: Return distinct outcome for missing Order
The Orders API must return a distinct missing-Order outcome when no Order exists for the provided order ID.

Acceptance criteria:
- AC-7.1: Given no Order exists for the provided order ID, when a support user with the existing appropriate Orders API access attempts to record a Refund for that order ID, then the Orders API does not record a Refund and returns reason code `ORDER_NOT_FOUND` with a non-empty human-readable message.

### FR-8: Exclude partial refunds
The Orders API must not record partial refunds as part of this project.

Acceptance criteria:
- AC-8.1: Given a support user with the existing appropriate Orders API access attempts to record less than a full Refund for an Order by order ID, when the request is processed, then the Orders API does not record a partial Refund.

## Non-functional requirements (business level)
- NFR-1: For an Order with an Eligible refund, a support user with the existing appropriate Orders API access can complete the refund-recording workflow through the Orders API without entering the Refund in the spreadsheet.

## Open questions
- [non-blocking] Should the glossary be extended in a later revision to define `support user`, `Orders API`, `order ID`, `reason code`, `human-readable message`, `refunded`, and `Orders API support authorization marker` as formal terms?

## Sources

- Knowledge graph: consulted
