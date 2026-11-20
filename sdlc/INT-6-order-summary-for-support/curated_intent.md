# Business outcome
Support leads can quickly understand the order book from the API without exporting order data or manually counting orders. They can also narrow the order list to a specific customer without manual filtering.

# Affected users
Support leads.

# Scope
- Provide a read-only order summary showing counts by status: placed, shipped, delivered and cancelled.
- Include the total value in cents of all non-cancelled orders in the order summary.
- Return zero counts and a zero total when there are no orders.
- Allow the existing order list to be filtered by customer name.
- Allow the customer filter to work together with the existing status filter.
- Preserve current order list behaviour when no customer filter is used.

# Exclusions
- No screen changes.
- No authentication changes.
- No new storage.
- No changes to how orders are placed or cancelled.
- No changes to existing endpoints or fields.

# Success measure
Support leads can get order counts, non-cancelled total value and customer-filtered order lists from the API without exporting data or manually counting or filtering orders.

# Accountable owner
Product Owner

## Project type

project_type: brownfield

## Repositories

| Repo | repo_type | Evidence |
| --- | --- | --- |
| `SanjulikaSthirAI/orders-api` | brownfield | neo4j: has commits, deployed 1.0.0, published contract |
| `SanjulikaSthirAI/orders-ui` | brownfield | neo4j: has commits |
