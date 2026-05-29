---
name: amazon-boostable-posts
description: >
  End-to-end skill for the Amazon Prime Video Boostable Posts daily report.
  Covers the full Mon–Fri workflow (Sprinklr export → clean → import → tag
  missing titles → set Topline date → build client sheet → draft email), the
  Friday-only 90-day benchmark refresh, and the title-tagging logic with the
  full 6-layer fallback stack (Sprinklr PV_Titles → memory bank URL match →
  caption LLM → account-history → thumbnail OCR → human queue). Triggers on
  any of: "run the boostable posts report", "Amazon PV daily", "tag these
  posts", "suggest title tags", "Friday refresh", "refresh 90-day benchmarks",
  "process the Sprinklr export", "build today's client sheet", "draft the
  Amazon boosting email", "what's the title tag for", "PV_Titles",
  "Benchmarking + Labeling", "missing tags". Also activates when the user
  uploads a Sprinklr boostable-posts export with or without a memory bank file.
metadata:
  type: workflow
  domain: amazon-prime-video
  owner: LF analyst team
---

# amazon-boostable-posts

End-to-end skill for the LF Analyst → Amazon Prime Video daily Boostable Posts
deliverable. Three workflows live here:

1. **Daily workflow** (Mon–Fri) — 7 stages, the main thing.
2. **Title tagging** — Stage 4 of the daily workflow, also runs standalone.
3. **Friday 90-day refresh** — extra step that slots in between Stage 4 and 5
   on Fridays.

## Files the analyst will touch

Located inside `amazon-boostable-posts/` in the workspace:

- `internal/[2026 V2] LF _ Amazon - Boostable Posts [INTERNAL].xlsx` — the
  8-tab working spreadsheet (Topline, Daily Post Export, Benchmarking + Labeling,
  90 Day Benchmark Export, Todays Organic Performance, Todays Boosted Performance,
  For Insights, Historical tags). **Internal only — never sent to client.**
- `client-sharable/LF _ Amazon - Boostable Posts [TEMPLATE].xlsx` — the
  single-tab Today's Performance file. **This is what goes to Amazon.** Rename
  with today's date before sending.
- `inputs-archive/` — drop each day's Sprinklr export here, renamed to
  `Daily Post Export - [YYYY-MM-DD].xlsx`.

## Inputs the team provides

**Every weekday:**

1. **Sprinklr daily export** (`.xlsx`)
   - Pulled from `[GG] - LF | Recurring Reporting` dashboard
   - Date range: prior 7 days (NOT including today)
   - Widget: `Boostable Posts Report - DAILY POST EXPORT TAB`
   - 17 columns; header on row 3; data from row 4
   - Columns the skill cares about: A=caption (Outbound Post), C=Account,
     G=Permalink, J=Tags, K=PV_Titles, N=Total Engagements,
     Q=Total Paid Engagements

2. **Memory bank** (`.csv` or `.xlsx`)
   - Exported from the `Benchmarking + Labeling` tab
   - Three columns: A=Publish Date, B=Post Link, C=Title Tag
   - Canonical URL → tag lookup AND the source of the known-title list
   - If missing, the skill **stops and asks for it** — without it the tagger
     would invent tags.

**Friday only — one additional file:**

3. **Sprinklr 90-day benchmark export** (`.xlsx`)
   - Same dashboard, date range = prior 90 days
   - Widget: `Boostable Posts Report - 90 DAY BENCHMARK TAB`
   - 12 columns; header on row 3
   - Stored in `inputs-archive/`, named `90 Day Benchmark - [date range].xlsx`

## Client deliverables — what goes to Amazon

Two things, in a single email sent ~12 PM EST:

1. **Attached Excel** `LF | Amazon - Boostable Posts [MM.DD.YY].xlsx` — single
   tab `Todays Performance` with the data table at row 11:
   `Brand | Title | Publish Date | Channel | Post Type | Text | Engagements |
   ER | Benchmark Δ | Pacing`. Organic only (paid excluded via the "-" rule).
   Sorted by Benchmark Δ descending.

2. **Email body** with the Topline overperformer table:
   - To: `pvs-boosting-team@amazon.com`
   - Cc: `team-amazonstreaming@listenfirstmedia.com`, `douglbos@amazon.com`,
     `PVSBrand-Social@amazon.com`
   - Subject: `Prime Video | Boostable Posts (WEEKDAY, DATE)`
   - Body: short greeting + Topline table (Brand | Title | Channel |
     Engagements | ER | Benchmark Δ) + signoff

