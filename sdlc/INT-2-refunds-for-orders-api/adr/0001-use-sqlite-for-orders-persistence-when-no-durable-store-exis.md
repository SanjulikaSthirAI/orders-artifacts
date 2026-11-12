# ADR 0001: Use SQLite for orders persistence when no durable store exists

Status: proposed at G2 for INT-2

Meets: hard to reverse; surprising without context; the result of a real trade-off.

Why: Hard to reverse because persisted refund/idempotency/audit data creates migration obligations; surprising because the reference design otherwise says replacing in-memory persistence is its own story with its own ADR; real trade-off because the alternatives were in-memory state, a separate refund store/service, existing persistence, or SQLite.

## Context

Refunds require durable refund markers, in-progress locks, idempotency records and audit records. The technical answer says to use the existing orders-api persistence mechanism if present, and add SQLite only if the base app is in-memory only.

## Decision

If the base app has no durable persistence, add SQLite behind the existing orders store/repository boundary for this story.

## Consequences

Refund state survives process restarts without introducing a separate refund service or database product; changing persistence later will require migration. No ADR is needed if an existing durable orders persistence mechanism is used instead.
