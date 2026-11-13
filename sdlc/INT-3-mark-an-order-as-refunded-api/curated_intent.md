# Curated Intent

## Business outcome
Support can record eligible order refunds in the Orders API instead of tracking them in a spreadsheet.

## Affected users
Support users who record order refunds.

## Scope
- Record a full refund for an order by order ID through the Orders API.
- Show the order as refunded after the refund is recorded.
- Record the time of the refund.
- Allow refunds only for orders created in the last 30 days.
- Prevent an order from being refunded more than once.
- Prevent cancelled orders from being refunded.
- Provide a reason when a refund is not allowed.

## Exclusions
- Orders screen changes.
- Partial refunds.
- New database or persistent store changes.
- Payment provider integration or moving money.
- Changes to how API callers authenticate.

## Success measure
Support can record refunds through the Orders API without using the spreadsheet for eligible refunds.

## Accountable owner
Product Owner

## Project type

project_type: brownfield

## Repositories

| Repo | repo_type | Evidence |
| --- | --- | --- |
| `SanjulikaSthirAI/orders-api` | brownfield | neo4j: has commits, deployed 1.0.0, published contract |
