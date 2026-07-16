# FB New Material Broadcast

This toolset generates a read-only Meta Ads broadcast for newly launched or scheduled FB ads.

## Files

- `tools/fb_new_creative_broadcast.py`: pulls Meta Ads data and stores a local SQLite history.
- `tools/fb_robot_broadcast.py`: builds and sends the DingTalk/Feishu/WeCom robot broadcast from the local history.
- `tools/daily_fb_new_creative_broadcast.py`: daily runner for the current broadcast rule.
- `tools/export_fb_material_sla_lists.py`: exports material-level SLA lists.
- `tools/export_unlaunched_image_materials.py`: compares finalized image materials with Meta ad records.

## Current Broadcast Rule

The daily broadcast separates the ad action window from the material window.

- Ad rule: count ads newly created in the report window, or ads whose ad set scheduled start time is in the report window.
- Material rule: the material must be counted by its first launch or schedule action. Later copied ads, additional ad sets, or repeated launches for the same material are not counted again.
- Material date rule: only materials whose production/final date is within 7 days ending at the report end date are included.
- Image rule: images use the final approval date from the image material library when available.
- Video rule: videos use the date parsed from the file name or ad name.

For example, for a report window of `2026-07-14`:

- ad action date: `2026-07-14`
- material date range: `2026-07-08` to `2026-07-14`
- only materials whose first launch/schedule action falls on `2026-07-14` are counted.

## Daily Window

- Monday: report last Friday through Sunday.
- Other days: report the previous day.

## Dry Run

```bash
cd /path/to/repo
python3 tools/fb_robot_broadcast.py \
  --since 2026-07-14 \
  --until 2026-07-14 \
  --account-aliases 7,8,9,27,18,23 \
  --material-lookback-days 7 \
  --max-lines 0 \
  --dry-run
```

## Send

Configure `.env` from `.env.example`, then run without `--dry-run`:

```bash
python3 tools/fb_robot_broadcast.py \
  --since 2026-07-14 \
  --until 2026-07-14 \
  --account-aliases 7,8,9,27,18,23 \
  --material-lookback-days 7 \
  --max-lines 0
```

The scripts are read-only for Meta Ads. They do not create, edit, pause, or delete ads.
