# VIPTHINK Xiaohongshu Loop

## What Is Ready

- Brand facts and content rules are stored in `inputs/brand/brand_rules.json`.
- VI colors, font preferences, logo rules, and XHS canvas size are stored in `inputs/brand/visual_guidelines.json`.
- IP, Logo, historical video, and historical image libraries are registered in `inputs/brand/asset_sources.json` without copying the source files.
- The competitor watchlist is in `inputs/competitor_data/competitor_watchlist.json`.
- The SmartBI connector contract is in `integrations/smartbi_xhs_task.template.json`.

## First Run

Run these commands in this folder:

```bash
cd /Users/yangyi/Documents/xiaohongshu-投放
python3 xhs_asset_index.py --max-files 10000
python3 xhs_loop.py --date today --render-images
```

Success means the second command prints a run folder and creates:

```text
runs/YYYY-MM-DD/
  input_summary.md
  content_demand.md
  candidates.csv
  publish_pack.md
  feedback.csv
```

## Add New Inputs

- Put raw SmartBI/Xiaohongshu-normalized CSV files in `inputs/performance_data/`.
- Put new product JSON or Markdown files in `inputs/product_updates/`.
- Refresh competitor data weekly and place normalized files in `inputs/competitor_data/`.

The loop works without performance data, but only uses brand rules until real data arrives.

## SmartBI And Xiaohongshu Authorization

The current SmartBI CLI is installed, but its online health check found no credentials in this terminal. After credentials are available through environment variables, use the CLI only to discover and export the read-only report named `投放小红书链路指标-素材维度`.

The supplied Xiaohongshu advertising authorization URL is recorded as a template only. Do not open it until the callback service, official token exchange details, and secure credential storage are ready. The content loop does not call `ad_manage` endpoints.
