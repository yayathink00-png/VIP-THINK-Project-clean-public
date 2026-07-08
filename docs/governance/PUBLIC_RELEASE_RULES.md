# Public Release Rules

## Principles

- Public repositories use minimum exposure by default.
- Untrusted assets are private by default.
- Unreviewed content is isolated by default.
- Governance lowers future public risk and does not certify historical exposure.
- Every release action must be auditable, explainable, and reversible.

## Allowed By Default

- public README and documentation
- source code intended for public reuse
- tests
- open-source dependency manifests
- config templates with fake values
- synthetic examples and sample data
- approved demo assets
- governance documentation

## Blocked By Default

- raw captures and raw sources
- exports and packaged release artifacts
- generated images, videos, audio, PDFs, HTML exports, CSV exports
- private prompts and AI intermediate artifacts
- cookies, sessions, tokens, API keys, app tokens, table IDs, spreadsheet tokens, webhooks
- logs, caches, local databases, temporary files
- customer, student, parent, supplier, order, revenue, cost, contract, pricing, or internal strategy content

## Required Before Public Release

- maintainer confirmation
- secret scan
- file-type scan
- large-file scan
- export/archive scan
- prompt/IP boundary check
- asset rights confirmation
- README public/private boundary statement
- PR review

