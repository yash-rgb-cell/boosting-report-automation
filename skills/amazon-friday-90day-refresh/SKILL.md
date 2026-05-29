---
name: amazon-friday-90day-refresh
description: >
  Friday-only refresh of the 90-day benchmark data for the Amazon Prime Video
  Boostable Posts report. Triggers when the user says "Friday refresh",
  "refresh 90-day benchmarks", "run the Friday step", "update the 90-day
  benchmark export", or mentions the "90 DAY BENCHMARK TAB" widget. Runs in
  addition to (not instead of) the daily workflow on Fridays. Has different
  inputs, widget, and date range from the daily workflow.
metadata:
  type: workflow
  domain: amazon-prime-video
  owner: LF analyst team
  cadence: weekly-friday
---

# amazon-friday-90day-refresh

## When to run

**Fridays only.** Run this BEFORE Stage 5 of the daily workflow so the
benchmark values (`J9:M21` on the `Benchmarking + Labeling` tab) refresh
before the Topline tab pulls them.

## Required input

A separate Sprinklr export for the 90-day benchmark widget. Drop it in
`inputs-archive/` named `90 Day Benchmark - [YYYY-MM-DD]_to_[YYYY-MM-DD].xlsx`.

Shape: 12 columns; header on row 2; data from row 3. The columns the workflow
cares about: `Permalink` (G), `PV_UCM_Total Engagements (SUM)` (K),
`PV_UCM_Total Paid Engagements (SUM)` (L).

## The five steps

### Step 1 — Sprinklr export
1. Same dashboard: `[GG] - LF | Recurring Reporting`.
2. Date range: **prior 90 days** (do NOT include today).
3. Same filter set as the daily workflow (Culture Rated, Primero Latino,
   Prime Movies, PV United States; no LinkedIn, X, Threads).
4. Export the widget **"Boostable Posts Report - 90 DAY BENCHMARK TAB"** as Excel.
5. Save into `inputs-archive/`, renamed as above.

### Step 2 — Clean
Sort by `PV_UCM_Total Engagements (SUM)` (col K) descending. Delete every
row with 0 engagements. **Unlike the daily workflow, duplicates do NOT need
handling here** — the 90-day export comes pre-deduped at the widget level.

### Step 3 — Replace data in the internal sheet
1. Open `internal/[2026 V2] LF _ Amazon - Boostable Posts [INTERNAL].xlsx`.
2. Go to the `90 Day Benchmark Export - Frida` tab.
3. **Delete all existing data from column D onward** (keep formulas in A:C).
4. Paste the cleaned export starting at column D.
5. Columns A:C auto-populate. If A:C is blank for new rows past the original
   formula range, select the cells where A:C populated, copy them, then
   paste-down across the blank rows.

### Step 4 — Verify benchmarks refreshed
On `Benchmarking + Labeling` tab, the `J9:M21` table should now show updated
benchmark values per (brand × channel). These feed the Topline tab's
overperformer table.

### Step 5 — Continue with the daily workflow
Resume at **Stage 5** (set Topline D3) of `amazon-boostable-posts-workflow`.
The benchmarks are now current.

## Common ways this goes wrong

- **Wrong widget exported.** The daily widget has 17 columns; the 90-day widget
  has 12. If your export has 17 columns, you exported the daily widget by
  mistake — re-export.
- **Deleted columns A:C by accident.** They contain the formulas. If you
  cleared them, copy from a row that's still intact and paste-down.
- **Forgot to run this before Stage 5.** The Topline overperformer table will
  show stale benchmarks. Re-run this skill, then re-set Topline D3 to today's
  date so dependent formulas refresh.

## Editing from this skill

Ask Claude with this skill loaded to:

- "Refresh 90-day benchmark data in the internal sheet from
  `inputs-archive/90 Day Benchmark - [date range].xlsx`"
- "Verify the J9:M21 benchmark table updated correctly"

Same caveat as the daily workflow skill: Google-Sheets-specific formulas
(REGEXMATCH, ARRAYFORMULA) will not recompute when edited locally in Excel.
For the live sheet, treat the Google Sheet as source of truth.

## See also

- `amazon-boostable-posts-workflow` — runs Mon–Fri; pauses for this skill on Fri.
- `amazon-title-tagging` — Stage 4 of the daily workflow.
