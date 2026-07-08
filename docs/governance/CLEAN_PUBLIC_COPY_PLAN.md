# Clean Public Copy Plan

Status: paused pending maintainer confirmation.

## Default Strategy

Use a new local clean-public workspace or orphan branch. Do not destructively delete files in the original checkout.

Recommended local layout:

```text
clean-public/
  README.md
  LICENSE
  .gitignore
  docs/
  src/
  examples/
  prompts/
  config/
  governance/
```

## Default Whitelist

Copy only after review:
- root `README.md`, rewritten for public boundary
- `LICENSE`, if present or newly added by maintainer choice
- safe source code under `src/`
- tests
- dependency manifests
- `.env.example` files using obvious fake placeholders
- sanitized docs
- synthetic sample data only
- approved demo assets only
- governance docs generated in `governance-output/`

## Default Blocklist

Never copy automatically:
- `raw-captures/`
- `raw-sources/`
- `outputs/`
- `exports/`
- `dist/`
- `final-releases/`
- dated checkpoint/handoff folders
- ZIP/RAR/7Z/TAR/GZ archives
- PDF exports
- HTML exports
- CSV/XLS/XLSX exports unless synthetic and approved
- unreviewed PNG/JPG/GIF/WEBP assets
- logs
- caches
- local database files
- cookies/session files
- real tokens, resource identifiers, webhooks, credentials
- private prompt packs
- AI intermediate artifacts
- files with unclear ownership or public boundary

## Candidate Safe Copy After Sanitization

These candidates still require confirmation:
- `audio-scraping/src/audio_bi_pipeline/`
- `audio-scraping/tests/`
- `audio-scraping/pyproject.toml`
- selected `README.md` files rewritten to remove internal identifiers and private workflow references
- selected `.env.example` templates with safe placeholders

## Stop Conditions

Pause immediately if any copied file contains:
- real API keys, tokens, cookies, passwords, private keys
- user, customer, student, parent, supplier, contract, pricing, order, revenue, cost, or account data
- internal business strategy or private prompt material
- unreviewed media assets or generated outputs

