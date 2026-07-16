# High-Quality Content Automation Plan

## Goal

The goal is not "generate many Xiaohongshu posts".

The goal is:

```text
Generate fewer but stronger post candidates that a parent would save, comment on,
or use immediately.
```

## Quality Bar

A post is high quality only if it passes these checks:

1. Specific parent scene
   - Good: "孩子上课听懂了，回家做题还是卡住"
   - Bad: "孩子学习不好怎么办"

2. Actionable method
   - Good: "先圈条件，再复述题目，最后说第一步"
   - Bad: "家长要多鼓励孩子"

3. Save value
   - The reader should want to save it for homework, parent-child practice, or course selection.

4. Clear carousel flow
   - Page 1: hook
   - Page 2: specific pain
   - Page 3: hidden reason
   - Page 4: method
   - Page 5: example
   - Page 6: checklist / CTA

5. Low compliance risk
   - No guaranteed outcome.
   - No exact improvement promise.
   - No competitor attack.
   - No real child identity.

## Automation Strategy

Do not fully automate publishing first.

Automate these:

- topic generation
- title generation
- cover copy
- carousel script
- caption
- hashtag
- quality score
- risk score
- publish recommendation

Keep human review for:

- yellow-risk posts
- conversion posts
- case-story posts
- any post mentioning performance outcome

## Daily Workflow

```bash
cd /Users/yangyi/Documents/xiaohongshu-投放
python3 xhs_auto_generator.py --count 10
```

Then open:

- `outputs/latest.md`
- `outputs/latest.csv`

Only publish:

- quality_score >= 78
- risk_level = green
- publish_recommendation = publish

Review manually:

- quality_score 65-77
- risk_level = yellow
- publish_recommendation = review

Reject:

- quality_score < 65
- risk_level = red
- publish_recommendation = reject

## What To Optimize First

1. Raise topic quality.
2. Raise cover quality.
3. Raise carousel usefulness.
4. Then improve visual design.
5. Last, consider auto-publish.

High-quality content depends more on topic and structure than on automation depth.
