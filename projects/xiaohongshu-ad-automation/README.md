# Xiaohongshu Ad Automation

小红书投放内容自动化本地项目公开版。

## Included

- Content generation scripts for Xiaohongshu post drafts and image pages.
- Brand rules, visual guidelines, content seeds, and public-safe templates.
- Generated batches, publish packs, preview images, and competitor summary outputs.
- SmartBI and Xiaohongshu integration templates without live credentials.

## Excluded

The public upload intentionally excludes local runtime and sensitive source data:

- OAuth status files and live authorization tokens.
- Raw competitor crawl files that may contain platform request tokens.
- Raw SmartBI Excel exports and local business source data.
- Python cache files and local runtime artifacts.

## Main Entrypoints

- `xhs_auto_generator.py` - batch content generation.
- `xhs_image_renderer.py` - render post image pages.
- `xhs_loop.py` - daily loop orchestration.
- `xhs_competitor_leaderboard.py` - competitor content ranking output.
- `LOOP_SETUP.md` - local workflow setup notes.
