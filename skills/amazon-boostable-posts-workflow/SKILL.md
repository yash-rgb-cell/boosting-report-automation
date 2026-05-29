---
name: amazon-boostable-posts-workflow
description: >
  Walks the LF analyst through the daily Amazon Prime Video Boostable Posts report,
  end to end. Use this skill when the user says "run the boostable posts report",
  "help with today's Amazon report", "Amazon PV daily", "process today's Sprinklr
  export", or asks how to do any stage of the report. Covers Stages 1–6 (Mon–Fri).
  For the Friday-only 90-day benchmark refresh, defer to the sister skill
  amazon-friday-90day-refresh. For the title-tagging step in Stage 4, defer to
  amazon-title-tagging.
metadata:
  type: workflow
  domain: amazon-prime-video
  owner: LF analyst team
---

# amazon-boostable-posts-workflow

## When to run

The analyst has a Sprinklr daily export ready (or is about to pull one) and needs
to produce today's Boostable Posts deliverable for Amazon. Expected runtime with
this skill: 5–15 minutes of analyst time (vs. 30–90 minutes unaided).

## What this skill does

This is a **workflow walkthrough** — it tells the analyst (or Claude on the
analyst's behalf) exactly what to do at each stage, in order, with the column
references and guardrails baked in. It does **not** replace the Apps Script that
lives inside the Google Sheet — when the Apps Script is healthy, prefer the menu
items it provides. This skill is the fallback / onboarding / ad-hoc helper.

## Files the analyst will touch

Located inside `amazon-boostable-posts/` in the user's workspace:

- `internal/[2026 V2] LF _ Amazon - Boostable Posts [INTERNAL].xlsx` — the 8-tab
  working spreadsheet (Topline, Daily Post Export, Benchmarking + Labeling,
  90 Day Benchmark Export, Todays Organic Performance, Todays Boosted Performance,
  For Insights, Historical tags). **Internal only — never sent to client.**
- `client-sharable/LF _ Amazon - Boostable Posts [TEMPLATE].xlsx` — the single-tab
  Today's Performance file. **This is what goes to Amazon.** Rename with today's
  date before sending.
- `inputs-archive/` — drop each day's Sprinklr export here, renamed to
  `Daily Post Export - [YYYY-MM-DD].xlsx`.

## The 7 stages, in order

### Stage 1 — Sprinklr export
1. Open Sprinklr → `[GG] - LF | Recurring Reporting` dashboard.
2. Set date range to **the prior 7 days** (do NOT include today).
3. Apply the `[LF] Boostable Assets Filter`. If missing, build it manually:
   - Culture Rated → FB, IG, TT
   - Primero Latino → FB, IG, TT
   - Prime Movies → FB, IG, TT, YT
   - PV United States → FB, IG, TT, YT
   - **Exclude** LinkedIn, X, Threads.
4. Export the widget **"Boostable Posts Report - DAILY POST EXPORT TAB"** as Excel.
5. Save into `inputs-archive/` and rename: `Daily Post Export - [YYYY-MM-DD].xlsx`.

Output shape: 17 columns; header on row 2; data from row 3.

### Stage 2 — Clean the export
1. Sort by `Total Engagements` (col N) descending.
2. **Delete every row with 0 engagements.**
3. Sort by `Permalink` (col G). Duplicates cluster together — Sprinklr emits one
   row per Sprinklr-tag, so a multi-tagged post appears multiple times.
4. For each cluster: keep one row, set its `PV_Titles` (col K) to `Multi-Title`,
   delete the rest.

**Critical guardrail:** dedupe **by Permalink, never by engagement count.** Two
different posts can have identical engagement counts by coincidence — deduping
on engagement would delete legitimate distinct posts.

### Stage 3 — Paste into the internal sheet
1. Open `internal/[2026 V2] LF _ Amazon - Boostable Posts [INTERNAL].xlsx`.
2. Go to `Daily Post Export` tab.
3. Paste cleaned export rows starting at **column L**, under the previous day.
4. Stamp **today's date** (the reporting date, NOT the post's publish date) into
   column A for every new row.
5. Columns B–K auto-populate via the sheet's formulas. If new rows extend past the
   existing formula range, copy B–K formulas down to cover them.

