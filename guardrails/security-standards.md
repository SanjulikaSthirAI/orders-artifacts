# Security standards

The security specialist is consulted on the security section of every design. This file is what they and the
design agent check against.

## Access

- Every endpoint that returns customer data or changes state requires authentication and an authorization check
  against the caller's rights to that record. "The caller is logged in" is not an authorization check.
- Authorization is decided on the server. The UI hides buttons for convenience only.
- Anything that moves money (refunds, credits) is high risk. It needs its own authorization rule, an audit trail
  and an idempotency key.

## Input and output

- Validate every input at the boundary with the framework's models: types, lengths, ranges, allowed values.
- Build queries with parameters, never by joining strings.
- In the browser, set text with `textContent`. Never put API data into `innerHTML`.
- Return only the fields a caller needs. Do not return internal identifiers, stack traces or database errors.

## Data

- Customer names and contact details are personal data. Keep them out of logs, error messages and test fixtures
  that use real people. Demo data is synthetic.
- No secrets in the repo. Configuration that differs by environment comes from environment variables.

## Supply chain

- Dependencies are pinned and come from the standard package indexes. A new dependency is named in the design
  and justified.
- CI runs the dependency and static checks the risk tier requires. A high-risk story also needs a security review.
