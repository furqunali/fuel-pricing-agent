# Engineering Standards

## Pricing integrity

- Preserve the documented first-effective-price and carry-forward business rules.
- Validate domain inputs before processing.
- Keep pricing calculations deterministic and independently testable.
- Do not store secrets, customer data, or generated credentials in source control.

## Change quality

- Add regression coverage for every business-rule change.
- Prefer small, reviewable pull requests with explicit acceptance criteria.
- Keep operational tooling separate from domain logic.