### Stage 4 — Tag missing titles
This is the long stage. **Defer to the `amazon-title-tagging` skill.**

Quick recap of the flow:
1. Column B in `Daily Post Export` is blank for posts not yet in the memory bank.
2. Those URLs surface in column E of `Benchmarking + Labeling`.
3. For each, assign a tag in column F using:
   - the hashtag list in column G
   - the text preview in column H
   - the rules in `amazon-title-tagging/references/tag_rules.md`
4. Special cases: multi-show → `Multi-Title`; nothing identifiable → `N/A`.
5. Once verified, copy `E:F` values into the memory bank table at `B:C`.
6. Clear column F. **Never touch the formulas in E, G, H.**

### Stage 5 — Set Topline reporting date
1. Go to the `Topline` tab.
2. Double-click cell **D3** and set it to today's date.
3. All downstream formulas refresh: Topline's overperformer table, Today's
   Performance dates and post list.

### Stage 6 — Build client-facing deliverable
1. In the internal sheet, select the entire `Todays Organic Performance` tab
   (Ctrl/Cmd + A).
2. Paste into the client-facing sheet's `Todays Performance` tab as **values only**
   (this strips formulas).
3. Re-copy the post link column normally so hyperlinks survive (paste-special
   destroys them — this is a known quirk).
4. Save-as a new copy named `LF | Amazon - Boostable Posts [MM.DD.YY].xlsx`.
5. Download as `.xlsx` if working in Sheets.

### Stage 7 — Email & sign off
Email setup:
- **To:** `pvs-boosting-team@amazon.com`
- **Cc:** `Amazon MGM Studios Streaming <team-amazonstreaming@listenfirstmedia.com>`,
  `douglbos@amazon.com`, `PVSBrand-Social@amazon.com`
- **Subject:** `Prime Video | Boostable Posts (WEEKDAY, DATE)`
- **Body:**

  ```
  Good morning,

  Please see the attached post list for consideration for boosting, and a summary
  of what's overperforming below:

  [Insert the post table from the TOPLINE TAB, starting at B11]

  Please reach out with any questions.

  Best,
  [Name]
  ```

- **Attachment:** the client-facing `.xlsx` from Stage 6.

Then mark the Asana task complete.

## Friday-only addendum

If today is Friday, also run the `amazon-friday-90day-refresh` skill **before**
Stage 5. This rebuilds the J9:M21 benchmarks in `Benchmarking + Labeling`, which
the overperformer table on Topline depends on.

## Common ways this goes wrong (and how to spot them)

- **Today's date snuck into the Sprinklr export.** Stage 1 says "prior 7 days,
  do not include today." If today's date appears in the publish-date column,
  the filter was wrong. Re-run Stage 1.
- **Duplicate posts survived dedup.** Stage 2 says dedupe by Permalink. If the
  client-facing sheet shows the same URL twice, the analyst sorted by engagement
  by mistake and missed a duplicate cluster.
- **Auto-applied tag is wrong.** Means a bad URL → tag pair entered the memory
  bank previously. Fix at the source: edit columns B:C in `Benchmarking + Labeling`
  for that URL. Don't paper over it on the daily export.
- **Topline date wasn't updated.** The client sheet will show last week's posts.
  Always set D3 before building the client deliverable.
- **Paste-special killed the hyperlinks.** Re-copy the post link column normally
  after the values paste.

## Editing the files from this skill

The analyst can ask Claude with this skill loaded to:

- "Update the client template with today's data from `inputs-archive/[date].xlsx`"
- "Stamp today's date on column A for new rows in the Daily Post Export"
- "Build today's client sheet from the internal one"

Claude will use Python (openpyxl) against the files in the workspace folder. The
internal sheet's Google-Sheets-only formulas (REGEXMATCH, ARRAYFORMULA) will not
recompute when edited in Excel — treat the Google Sheet as the source of truth
and use these local edits only for one-off fixes or template updates.

## See also

- `amazon-title-tagging` — Stage 4 detail
- `amazon-friday-90day-refresh` — Friday's benchmark refresh
- `../../client-sharable/` — the file that goes to Amazon
- `../../internal/` — the 8-tab working sheet (internal only)
