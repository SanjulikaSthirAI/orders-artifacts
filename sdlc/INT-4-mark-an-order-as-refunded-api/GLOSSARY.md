# Glossary

## Order
A purchase record that can be refunded or cancelled.

## Refund
A record that an order has been refunded. In this first version, it records the refund state and time only; moving money remains manual.
_Avoid_: partial refund

## Refunded order
An order marked as refunded, with the time of the refund recorded. A refunded order cannot later be cancelled.

## Cancelled order
An order that has been cancelled. A cancelled order cannot be refunded.

## Recent order
An order created in the last 30 days.

## Refund action
The Orders API action support uses to mark an order as refunded by order ID.

## Refund reason
The explanation returned when a refund is not allowed.
