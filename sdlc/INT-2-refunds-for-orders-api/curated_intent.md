# Curated Intent

## Business outcome
Support can return money to customers when an order is not right without manual finance handling for eligible refund requests.

## Affected users
- Support staff using support tools backed by the orders API
- Customers receiving money back for refunded orders

## Scope
- Enable support to refund an order through the orders API.
- Limit refunds to orders placed in the last 30 days.
- Support full-order refunds only.
- Prevent the same order from being refunded twice.
- Provide clear error messages when a refund is not allowed, distinguishing:
  - order older than 30 days
  - order already refunded
  - order not refundable or not found

## Exclusions
- Orders screen changes.
- Partial refunds.
- Refund reporting.

## Success measure
Support can complete eligible order refunds through the API without manual finance intervention for at least 90% of refund requests.

## Accountable owner
Product Owner

## Project type

project_type: brownfield

## Repositories

| Repo | repo_type | Evidence |
| --- | --- | --- |
| `SanjulikaSthirAI/orders-api` | brownfield | neo4j: has commits, deployed 1.0.0, published contract |
| `SanjulikaSthirAI/orders-ui` | brownfield | neo4j: has commits |
