# Curated Intent

## Business outcome
Support can record refunded orders in the Orders API instead of tracking refunds in a spreadsheet.

## Affected users
Support.

## Scope
- Add an Orders API refund action for an order by its ID.
- Record that the order is refunded and the time of the refund.
- Allow refunds only for orders created in the last 30 days.
- Prevent an order from being refunded more than once.
- Prevent cancelled orders from being refunded.
- Return a reason when a refund is not allowed.
- Prevent refunded orders from being cancelled afterwards, so an order is never both refunded and cancelled.

## Exclusions
- Orders screen changes.
- Partial refunds.
- New database or persistence changes beyond the existing in-memory store.
- Payment provider integration or moving money; that remains a manual step.
- Caller authentication or rules about who may call the API.

## Success measure
Support no longer uses a spreadsheet for recording refunded orders after the API is available.

## Accountable owner
Product Owner

## Project type

project_type: brownfield

## Repositories

| Repo | repo_type | Evidence |
| --- | --- | --- |
| `SanjulikaSthirAI/orders-api` | brownfield | neo4j: has commits, deployed 1.0.0, published contract |
| `SanjulikaSthirAI/orders-ui` | brownfield | neo4j: has commits |
