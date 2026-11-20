## Business outcome
Support can process eligible order refunds quickly within the orders system instead of handling refund requests manually.

## Affected users
Support agents and customers requesting money back for orders that are not right.

## Scope
- Support agents can refund an order from the orders screen.
- Refunds are available only for orders placed in the last 30 days.
- Only full-order refunds are included.
- A refund returns the customer's money for the order.
- The same order cannot be refunded twice.
- Support agents see a clear message if something goes wrong.

## Exclusions
- Refund reporting.
- Partial refunds.
- Customer self-service refunds.
- Refunds for orders older than 30 days.

## Success measure
Reduce average handling time for refund requests by 50%.

## Accountable owner
Product Owner

## Project type

project_type: brownfield

## Repositories

| Repo | repo_type | Evidence |
| --- | --- | --- |
| `SanjulikaSthirAI/orders-api` | brownfield | neo4j: has commits, deployed 1.0.0, published contract |
| `SanjulikaSthirAI/orders-ui` | brownfield | neo4j: has commits |
