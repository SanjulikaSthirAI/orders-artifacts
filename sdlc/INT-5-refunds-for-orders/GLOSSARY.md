# Glossary

## Refund
Money returned to a customer for an order they paid for.

## Order
A customer's purchase in the orders system.

## Recent order
An order placed in the last 30 days and eligible for refund consideration in the first version.

## Full-order refund
A refund of the whole order amount, rather than only part of the order.
_Avoid_: Partial refund

## Support agent
A support user who handles customer refund requests.

## Refund request
A customer request to get money back because an order is not right.

## Refund unavailable reason
A stable explanation shown to an authorized Support agent when an Order cannot be refunded.
_Avoid_: Error reason, disabled reason

## Idempotency key
A caller-provided value that identifies one confirmed Refund attempt so repeated submissions do not create more than one Refund.
_Avoid_: Retry token, duplicate key

## Refund audit/history record
An internal record of a successful Refund used to show who performed it, which Order it applied to, the amount, the date/time, and the processor reference when available.
_Avoid_: Refund report, Support note
