# Release Package

## Commit Message

```text
chore(governance): prepare clean public release guardrails

- add public release governance rules
- add asset governance and security checklists
- define contribution and historical responsibility boundaries
- document excluded raw/export/generated/private assets
- prepare maintainer confirmation template
```

## PR Description

```markdown
## Summary

This PR prepares the repository for a clean public release by adding governance guardrails and release checklists.

## Public Boundary

This release is intended to include only approved source code, public-safe docs, templates, tests, synthetic examples, and governance materials.

It excludes raw assets, generated outputs, exports, archives, private prompts, cookies/session state, resource identifiers, and unreviewed media.

## Responsibility Boundary

This PR lowers future public-release risk. It does not certify historical commits, forks, clones, third-party redistribution, or prior public exposure.

## Checks

- [ ] Secret scan completed
- [ ] File-type scan completed
- [ ] Large-file scan completed
- [ ] Export/archive scan completed
- [ ] Asset rights reviewed
- [ ] Sample data confirmed synthetic/anonymized
- [ ] Maintainer confirmation completed
- [ ] No push/force-push/visibility change/history rewrite included
```

## Release Note

```markdown
## Public Release Governance

This release introduces public-release governance materials for a safer clean public repository:
- public release rules
- asset governance rules
- contribution boundary note
- publishing checklist
- security checklist
- maintainer confirmation template

This release does not certify historical public exposure or third-party redistribution.
```

## Governance Summary

```markdown
The repository has been reviewed for public-release readiness. Current state requires maintainer confirmation before clean-public rebuild because the audit found platform resource identifiers, export artifacts, generated assets, and private workflow/checkpoint material.

Recommended release path: create a clean public workspace with only maintainer-approved whitelist files and keep raw/export/private materials outside public Git history.
```