---

# Daily workflow — the 7 stages

Run in strict order. Each stage depends on the previous one's output.

### Stage 1 — Sprinklr export
1. Open Sprinklr → `[GG] - LF | Recurring Reporting` dashboard.
2. Set date range to **the prior 7 days** (do NOT include today).
3. Apply the `[LF] Boostable Assets Filter`. If missing, build it manually:
   - Culture Rated → FB, IG, TT
   - Primero Latino → FB, IG, TT
   - Prime Movies → FB, IG, TT, YT
   - PV United States → FB, IG, TT, YT
   - **Exclude** LinkedIn, X, Threads.
4. Export the widget **"Boostable Posts Report - DAILY POST EXPORT TAB"** as
   Excel.
5. Save into `inputs-archive/`, renamed `Daily Post Export - [YYYY-MM-DD].xlsx`.

### Stage 2 — Clean
1. Sort by `Total Engagements` (col N) descending.
2. **Delete every row with 0 engagements.**
3. Sort by `Permalink` (col G). Duplicates cluster together — Sprinklr emits
   one row per Sprinklr-tag, so a multi-tagged post appears multiple times.
4. For each cluster: keep one row, set its `PV_Titles` (col K) to
   `Multi-Title`, delete the rest.

**Critical guardrail:** dedupe **by Permalink, never by engagement count.**
Two different posts can have identical engagement counts by coincidence —
deduping on engagement would delete legitimate distinct posts.

### Stage 3 — Paste into internal sheet
1. Open `internal/[2026 V2] LF _ Amazon - Boostable Posts [INTERNAL].xlsx`.
2. Go to `Daily Post Export` tab.
3. Paste cleaned export rows starting at **column L**, under the previous day.
4. Stamp **today's date** (the reporting date, NOT the post's publish date)
   into column A for every new row.
5. Columns B–K auto-populate via the sheet's formulas. Extend formulas if
   new rows exceed the existing range.

### Stage 4 — Tag missing titles

Use the 6-layer fallback stack (see "Title tagging" section below for full
detail). The short version:

1. Column B in `Daily Post Export` is blank for posts not yet in the memory bank.
2. Those URLs surface in column E of `Benchmarking + Labeling`.
3. Run `scripts/process_export.py` to get suggested tags as a CSV:
   ```
   python scripts/process_export.py \
     --export /path/to/Daily Post Export - [date].xlsx \
     --memory-bank /path/to/memory_bank.csv \
     --output ./suggested_tags.csv \
     [--thumbnails-ocr] \
     [--prompts-out ./layer3_prompts.jsonl]
   ```
4. Review the output. Paste verified tags into column F of
   `Benchmarking + Labeling`.
5. Copy column E:F values into the memory bank at columns B:C.
6. Clear column F. **Never touch the formulas in E, G, H.**

### Stage 5 — Set Topline reporting date
1. Go to the `Topline` tab.
2. Double-click cell **D3** and set it to today's date.
3. All downstream formulas refresh: Topline's overperformer table at B11,
   Today's Performance dates and post list.

## Persistent benchmark state (no more re-uploading)

The skill maintains its own benchmark state on disk so you never need to
re-upload the J9:M21 table. State files live in `state/` under the workspace:

- `state/post_log.csv` — append-only log of all organic posts ever seen
  (deduped by Permalink, latest engagement wins because engagements grow
  over time on the same post)
- `state/benchmarks.csv` — current per-(Brand × Channel) benchmark with a
  `refreshed_at` column so you can tell how fresh the values are
- `state/benchmarks_history/benchmarks_YYYY-MM-DD.csv` — daily snapshots
  before each overwrite, for audit

### How updates happen

**Daily nudge (default):** every run with `--auto-refresh-benchmarks` ingests
that day's organic posts into the log, dedupes by Permalink, then recomputes
benchmarks as the 90-day rolling mean. Benchmark drift is gradual and
self-correcting.

**Friday refresh (authoritative):** point `update_benchmark_state.py` at the
90-day Sprinklr export with `--replace-log` to wipe and rebuild the log from
scratch. This is the canonical reset and matches the analyst's Friday step.

```bash
# Friday — replace the log from the 90-day export
python scripts/update_benchmark_state.py \
  --90day-export inputs-archive/90\ Day\ Benchmark\ -\ [range].xlsx \
  --state-dir state/ \
  --replace-log
```

### Bootstrap

