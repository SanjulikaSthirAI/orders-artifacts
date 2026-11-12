# Glossary

## Refund
Money returned to a customer for an order they paid for.

## Order
A customer purchase that may be eligible for a refund.

## Recent order
An order placed in the last 30 days.

## Full-order refund
A refund of the whole order amount, rather than part of the order.
_Avoid_: partial refund

## Eligible refund request
A request for a refund that is allowed under the first-version refund rules.

## Manual finance intervention
Finance team handling outside the API-supported refund flow that support currently depends on.

## Idempotency key
A caller-supplied value that identifies one refund request so retries can return the original outcome without creating another refund.
_Avoid_: request ID

## Refund audit history
Internal history of refund attempts and outcomes kept for accountability.
_Avoid_: refund reporting
