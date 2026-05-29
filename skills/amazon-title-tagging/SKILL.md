---
name: amazon-title-tagging
description: >
  Apply Prime Video title tags to a Sprinklr daily boostable-posts export. Use this skill
  whenever the user asks to tag posts, suggest title tags for URLs, label posts by show,
  or process a Sprinklr export for the Amazon Prime Video boostable posts report. Also
  triggers when the user uploads a Sprinklr daily-post export alongside a memory bank
  file (Benchmarking + Labeling tab), or mentions "title tags", "PV_Titles",
  "Benchmarking + Labeling", "missing tags", or "tag these posts". Always picks from the
  known title list — never invents new tags silently. Surfaces uncertain or new shows
  for human review.
metadata:
  type: workflow
  domain: amazon-prime-video
  owner: LF analyst team
---

# amazon-title-tagging

## When to run

The analyst is in Stage 4 of the daily Boostable Posts workflow. Sprinklr's `PV_Titles`
column covers ~83% of posts. The remaining ~17% land on the **Benchmarking + Labeling**
tab in column E with column F blank, and someone has to assign a Prime Video show title
to each one. This skill produces those tags.

The skill runs inside a Claude conversation. The analyst uploads two files and gets
back a CSV they paste into column F of the Benchmarking + Labeling tab.

## Required inputs

1. **Sprinklr daily export** (`.xlsx`)
   - 17 columns, header on row 2, data from row 3.
   - Columns the skill uses: A = caption (Outbound Post), C = Account, G = Permalink,
     J = Tags, K = PV_Titles, N = Total Engagements, Q = Total Paid Engagements.
   - There may also be a thumbnail / media URL column — the skill auto-detects this by
     column name (case-insensitive match against "media", "thumbnail", "image url").

2. **Memory bank export** (`.csv` or `.xlsx` from the Benchmarking + Labeling tab)
   - Three columns: A = Publish Date, B = Post Link, C = Title Tag.
   - This is the canonical URL → tag lookup AND the source of the known-title list.

If the memory bank is missing, **stop and ask** for it. Never proceed without the
known-title list — Claude will invent tags.

## Six-layer fallback stack

Apply these layers in order to each untagged post. **Stop at the first layer that
produces a confident tag.** Do not skip layers.

### Layer 1 — Sprinklr's own tag (PV_Titles column)
If column K is non-empty, take that value as the tag. Mark confidence `sprinklr`.
**Expected hit rate: ~83%.** Zero LLM calls. Always run first.

### Layer 2 — Memory bank exact-URL match
For each surviving post, look up the permalink in the memory bank (column B → column C).
If found, use the memory bank's tag. Mark confidence `memory`. Zero LLM calls.

### Layer 3 — LLM tag suggestion from caption + signals
For posts that survive layers 1 and 2, send Claude the prompt in `references/tag_rules.md`
with: caption, hashtags, account, URL slug, and the full known-title list extracted from
the memory bank. Claude returns one of: a tag from the known list, `Multi-Title`, `N/A`,
or `NEW:<show name>`. Mark confidence `high` (or `review` for `NEW:` / `N/A`).

### Layer 4 — Account-history fallback
Only run for posts where Layer 3 returned `N/A`. Check the same account's posts from
the last 14 days in the memory bank. If a single show dominates that account's recent
activity (>60% of posts), suggest it. Mark confidence `low` — the human must eyeball.

### Layer 5 — Video thumbnail OCR (NEW, optional)
Only run for posts where Layers 3 and 4 both failed AND the export contains a media /
thumbnail URL. Use `scripts/thumbnail_ocr.py` to pull the thumbnail and OCR any
on-screen text. If the OCR text contains a known title (case-insensitive contains-match),
suggest that title. Mark confidence `ocr`. The human still reviews — OCR can hallucinate.

**Why this is a separate layer:** show names are commonly baked into the last frame /
cover image of IG Reels and TikTok videos. This catches the visual-only posts that
Layer 3 can't read. It does not replace human review for ambiguous cases — it just
shrinks the pile.

### Layer 6 — Human queue
Anything still unresolved goes to a `needs-human-review` list at the end of the output.
Each row: URL, caption, account, reason. Expected: 0–5 posts per day.

## Running the skill

Two ways:

### A. End-to-end via the helper script (recommended)

```bash
python scripts/process_export.py \
  --export /path/to/DailyBoostablePostsAutomatedExport.xlsx \
  --memory-bank /path/to/memory_bank.csv \
  --thumbnails-ocr           # optional, enables Layer 5
  --output ./suggested_tags.csv
```

The script:
1. Parses the export and memory bank.
2. Runs Layers 1, 2, 4, 5 deterministically.
3. Emits one Claude-ready prompt per post that needs Layer 3.
4. Pastes Claude's responses back together with the deterministic results.
5. Writes a CSV: `Post Link,Suggested Tag,Confidence,Reason`.

### B. Manual, conversational

If the analyst wants to tag a handful of posts ad-hoc, paste the relevant rows into
chat and use the Layer 3 prompt from `references/tag_rules.md` directly.

## Output format

CSV the analyst pastes into column F of Benchmarking + Labeling:

```
Post Link,Suggested Tag,Confidence,Reason
https://www.tiktok.com/@primevideo/video/7641339515285638413,Off Campus,sprinklr,PV_Titles populated
https://www.instagram.com/p/DYZpl_Rlnko/,Rear Window,memory,exact URL match in memory bank
https://www.instagram.com/p/DYXYQXFFlzM/,Off Campus,high,#OffCampus hashtag
https://www.instagram.com/p/DY-abc-12/,Goodfellas,low,Prime Movies account history dominated by Goodfellas (last 14d)
https://www.instagram.com/p/DY-ocr-99/,The Boys,ocr,thumbnail text contained "THE BOYS"
https://www.instagram.com/p/DYabc1234/,NEW:Mr. and Mrs. Smith,review,not on known list — human verify
https://www.instagram.com/p/DYzzzz9999/,N/A,review,no identifiable show
```

**Confidence levels:**
- `sprinklr` — Layer 1, paste as-is
- `memory` — Layer 2, paste as-is
- `high` — Layer 3 LLM, paste after a quick scan
- `low` — Layer 4 account history, eyeball before pasting
- `ocr` — Layer 5 thumbnail OCR, eyeball before pasting
- `review` — `NEW:` or `N/A`, definitely needs human attention

## Rules the analyst should never break

1. **Never paste `review`-confidence tags into the memory bank without verifying.**
   A bad URL → tag pair in the memory bank propagates forever.
2. **Always run Layer 1 first.** It's free and accurate. Skipping it wastes API budget.
3. **Never invent a title outside the known list without the `NEW:` prefix.** Better
   to return `N/A` than guess wrong.
4. **The skill cannot watch the video.** It reads text and (optionally) thumbnail OCR.
   Visual-only posts will return `N/A` — that's expected, not a bug.

## See also

- `references/tag_rules.md` — the 8 rules with examples for the Layer 3 prompt.
- `references/accounts.md` — what each Sprinklr account typically posts.
- `scripts/process_export.py` — end-to-end runner.
- `scripts/thumbnail_ocr.py` — Layer 5 helper.
- Sister skills: `amazon-boostable-posts-workflow` (daily 7-stage workflow),
  `amazon-friday-90day-refresh` (Friday-only benchmark refresh).
