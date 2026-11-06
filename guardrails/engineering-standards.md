# Engineering standards

These apply to every repo in the orders project. The design agent checks planned designs against them, and the
rubric reviewers check pull requests against them.

## Languages and frameworks

- Services: Python 3.12 with FastAPI and Pydantic. See ADR 0001.
- Browser UI: plain HTML and ES modules. No framework and no build step unless an ADR says otherwise.
- New languages or frameworks need an ADR before design approval.

## Tests

- Every acceptance criterion has at least one automated test, and the test's name says which case it covers.
- Cover failure paths (bad input, missing record, wrong state), not only the happy path.
- Tests are deterministic: inject the clock and any randomness; never depend on real time or network.
- A change that alters an API contract updates the contract test in the same commit.

## Change and review

- Work happens on a story branch and merges by pull request. Nobody pushes to `develop` or `main`.
- A pull request changes one story. Unrelated cleanup goes in its own story.
- CI must pass: `lint` and `tests` for every repo, plus any check the story's risk tier adds.
- Code owners review changes to the paths listed in each repo's `CODEOWNERS`.

## Code

- Pin dependency versions exactly. Upgrades are their own change.
- No secrets, tokens or real customer data in code, tests, fixtures or logs. Use environment variables.
- Money is an integer number of minor units (`*_cents`). Never use floating point for money.
- Errors carry a useful message for the caller. Do not swallow exceptions silently.
- Log what happened and which record it concerned, but never customer names, addresses or payment details.