On first install, drop a 90-day Sprinklr export into `inputs-archive/` and
run the `--replace-log` command above. This gives the skill a real 90-day
window from day one. Without bootstrap, the skill will use the hardcoded
default benchmarks for the first 7 days, then progressively self-correct as
the post log fills up.

---

### Stage 6 — Build client-facing deliverable

Run `scripts/build_client_sheet.py` to produce the deliverable directly. It
mirrors the real client-file layout exactly (banner rows, benchmark
descriptors, header at row 11, organic-only data sorted by Benchmark Δ,
hyperlinks on the Channel cell, ER as percentage, date-only Publish Date).

```bash
python scripts/build_client_sheet.py \
  --export   "inputs-archive/Daily Post Export - [YYYY-MM-DD].xlsx" \
  --memory-bank   "/path/to/memory_bank.csv" \
  --reporting-date 2026-05-26 \
  --output   "client-sharable/LF _ Amazon - Boostable Posts [MM.DD.YY].xlsx" \
  --state-dir state/ \
  --auto-refresh-benchmarks
```

`--auto-refresh-benchmarks` updates `state/benchmarks.csv` from today's export
before the deliverable is built. Skip it on days you want to use the existing
stored benchmarks unchanged. `--state-dir` points at the state folder
(defaults to `state/` near the export).

### Untagged-post highlighting (two files per run)

Every run produces **two** Excel files instead of one:

1. **`LF _ Amazon - Boostable Posts [DATE].xlsx`** — the CLIENT file.
   Clean, no highlights, blank titles replaced with `N/A`. Safe to attach to
   the Amazon email as-is.

2. **`LF _ Amazon - Boostable Posts [DATE]_review.xlsx`** — the INTERNAL
   review file. Identical layout, but any row whose tag is blank, `N/A`, or
   a provisional `NEW:` tag gets **yellow-highlighted** on the Brand + Title
   cells, with `(needs-review)` text where the title would be blank.

3. **`needs-review-[DATE].csv`** — the worklist (only emitted when at least
   one row needs attention). Five columns: Post Link, Brand, Channel,
   Caption Preview, Suggested Tag. The analyst uses this as a to-do list:
   open each link, decide the tag, add to memory bank, re-run.

The console summary tells you the count:

```
✓  All rows tagged. No review needed.
```

or:

```
⚠  4 rows need review before sending to client.
   Open the _review.xlsx, tag the yellow rows, add to memory bank, re-run.
```

**Recommended workflow:** open the `_review.xlsx`, scan for yellow cells,
fix any wrong-looking tags by adding the correct URL → tag pair to the
memory bank, then re-run the build. On the second pass the `_review.xlsx`
should have no highlights and you can confidently send the CLIENT file.

If working in Google Sheets manually instead:
1. In the internal sheet, select the entire `Todays Organic Performance` tab.
2. Paste into the client-facing sheet's `Todays Performance` tab as **values
   only** (strips formulas).
3. Re-copy the post link column normally so hyperlinks survive (paste-special
   destroys them — known quirk).
4. Save-as `LF | Amazon - Boostable Posts [MM.DD.YY].xlsx`.

### Stage 7 — Email & sign off

Construct the email exactly per the "Client deliverables" section above.
Mark the Asana task complete.

### Friday-only addendum
If today is Friday, run the 90-day refresh (section below) **between Stages 4
and 5** so the J9:M21 benchmarks are current before Topline rebuilds.

---

# Title tagging — 6-layer fallback stack

For each post in the daily export, apply these layers in order. **Stop at the
first layer that produces a confident tag.**

### Layer 1 — Sprinklr's own tag (PV_Titles column)
If column K is non-empty, take that value. Confidence: `sprinklr`. Expected
hit rate: ~83%. Zero LLM calls. Always run first.

### Layer 2 — Memory bank exact-URL match
Look up the permalink in the memory bank. If found, use its tag.
Confidence: `memory`. Zero LLM calls.

### Layer 3 — LLM tag suggestion from caption + signals
Send Claude the prompt below with: caption, hashtags, account, URL slug, and
the full known-title list from the memory bank. Claude returns one of: a tag
from the known list, `Multi-Title`, `N/A`, or `NEW:<show name>`.
Confidence: `high` (or `review` for `NEW:` / `N/A`).

