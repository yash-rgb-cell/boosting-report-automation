# Title-tagging rules (Layer 3 prompt + examples)

This is the prompt to send Claude for each post that survives Layers 1 and 2. Variables
in `<ANGLE_BRACKETS>` are substituted by `scripts/process_export.py` with the actual
values from the export.

## The prompt (copy verbatim)

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
   return that exact tag (case-sensitive, exact spelling from the list).
2. If two or more distinct shows on the known list are referenced, return
   exactly: Multi-Title
3. If the caption clearly references a real show that is NOT on the known
   list, return: NEW:<show name as best you can identify>
4. If nothing identifiable — generic caption, no show name, no telling
   hashtag, no slug hint — return exactly: N/A
5. Account context matters but is not decisive on its own. See accounts.md
   for what each account typically posts.
6. Hashtags like #ObsessionIsInSession, #PrimeVideo, #StreamOnPrimeVideo are
   campaign tags, not show tags — ignore them for title identification.
   Show-specific hashtags (#OffCampus, #WhiteChicks, #TheBoys) are decisive.
7. URL slugs sometimes contain the show name (especially YouTube and Facebook).
   Use this as a tiebreaker, not as primary evidence.
8. Never invent a title that isn't in the known list without the NEW: prefix.
   It is better to return N/A than to guess wrong.

## Output format
Return ONLY the tag on a single line. No explanation, no punctuation, no
quotes. Examples of valid outputs:
Off Campus
The Boys
Multi-Title
N/A
NEW:Mr. and Mrs. Smith Season 2
```

## Worked examples by difficulty

### Easy — hashtag-driven (Layer 3 should hit `high`)

| Caption | Account | Expected tag |
|---|---|---|
| They are everything we wanted and more #ObsessionIsInSession 📺: #OffCampus | PV United States - TT | Off Campus |
| Quite an appetite. 🎥: #WhiteChicks, available to rent or buy. | PV United States - TT | White Chicks |

The show-specific hashtag wins. Ignore the campaign hashtag (`#ObsessionIsInSession`).

### Medium — show named in caption, no hashtag

| Caption | Account | Expected tag |
|---|---|---|
| Perfect set-up. 🎥: Rear Window | Prime Movies - IG | Rear Window |
| Two rules. No exceptions. 🎥: Goodfellas | Prime Movies - IG | Goodfellas |

The 🎥/📺 emoji is a tell — the title typically follows it. Match against the known list.

### Hard — opaque short caption, Layer 3 returns `N/A`

| Caption | Account | Expected tag (Layer 4) |
|---|---|---|
| Some Wellsy wisdom | PV United States - IG | Off Campus |
| Family first. | Prime Movies - IG | The Godfather |
| Negotiations have begun | PV United States - IG | The Boys |

Layer 3 should return `N/A` for these. Layer 4 (account-history) should catch them as
`low` confidence based on the dominant recent show for that account. The analyst's
eyeball is the gate — if the guess looks wrong, override it before pasting to the
memory bank.

### Multi-Title

| Caption | Account | Expected tag |
|---|---|---|
| Elle walked so Hannah could run | PV United States - IG | Multi-Title |
| From one heartthrob to another | PV United States - IG | Multi-Title |

These reference two distinct shows obliquely. The trigger is when the caption is clearly
juxtaposing two characters/shows from the known list, even if neither is named explicitly.
In practice, this is rare — most multi-title posts are explicit (`Sydney Bristow x Joanna
Hannah` style references in PV United States curated content).

### NEW

| Caption | Account | Expected tag |
|---|---|---|
| Watch out for these two #MrAndMrsSmithSeason2 | PV United States - IG | NEW:Mr. and Mrs. Smith Season 2 |

Show is clearly named (in caption + hashtag), but the title is not yet on the known list.
Return with the `NEW:` prefix so the analyst can decide whether to add it to the
memory bank canon.

## Common Layer 3 failure modes

- **Over-confident match on the wrong show.** Two shows with overlapping cast or theme
  can confuse a one-shot read. Prefer `N/A` and let Layer 4 + human review handle it.
- **Treating a campaign hashtag as a show tag.** `#ObsessionIsInSession` is a campaign,
  not a show. The accounts.md file lists the known campaign hashtags to ignore.
- **Picking the closest-spelled known title for a typo.** Don't. If the caption says
  "Off-Campus" but the known list has "Off Campus", that's still a Layer 3 match. But
  if the caption says "Off Campas" (real typo), return the closest match — never
  invent a variant spelling.
