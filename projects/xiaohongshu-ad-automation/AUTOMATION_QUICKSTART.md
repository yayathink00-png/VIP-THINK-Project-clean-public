# Automation Quickstart

## Fastest Path

Run this from:

```bash
cd /Users/yangyi/Documents/xiaohongshu-投放
```

Generate 10 drafts:

```bash
python3 xhs_auto_generator.py --count 10
```

Successful output looks like:

```text
Generated 10 drafts
Markdown: /Users/yangyi/Documents/xiaohongshu-投放/outputs/xhs_batch_YYYYMMDD_HHMMSS.md
CSV: /Users/yangyi/Documents/xiaohongshu-投放/outputs/xhs_batch_YYYYMMDD_HHMMSS.csv
Latest: /Users/yangyi/Documents/xiaohongshu-投放/outputs/latest.md
```

Open:

- `outputs/latest.md` for human review
- `outputs/latest.csv` for spreadsheet workflow

## Daily Operating Rule

1. Run the command.
2. Open `outputs/latest.md`.
3. Publish green drafts first.
4. Review yellow drafts before publishing.
5. Do not publish red drafts.

## Optional AI Mode

If an OpenAI API key is configured in the environment, run:

```bash
python3 xhs_auto_generator.py --count 10 --ai
```

If AI generation fails, the script automatically falls back to local templates.

## What This Automates Now

- Topic generation
- Title options
- Cover text
- Carousel page script
- Caption body
- Hashtags
- CTA
- Risk level
- Publish recommendation
- Markdown and CSV export

## What This Does Not Automate Yet

- Real competitor crawling
- Image generation
- Xiaohongshu auto-publish
- Performance data ingestion

Those should come after this draft generator is producing usable content.