```
You are tagging Prime Video social media posts with the show or movie title
they reference. Tags feed the Amazon boostable-posts report and become a
permanent lookup once committed, so accuracy matters more than coverage.

## Inputs for this post
Caption: <CAPTION>
Hashtags: <COMMA_SEPARATED_HASHTAGS>
Account: <ACCOUNT_NAME>
URL: <PERMALINK>
URL slug: <LAST_PATH_SEGMENT_OF_URL>

## Known titles (pick from this list — do not invent variations)
<KNOWN_TITLE_LIST_NEWLINE_SEPARATED>

## Rules
1. If the caption or hashtags clearly reference one show on the known list,
   return that exact tag (case-sensitive, exact spelling).
2. If two or more distinct shows are referenced, return exactly: Multi-Title
3. If the caption references a real show NOT on the known list, return:
   NEW:<show name>
4. If nothing identifiable — generic caption, no show name, no telling
   hashtag, no slug hint — return exactly: N/A
5. Account context matters but is not decisive on its own (see references/
   accounts.md).
6. Hashtags like #ObsessionIsInSession, #PrimeVideo, #StreamOnPrimeVideo are
   campaign tags — ignore them. Show-specific hashtags (#OffCampus,
   #WhiteChicks, #TheBoys) are decisive.
7. URL slugs sometimes contain the show name. Tiebreaker only.
8. Never invent a title outside the known list without the NEW: prefix.

## Output format
Return ONLY the tag on a single line. No explanation, no punctuation, no
quotes. Examples:
Off Campus
The Boys
Multi-Title
N/A
NEW:Mr. and Mrs. Smith Season 2
```

### Layer 4 — Account-history fallback
Only runs when Layer 3 returns `N/A`. For the same account, look at the last
14 days of tagged posts in the memory bank. If a single title dominates
(>60% of recent posts), suggest it. Confidence: `low` — human must eyeball.

### Layer 5 — Video thumbnail OCR (optional)
Runs when Layers 3 and 4 fail AND the export contains a media/thumbnail URL.
`scripts/thumbnail_ocr.py` pulls each thumbnail, runs Tesseract OCR, and
matches the detected text against the known-title list (case-insensitive
substring match; longest match wins). Confidence: `ocr` — human still reviews.

Show names are commonly baked into the end frame / cover of IG Reels and
TikTok videos, so this catches the visual-only posts Layer 3 can't read.

### Layer 6 — Human queue
Anything still unresolved → `needs-human-review` list at the end of the
output. Each row carries URL, caption, account, and reason. Expected daily
queue: 0–5 posts.

### Confidence labels in the output CSV

| Label | Source | What the analyst does |
|---|---|---|
| `sprinklr` | Layer 1 | Paste as-is |
| `memory` | Layer 2 | Paste as-is |
| `high` | Layer 3 LLM | Quick scan, then paste |
| `low` | Layer 4 account-history | Eyeball before pasting |
| `ocr` | Layer 5 thumbnail OCR | Eyeball before pasting |
| `review` | `NEW:` or `N/A` | Definitely needs human attention |

### Rules the analyst should never break
1. **Never paste `review`-confidence tags into the memory bank without
   verifying.** A bad URL → tag pair propagates forever.
2. **Always run Layer 1 first.** It's free and accurate.
3. **Never invent a title outside the known list without the `NEW:` prefix.**
4. **The skill cannot watch the video.** It reads text and (optionally)
   thumbnail OCR. Visual-only posts will return `N/A` — that's expected,
   not a bug.

---

# Friday 90-day benchmark refresh

Friday only. Runs **between Stage 4 and Stage 5** of the daily workflow.

### Step 1 — Sprinklr export
1. Same dashboard, date range = **prior 90 days** (NOT including today).
2. Same filter set as daily.
3. Export widget **"Boostable Posts Report - 90 DAY BENCHMARK TAB"**.
4. Save into `inputs-archive/`, renamed
   `90 Day Benchmark - [YYYY-MM-DD]_to_[YYYY-MM-DD].xlsx`.

### Step 2 — Clean
Sort by `PV_UCM_Total Engagements (SUM)` (col K) descending. Delete 0-engagement
rows. **No dedup needed** — the 90-day widget comes pre-deduped.

### Step 3 — Replace data in the internal sheet
1. Open the internal sheet → `90 Day Benchmark Export - Frida` tab.
2. **Delete all existing data from column D onward** (keep formulas in A:C).
3. Paste the cleaned export starting at column D.
4. If A:C is blank for new rows past the original formula range, copy A:C
   from an intact row and paste-down across the blanks.

### Step 4 — Verify benchmarks refreshed
On `Benchmarking + Labeling`, the `J9:M21` table should now show updated
benchmark values per (brand × channel). These feed the Topline overperformer
table at B11.

