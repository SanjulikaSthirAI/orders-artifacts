# Requirements: Order summary and customer-filtered Order book

## Business rules
- BR-1: The Order book summary is a global read-only snapshot across all existing Orders.
- BR-2: The Order book summary always includes counts for Order status placed, shipped, delivered and cancelled.
- BR-3: The Non-cancelled total value is the sum, in cents, of the full stored value for every existing Order with Order status placed, shipped or delivered.
- BR-4: Orders with Order status cancelled do not contribute to the Non-cancelled total value.
- BR-5: Orders with Order status outside placed, shipped, delivered and cancelled are excluded from the Order book summary counts and from the Non-cancelled total value.
- BR-6: An Order with a missing or null stored value contributes 0 cents to the Non-cancelled total value while still being counted in its Order status bucket when its Order status is placed, shipped, delivered or cancelled.
- BR-7: An Order with a negative stored value contributes that negative value as stored to the Non-cancelled total value when its Order status is placed, shipped or delivered.
- BR-8: The Customer filter matches the Customer name after trimming leading and trailing spaces from the request value.
- BR-9: The Customer filter is an exact, case-sensitive match against the stored Customer name.
- BR-10: A blank or whitespace-only Customer filter value means no Customer filter is applied.
- BR-11: Orders with a missing or null Customer name do not match any provided non-blank Customer filter, but remain in the Order book when no Customer filter is applied.
- BR-12: When both Customer filter and Order status filter are provided, the returned Orders contain only Orders that match both the trimmed exact Customer name and the requested Order status.

## Functional requirements
### FR-1: Provide global Order book summary
The system must provide a new read-only API capability for Support leads to retrieve an Order book summary without changing existing API capabilities or fields.

Acceptance criteria:
- AC-1.1: Given existing Orders in the Order book, when a Support lead requests the Order book summary, then the response includes counts for placed, shipped, delivered and cancelled Orders across all existing Orders.
- AC-1.2: Given no existing Orders, when a Support lead requests the Order book summary, then the response includes placed, shipped, delivered and cancelled counts of 0 and a Non-cancelled total value of 0 cents.
- AC-1.3: Given existing Orders in the Order book and any Customer filter or Order status filter used for returned Orders, when a Support lead requests the Order book summary, then the Order book summary is calculated across all existing Orders without applying those filters.

### FR-2: Count Order book summary by Order status
The system must report Order book summary counts for each Order status placed, shipped, delivered and cancelled, and exclude any Order status outside placed, shipped, delivered and cancelled from those counts.

Acceptance criteria:
- AC-2.1: Given there are no Orders for one or more of placed, shipped, delivered or cancelled, when a Support lead requests the Order book summary, then the response still includes each absent Order status with a count of 0.
- AC-2.2: Given an Order has Order status placed, shipped, delivered or cancelled, when a Support lead requests the Order book summary, then that Order contributes 1 to the matching Order status count.
- AC-2.3: Given an Order has Order status outside placed, shipped, delivered and cancelled, when a Support lead requests the Order book summary, then that Order does not contribute to any Order status count.

### FR-3: Calculate Non-cancelled total value
The system must include the Non-cancelled total value in cents in the Order book summary.

Acceptance criteria:
- AC-3.1: Given existing Orders with Order status placed, shipped or delivered, when a Support lead requests the Order book summary, then the Non-cancelled total value equals the sum of their full stored values in cents.
- AC-3.2: Given existing Orders with Order status cancelled, when a Support lead requests the Order book summary, then cancelled Orders do not contribute to the Non-cancelled total value.
- AC-3.3: Given an Order has an Order status outside placed, shipped, delivered and cancelled, when a Support lead requests the Order book summary, then that Order does not contribute to the Non-cancelled total value.
- AC-3.4: Given an Order with Order status placed, shipped or delivered has a missing or null stored value, when a Support lead requests the Order book summary, then that Order contributes 0 cents to the Non-cancelled total value.
- AC-3.5: Given an Order with Order status placed, shipped or delivered has a negative stored value, when a Support lead requests the Order book summary, then that Order contributes the negative value exactly as stored to the Non-cancelled total value.

### FR-4: Filter returned Orders by Customer name
The system must allow Support leads to apply a Customer filter to returned Orders while preserving current Order book retrieval behaviour when no Customer filter is used.

Acceptance criteria:
- AC-4.1: Given Orders with stored Customer names, when a Support lead requests Orders with a non-blank Customer filter, then the response includes only Orders whose stored Customer name exactly matches the trimmed Customer filter value with the same letter casing.
- AC-4.2: Given an Order with Customer name `Alice`, when a Support lead requests Orders with Customer filter value ` Alice `, then the Order is included in the response.
- AC-4.3: Given an Order with Customer name `Alice`, when a Support lead requests Orders with Customer filter value `alice`, then the Order is not included in the response.
- AC-4.4: Given a non-blank Customer filter and no matching Orders, when a Support lead requests Orders, then the system returns a successful response with no Orders.
- AC-4.5: Given Orders with missing or null Customer names, when a Support lead requests Orders with a non-blank Customer filter, then those Orders are not included in the response.
- AC-4.6: Given Orders with missing or null Customer names that are returned when no Customer filter is applied, when a Support lead requests Orders without a Customer filter, then those Orders remain in the response.
- AC-4.7: Given a blank or whitespace-only Customer filter value, when a Support lead requests Orders, then no Customer filter is applied.

### FR-5: Combine Customer filter with Order status filter
The system must allow the Customer filter to work together with the existing Order status filter.

Acceptance criteria:
- AC-5.1: Given both a non-blank Customer filter and an Order status filter are provided, when a Support lead requests Orders, then the response includes only Orders matching both the trimmed exact Customer name and the requested Order status.
- AC-5.2: Given only an Order status filter is provided, when a Support lead requests Orders, then only the Order status filter is applied.
- AC-5.3: Given no Customer filter is provided, when a Support lead requests Orders, then no Customer filter is applied.

## Non-functional requirements (business level)

## Open questions
- [non-blocking] The glossary does not define Order book summary, Order status filter, API capability, returned Orders, response, or stored value; confirm whether these should be added to the glossary.

## Sources

- Knowledge graph: consulted
