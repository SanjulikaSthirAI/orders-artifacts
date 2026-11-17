# Requirements: Orders API refund action

## Business rules
- BR-1: A Refund records that an Order has been refunded and records the refund time only; moving money remains manual.
- BR-2: A Refund action is allowed only for a Recent order, where the Refund action processing time is less than or equal to the Order creation timestamp plus 30×24 hours.
- BR-3: An Order is eligible for a Refund at the exact 30-day cutoff when the Refund action processing time equals the Order creation timestamp plus 30×24 hours.
- BR-4: A Refunded order cannot be refunded again.
- BR-5: A Cancelled order cannot be refunded.
- BR-6: A Refunded order cannot later be cancelled.
- BR-7: An Order must never be both a Refunded order and a Cancelled order.
- BR-8: If more than one Refund reason applies when a Refund is not allowed for an Order, the Refund reason priority is: "order already refunded", then "order cancelled", then "refund window expired".
- BR-9: The only Refund blockers for this version are: Order not found, Order already refunded, Cancelled order, and Order outside the Recent order window.
- BR-10: The Refund action does not require or store a Support-provided reason or comment.

## Functional requirements
### FR-1: Record a Refund for an Order
The Orders API must provide a Refund action that Support can use to mark an Order as refunded by Order ID.

Acceptance criteria:
- AC-1.1: Given an existing Order that is not a Refunded order, is not a Cancelled order, and has a creation timestamp less than or equal to 30×24 hours before the Refund action processing time, when Support performs the Refund action for that Order ID, then the Order is marked as a Refunded order and the refund time is recorded.
- AC-1.2: Given an existing Order that is not a Refunded order, is not a Cancelled order, and has a creation timestamp less than or equal to 30×24 hours before the Refund action processing time, when Support performs the Refund action for that Order ID, then the response includes the same refund time that is recorded for the Order.
- AC-1.3: Given Support performs the Refund action for an Order ID and supplies a refund time, when the request is processed, then the supplied refund time is not used as the recorded refund time.
- AC-1.4: Given Support performs the Refund action for an Order ID, when the request is sent with only the Order ID and no request body, then the Orders API processes the request.

### FR-2: Return Refund success information
The Orders API must return clear information when a Refund is successfully recorded.

Acceptance criteria:
- AC-2.1: Given an existing Order that is allowed to be refunded, when Support performs the Refund action for that Order ID, then the response includes the Order ID, whether the Order is a Refunded order, and the refund time.

### FR-3: Reject Refund for an unknown Order
The Orders API must not record a Refund when the Order ID does not exist.

Acceptance criteria:
- AC-3.1: Given no Order exists for the supplied Order ID, when Support performs the Refund action for that Order ID, then a not-found response is returned with Refund reason "order not found".
- AC-3.2: Given no Order exists for the supplied Order ID, when Support performs the Refund action for that Order ID and later requests the same Order ID, then the Order is still not found.

### FR-4: Reject repeat Refunds
The Orders API must prevent a Refunded order from being refunded again.

Acceptance criteria:
- AC-4.1: Given an Order is already a Refunded order, when Support performs the Refund action for that Order ID, then the Refund is rejected with Refund reason "order already refunded".
- AC-4.2: Given an Order is already a Refunded order, when Support performs the Refund action for that Order ID, then the original refund time remains unchanged in later Order API behavior that returns the Order.

### FR-5: Reject Refunds for Cancelled orders
The Orders API must prevent a Cancelled order from being refunded.

Acceptance criteria:
- AC-5.1: Given an Order is a Cancelled order, when Support performs the Refund action for that Order ID, then the Refund is rejected with Refund reason "order cancelled".
- AC-5.2: Given an Order is a Cancelled order, when Support performs the Refund action for that Order ID, then later Order API behavior that returns the Order still shows the Order as cancelled and not a Refunded order.

### FR-6: Enforce Recent order eligibility
The Orders API must allow Refunds only for a Recent order, using exact elapsed time from the Order creation timestamp.

Acceptance criteria:
- AC-6.1: Given an existing Order is not a Refunded order, is not a Cancelled order, and the Refund action processing time is earlier than the Order creation timestamp plus 30×24 hours, when Support performs the Refund action for that Order ID, then the Order is marked as a Refunded order and the refund time is recorded.
- AC-6.2: Given an existing Order is not a Refunded order, is not a Cancelled order, and the Refund action processing time is equal to the Order creation timestamp plus 30×24 hours, when Support performs the Refund action for that Order ID, then the Order is marked as a Refunded order and the refund time is recorded.
- AC-6.3: Given an existing Order is not a Refunded order, is not a Cancelled order, and the Refund action processing time is later than the Order creation timestamp plus 30×24 hours, when Support performs the Refund action for that Order ID, then the Refund is rejected with Refund reason "refund window expired".
- AC-6.4: Given an Order is not a Recent order, when Support performs the Refund action for that Order ID, then later Order API behavior that returns the Order shows the Order is not a Refunded order.

### FR-7: Prioritize Refund reasons
The Orders API must return the agreed Refund reason when more than one Refund-blocking condition applies.

Acceptance criteria:
- AC-7.1: Given an Order is already a Refunded order and is not a Recent order, when Support performs the Refund action for that Order ID, then the Refund is rejected with Refund reason "order already refunded".
- AC-7.2: Given an Order is a Cancelled order and is not a Recent order, when Support performs the Refund action for that Order ID, then the Refund is rejected with Refund reason "order cancelled".

### FR-8: Prevent cancellation after Refund
The Orders API must prevent a Refunded order from later becoming a Cancelled order.

Acceptance criteria:
- AC-8.1: Given an Order is a Refunded order, when Support attempts to cancel that Order, then the cancel attempt is rejected with reason "order already refunded".
- AC-8.2: Given an Order is a Refunded order, when Support attempts to cancel that Order, then later Order API behavior that returns the Order shows the Order as a Refunded order and not cancelled.

### FR-9: Expose Refund information in Order responses
The Orders API must expose Refund information in Order responses so Support can see whether an Order is refunded.

Acceptance criteria:
- AC-9.1: Given a newly created Order has not been refunded, when the create response is returned, then it shows `refunded: false` and `refundTime: null`.
- AC-9.2: Given an Order has not been refunded, when the Order is returned in an existing read response, then it shows `refunded: false` and `refundTime: null`.
- AC-9.3: Given an Order has not been refunded, when the Order is returned in an existing list response, then it shows `refunded: false` and `refundTime: null`.
- AC-9.4: Given an Order has been refunded, when the Order is returned in an existing read response, then it shows `refunded: true` and the recorded refund time.
- AC-9.5: Given an Order has been refunded, when the Order is returned in an existing list response, then it shows `refunded: true` and the recorded refund time.
- AC-9.6: Given an Order is returned in an existing cancellation success response, when the response is returned, then it shows the existing cancelled state alongside `refunded` and `refundTime`.
- AC-9.7: Given an Order is returned in any create, read, list, Refund action success, or cancellation success response, when the response includes cancelled state and refund fields, then it does not show both cancelled state and `refunded: true` for the same Order.

## Non-functional requirements (business level)
- NFR-1: Support can determine from the Orders API whether an Order has a Refund recorded without consulting a separate spreadsheet.

## Open questions
- [non-blocking] Should the glossary be extended with the exact Refund reason values "order not found", "order already refunded", "order cancelled", and "refund window expired"?
- [non-blocking] Should the glossary be extended with terminology for cancel attempt rejection reasons, since "Refund reason" only covers explanations returned when a Refund is not allowed?

## Sources

- Knowledge graph: consulted