### Step 5 — Continue with the daily workflow
Resume at **Stage 5** (set Topline D3).

### Common Friday failure modes
- **Wrong widget exported.** Daily widget = 17 columns; 90-day widget = 12.
  Check column count before pasting.
- **Deleted columns A:C by accident.** Copy from an intact row, paste-down.
- **Forgot to run this before Stage 5.** Topline shows stale benchmarks.
  Re-run, then re-set Topline D3.

---

# What can go wrong (cross-cutting)

- **Today's date snuck into the Sprinklr export.** Stage 1 says "prior 7 days,
  do not include today." If today appears in publish dates, the filter was
  wrong. Re-run Stage 1.
- **Duplicate posts survived dedup.** Stage 2 says dedupe by Permalink, not
  engagement. If the client sheet shows the same URL twice, re-do Stage 2.
- **Auto-applied tag is wrong.** A bad URL → tag pair entered the memory
  bank previously. Fix at the source: edit columns B:C in
  `Benchmarking + Labeling` for that URL. Don't paper over it on the daily.
- **Topline date wasn't updated.** Client sheet shows last week's posts.
  Always set D3 before building the client deliverable.
- **Paste-special killed hyperlinks.** Re-copy the post link column normally
  after the values paste.
- **Google-Sheets-only formulas don't recompute in Excel.** The internal
  sheet uses REGEXMATCH, ARRAYFORMULA, etc. Treat the Google Sheet as source
  of truth; use local Excel edits only for one-off fixes.

---

# Editing files via this skill

Ask Claude with this skill loaded to do things like:

- "Update the client template with today's data from
  `inputs-archive/[date].xlsx`"
- "Stamp today's date in column A for new rows in the Daily Post Export"
- "Build today's client sheet from the internal one"
- "Tag the posts in this Sprinklr export"
- "Refresh the 90-day benchmark data"
- "Draft today's email with the Topline overperformer table"

Claude will use Python (openpyxl) against the files in the workspace folder.

## See also

- `references/tag_rules.md` — Layer 3 prompt + worked examples by difficulty
- `references/accounts.md` — Sprinklr account profiles + Layer 4 thresholds
- `scripts/process_export.py` — runs the deterministic layers + queues Layer 3
- `scripts/thumbnail_ocr.py` — Layer 5 helper (requires Tesseract)
- `scripts/build_client_sheet.py` — builds the client-facing deliverable from
  the cleaned export, matching the real layout exactly (hyperlinks on Channel
  cell, ER as percentage, date-only Publish Date, multi-level benchmark
  fallback)
- `scripts/update_benchmark_state.py` — maintains the post log and
  recomputes per-(Brand × Channel) benchmarks. Called automatically by
  `build_client_sheet.py --auto-refresh-benchmarks`; can also be invoked
  directly with `--90day-export ... --replace-log` for the Friday reset.
- `scripts/draft_email.py` — produces the daily client email exactly matching
  Aaron's reference format (Brand | Title | Channel | Engagements | ER | Δ%,
  green-highlighted Δ cells, blue Channel hyperlinks). Writes `.html`,
  `.txt`, and `.eml` files in one go. The `.eml` opens directly in your
  default mail client with the deliverable attached and recipients filled in.

### Full daily run, one command per script

```bash
# 1. Build the deliverable (CLIENT + REVIEW + worklist)
python scripts/build_client_sheet.py \
  --export "inputs-archive/Daily Post Export - 2026-05-26.xlsx" \
  --memory-bank memory_bank.csv \
  --reporting-date 2026-05-26 \
  --output "client-sharable/LF _ Amazon - Boostable Posts [05.26.26].xlsx" \
  --state-dir state/ \
  --auto-refresh-benchmarks

# 2. Draft the email
python scripts/draft_email.py \
  --export "inputs-archive/Daily Post Export - 2026-05-26.xlsx" \
  --memory-bank memory_bank.csv \
  --client-xlsx "client-sharable/LF _ Amazon - Boostable Posts [05.26.26].xlsx" \
  --reporting-date 2026-05-26 \
  --output "client-sharable/email_draft_2026-05-26" \
  --sender-name "Aaron" \
  --from-email aaron@listenfirstmedia.com \
  --state-dir state/
```

Double-click the resulting `.eml` to open it in your mail client with the
table pre-rendered and the Excel already attached.
- `../../client-sharable/` — files that go to Amazon
- `../../internal/` — the 8-tab working sheet (internal only)
