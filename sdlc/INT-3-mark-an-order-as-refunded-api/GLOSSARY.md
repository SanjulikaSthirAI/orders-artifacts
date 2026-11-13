# Glossary

## Order
A customer order that can be identified by its order ID and may be eligible for a refund.

## Refund
A record that an order has been refunded. In this first version, it is a full refund record only and does not move money.

## Eligible refund
A refund that is allowed for an order. The order must have been created in the last 30 days, must not already be refunded, and must not be cancelled.

## Cancelled order
An order that has been cancelled and cannot be refunded.

## Refund time
The time at which the refund is recorded for the order.

## Reason code
A stable code returned by the Orders API to identify why a Refund is not allowed.
_Avoid_: error text, failure string

## Support user
A caller with the existing appropriate Orders API access for recording Refunds.
_Avoid_: admin, agent

## Refunded
The exposed Order state after a Refund has been recorded for the Order.
_Avoid_: reimbursed, paid back
