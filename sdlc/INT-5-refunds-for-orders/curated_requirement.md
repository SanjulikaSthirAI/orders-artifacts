# Requirements: Support agents can process eligible order refunds

## Business rules
- BR-1: Only a Support agent with refund permission can see or issue a Refund.
- BR-2: A Support agent with refund permission can issue a Refund for an Order only when the Order is currently paid, is a Recent order, and has not already been refunded.
- BR-3: A Recent order is determined using the Order creation timestamp and includes an Order created less than or equal to 30 days before the Refund attempt.
- BR-4: A Full-order refund returns the full paid Order total exactly as captured on the Order.
- BR-5: The same Order cannot be refunded twice.
- BR-6: A successful Refund marks the Order as refunded and shows that status on the orders screen.
- BR-7: After a successful Refund, no further paid-Order fulfillment or customer-facing paid-Order actions proceed for that Order.
- BR-8: A successful Refund is recorded in an internal audit/history record with the Support agent, Order ID, refunded amount, Refund date/time, and processor Refund or transaction reference when available.
- BR-9: The internal audit/history record is not shown to Support agent on the orders screen in this version.
- BR-10: Refund eligibility and displayed Refund date/time use the system’s standard order-service timestamp.
- BR-11: A Support agent is not required to enter a Refund reason in this version.

## Functional requirements
### FR-1: Show Refund availability on the orders screen
The system must let a Support agent with refund permission identify from the orders screen whether an Order can be refunded. The Refund action must be hidden from a Support agent without refund permission.

Acceptance criteria:
- AC-1.1: Given a Support agent with refund permission is viewing an Order that is currently paid, is a Recent order, and has not already been refunded, when the orders screen is shown, then the Refund action is available.
- AC-1.2: Given a Support agent with refund permission is viewing an Order that is not currently paid, when the orders screen is shown, then the Refund action is unavailable with a specific reason that only currently paid Orders can be refunded.
- AC-1.3: Given a Support agent with refund permission is viewing an Order created more than 30 days before the Refund attempt, when the orders screen is shown, then the Refund action is unavailable with a specific reason that only Orders placed in the last 30 days can be refunded.
- AC-1.4: Given a Support agent with refund permission is viewing an Order that has already been refunded, when the orders screen is shown, then the Refund action is unavailable with a specific reason that the Order has already been refunded.
- AC-1.5: Given a Support agent without refund permission is viewing any Order, when the orders screen is shown, then the Refund action is not shown.

### FR-2: Confirm a Full-order refund before issuing it
The system must require a Support agent with refund permission to confirm a Full-order refund before the Refund is issued.

Acceptance criteria:
- AC-2.1: Given a Support agent with refund permission is viewing an Order that is currently paid, is a Recent order, and has not already been refunded, when the Support agent selects Refund, then the system shows a confirmation that the full paid Order total will be refunded.
- AC-2.2: Given the Refund confirmation is shown, when the Support agent submits the confirmation, then the system attempts to issue a Full-order refund for the full paid Order total exactly as captured on the Order.
- AC-2.3: Given the Refund confirmation is shown, when the Support agent closes or cancels the confirmation without submitting it, then no Refund is issued and the Order remains unchanged.
- AC-2.4: Given the Refund confirmation is shown, when the Support agent submits the confirmation, then the Support agent is not required to enter a Refund reason.

### FR-3: Complete a successful Refund
The system must complete a Full-order refund for an eligible Order, update the Order, and inform the Support agent.

Acceptance criteria:
- AC-3.1: Given a Support agent with refund permission submits confirmation for an Order that is currently paid, is a Recent order, and has not already been refunded, when the Refund completes successfully, then the Order is marked as refunded.
- AC-3.2: Given a Refund completes successfully, when the orders screen is shown to a Support agent, then it shows refunded status, refunded amount, and Refund date/time.
- AC-3.3: Given a Refund completes successfully, when the result is shown to the Support agent, then the message says that the Refund completed and that the full paid Order total was refunded.
- AC-3.4: Given a Refund completes successfully, when a paid-Order fulfillment action is attempted for that Order, then that action is not completed.
- AC-3.5: Given a Refund completes successfully, when a customer-facing paid-Order action is attempted for that Order, then that action is not completed.

### FR-4: Prevent duplicate Refunds
The system must ensure repeated submissions for the same Order do not create more than one Refund.

Acceptance criteria:
- AC-4.1: Given a Support agent with refund permission submits a Refund confirmation for an Order and that Refund completes successfully, when another Refund submission for the same Order is handled, then the same Order is not refunded a second time.
- AC-4.2: Given one Refund has completed successfully for an Order, when repeated submissions for that same Order are handled, then the Order is shown as refunded.

### FR-5: Handle failed Refund attempts
The system must leave the Order unchanged and inform the Support agent when a Refund attempt fails.

Acceptance criteria:
- AC-5.1: Given a Support agent with refund permission submits confirmation for an Order that is currently paid, is a Recent order, and has not already been refunded, when the Refund attempt fails, then the Order remains unchanged and no successful Refund is recorded for that Order.
- AC-5.2: Given a Refund attempt fails, when the result is shown to the Support agent, then the message says “The refund could not be completed. Please try again.”

### FR-6: Record successful Refund history internally
The system must record basic internal audit/history details for each successful Refund without showing that audit/history record on the orders screen.

Acceptance criteria:
- AC-6.1: Given a Refund completes successfully, when the internal audit/history record is created, then it includes the Support agent, Order ID, refunded amount, and Refund date/time.
- AC-6.2: Given a Refund completes successfully and a processor Refund or transaction reference is available, when the internal audit/history record is created, then it includes that reference.
- AC-6.3: Given a Refund completes successfully, when the internal audit/history record is created, then it does not include Support agent notes.
- AC-6.4: Given a Refund completes successfully, when the orders screen is shown to a Support agent, then the internal audit/history record is not shown on the orders screen.

## Non-functional requirements (business level)

## Open questions
- [non-blocking] What baseline period and measurement method will be used to evaluate the 50% average handling time reduction?

## Sources

- Knowledge graph: consulted
