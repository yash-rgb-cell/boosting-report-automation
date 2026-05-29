# Sprinklr account profiles

What each account in the Sprinklr export typically posts. Use this for:

- Layer 3 disambiguation (account context as a tiebreaker, not decisive).
- Layer 4 account-history fallback (filter the 14-day window by Account first).
- Knowing which campaign hashtags to ignore.

## PV United States (FB, IG, TT, YT)

The main Prime Video US brand handle. Posts span the entire Prime Video catalog —
series and movies, originals and licensed. Visual-only meme-style posts are common,
especially on IG and TT. **Show-specific hashtags are usually present** when the post
is about a single title. Multi-title curated posts (e.g. "leading ladies of Prime
Video") show up here weekly.

Common campaign hashtags to ignore as show signals:
- `#ObsessionIsInSession`
- `#PrimeVideo`
- `#StreamOnPrimeVideo`
- `#OnlyOnPrimeVideo`
- `#TGIF` (and similar day-of-week tags)

## Prime Movies (FB, IG, TT, YT)

Movies only. Never series. Posts almost always include the title via the 🎥 emoji
+ "available to rent or buy" / "available with [subscription]" / "streaming now"
phrasing. **High Layer 3 hit rate.** Used heavily for catalog promo of licensed
films (Goodfellas, Rear Window, The Godfather, etc.).

If a Prime Movies post has no caption text but has a thumbnail, the title is
almost always baked into the thumbnail — Layer 5 (OCR) is highly effective here.

## Primero Latino (FB, IG, TT)

Spanish-language Prime Video content. Captions are in Spanish. When ambiguous,
prefer Spanish-language Prime Video titles (telenovelas, Spanish-language
originals, dubbed catalog) over English-language ones with the same theme.

## Culture Rated (FB, IG, TT)

Black-culture focused content. When multiple titles in the known list could
plausibly fit, use Culture Rated context as a tiebreaker — prefer the title
that aligns with the account's editorial focus.

## Account-history fallback (Layer 4) — how to apply

Group the memory bank by Account. For each account, take the last 14 days of
tagged posts. Compute the share of the most frequent title.

- If share > 60% → suggest that title as `low` confidence.
- If share ≤ 60% → fall through to Layer 5 (or human queue if Layer 5 unavailable).

The 60% threshold is conservative on purpose. Lowering it inflates the
false-positive rate, which pollutes the memory bank if the analyst rubber-stamps.

## When account context misleads

Two known failure modes:

1. **Cross-account reshares.** Sometimes Culture Rated reshares a PV United States
   post about a non-Black-culture show. Account history is misleading in this case —
   prefer `N/A` over a `low` guess if the caption clearly doesn't fit the account's
   typical content.

2. **New show launch weeks.** When a new show launches, an account may post 8 in
   a row about it, then return to its usual mix. Layer 4 will keep suggesting the
   launch show for ~10 days after the launch tapers. The analyst's eyeball catches
   this; the memory bank gate prevents it from sticking.
