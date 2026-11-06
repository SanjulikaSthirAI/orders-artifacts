# Reference design: REST service

Use this when a design adds a new service or a new area to an existing one. `orders-api` follows it.

## Layers

```
HTTP  ->  routes (app/main.py)  ->  store or service (app/store.py)  ->  data
```

- **Routes** parse and validate input, call the store, and turn its exceptions into HTTP errors. No business rules.
- **Models** (`app/models.py`) are the request and response shapes. They are the contract.
- **Store or service** holds the rules (what may be cancelled, how totals are computed) and raises domain
  exceptions such as `OrderNotFound`. It knows nothing about HTTP.
- **App factory:** `create_app(store)` takes its collaborators as arguments, so tests build an app with their own
  store and clock.

## Adding behaviour

1. Add the rule and its domain exceptions to the store.
2. Add the route and declare every status it can return.
3. Add or change models.
4. Regenerate `openapi.yaml`; the contract test must pass.
5. Test the rule in the store or through the route, covering each failure the contract declares.

## When a feature needs new data

- A new kind of record gets its own model, store methods and routes. Do not widen an existing model to carry
  unrelated state.
- Rules that depend on dates take the clock as a parameter. Nothing calls `datetime.now()` directly.
- Replace the in-memory store behind the same interface when persistence is required; that replacement is its own
  story with its own ADR.

## UI clients

- The UI calls the service only through its API client module, and only with operations present in the contract.
- If the UI needs an operation the contract lacks, the service changes first and the UI story depends on it.
