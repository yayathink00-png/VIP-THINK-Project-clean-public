# Xiaohongshu Fast MVP

## One-Line Goal

Build a lightweight Xiaohongshu content factory for an online education brand:
generate 10 draft posts per day, auto-mark risk, manually pick 3 to publish.

## Brand Assumption

- Category: online education
- Audience: parents of children aged 4-12
- Direction: math thinking, coding enlightenment, learning habits, parent education
- Conversion action: comment keyword, private message, trial lesson, learning material

## Fastest Workflow

```text
Competitor ideas
  -> AI generates 10 drafts
  -> AI marks risk level
  -> Human picks 3
  -> Publish manually
  -> Record performance next day
```

## Daily Work

| Step | Owner | Time | Output |
|---|---:|---:|---|
| Paste daily prompt | human | 2 min | 10 drafts |
| Pick publishable drafts | human | 5 min | 3 posts |
| Light edit | human | 5-10 min | safer wording |
| Publish | human | 5 min | 3 notes |
| Record data next day | human | 5 min | performance feedback |

Target human time: 15-25 minutes per day.

## Competitor Seeds

Start with:

- 火花思维
- 豌豆思维
- Mathplore
- 叫叫思维 / 叫叫阅读
- 核桃编程
- 编程猫
- 学而思
- 小码王

Use them for topic ideas only. Do not copy full text or images.

## Content Types

Use only these 5 types in v1:

1. Parent pain point
2. Learning method
3. Mistake correction
4. Case-style story
5. Free material / trial lesson conversion

## Risk Rules

Green: can publish after quick glance.

- Learning method
- Parent mistake correction
- General study habit tips
- No exact performance promise
- No named child details

Yellow: review carefully.

- Strong conversion CTA
- Before/after story
- Mentions age-specific outcome
- Mentions competitor category

Red: do not publish.

- "Guaranteed improvement"
- "100% effective"
- "Visible result in X days"
- Attacks a competitor
- Uses real child identity without consent
- Pushes users off platform too directly

## First Week Plan

Day 1:
- Use `xhs_batch_01.md`.
- Pick 3 green/yellow-low-risk drafts.
- Publish manually.

Day 2:
- Use `xhs_daily_generation_prompt.md`.
- Generate batch 02.
- Keep the best 10 drafts.

Day 3-7:
- Repeat.
- Record data in a simple sheet:
  - date
  - title
  - content type
  - publish time
  - views
  - likes
  - saves
  - comments
  - private messages
  - next action

## Do Not Build Yet

Skip these until posts are already working:

- Full backend
- Full auto-publish
- Complex dashboard
- Multi-agent workflow
- Automated image generation pipeline
- Large database

The fastest useful version is a daily draft generator plus risk gate.
