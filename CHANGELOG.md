# Changelog

Record of every change made to the dashboard, kept so the local codebase
(zip) can be regenerated with everything included whenever it's next
requested, without re-deriving these from scratch.

This file is published alongside the dashboard as a second file in the
same artifact, specifically so it survives independently of any one
session's disk.

## 2026-10-07

- **New: CLI tool to manually merge two videos that the automatic matcher
  missed, `src/merge_videos_cli.py`.**
  - Run `python src/merge_videos_cli.py` and it lists every current group
    title with its total views, lets you pick two (by list number or by
    typing the title), asks which title the merged result should take
    (defaults to whichever of the two has more views), then merges them:
    combines their per-platform entries, sums the totals, and rebuilds
    `dist/dashboard.html` immediately so you can check the result.
  - Can also be run non-interactively for scripting:
    `python src/merge_videos_cli.py --a "Title One" --b "Title Two" --result "Title One"`.
  - Every merge is appended to `data/processed/manual_group_merges.json`,
    a durable record (separate from `config.py`) applied automatically by
    `src/cluster_videos.py` on every future pipeline run — so a merge made
    today still holds after next week's fresh CSV/XLSX exports are dropped
    in and `python run.py` is re-run. This is additive to the existing
    `MANUAL_TITLE_MERGES` list in `config.py`; that list still works for
    merges you'd rather hand-edit, this is for the ones found while
    reviewing the dashboard.
  - Internally this reuses the same merge logic the pipeline itself will
    use (`cluster_videos._merge_two_groups`), so a CLI merge and a
    pipeline-applied merge produce an identical result.
  - No dashboard content changed with this update — it's a backend-only
    addition, so the published dashboard itself is untouched. This entry
    (and the full source) will be included the next time the zipped
    codebase is sent.

## 2026-10-06 (later)

- **"Data as of" now shows a real, platform-specific date — or
  "undefined" when there isn't one, never today's date.**
  - Backend (`src/merge_platforms.py`): removed every fallback to
    `date.today()`. Each platform's `asof` now comes only from data
    actually present in its export:
    - YouTube: the "Data as of" column from the API-pull `.xlsx`
      (`captured_at` from `yt_pull.py`); `None` if that cell is blank.
      The Studio-CSV-only fallback path also uses `None` rather than
      inventing a date, since that CSV has no date field of its own.
    - Facebook / Instagram: the end date embedded in the export's own
      filename (e.g. `..._Sep-28-2026-FB3.csv` → `2026-09-28`); `None`
      if a filename doesn't match that pattern.
    - TikTok: the CSV's own "Time" column (its literal export date,
      e.g. `"September 28"` — no year, shown as-is since that's genuinely
      all TikTok's export gives us).
  - Frontend (`templates/dashboard_template.html`): replaced the single
    global "latest across everything" calculation with
    `LATEST_BY_PLATFORM`, computed once per platform from only that
    platform's own entries.
    - Viewing a specific platform tab shows that platform's own latest
      date (e.g. TikTok tab → "September 28").
    - Viewing "All" shows a date only if every platform's latest date is
      identical; otherwise shows literally "undefined" rather than
      blending dates that may not represent the same snapshot.
  - Fixed a related bug while in there: `updateAsOf()` had been written
    but was never actually called from `render()`, so the "Data as of"
    field never updated after the initial page load regardless of which
    fix was in place. It's now called on every render (tab switch,
    search, initial load).
  - Added an `asof-scope` label under the date that says which export(s)
    it's describing ("TikTok export" vs "YouTube, Facebook, Instagram &
    TikTok").

## 2026-10-06 (earlier)

- Fixed "Data as of" showing "unknown": the JS was checking `.asof`
  directly on each platform's value in `g.platforms`, but each platform
  holds an *array* of entries (to support Standard/Short, multiple posts,
  etc.) — arrays have no `.asof`, so the computed "latest" value was
  always `null`. (This specific bug is superseded by the per-platform
  rework above, but is kept here for the history.)
- Merged the hashtag-only Instagram upload (caption:
  `#love #younglove #lovers ...`, no real title) into "Sneaking In" via a
  manual entry in `config.py`'s `MANUAL_TITLE_MERGES`. Matched on
  `#younglove` rather than the full caption, because the real caption has
  a stray Unicode diacritic hidden inside one hashtag that silently
  breaks an exact match on the full string.

## Earlier sessions (summary — see the live conversation for full detail)

- Built the initial pipeline: merge_platforms.py → cluster_videos.py →
  build_dashboard.py, matching videos across YouTube/Facebook/
  Instagram/TikTok by fuzzy title overlap.
- Added YouTube Short vs Standard detection (by view-rank within a
  matched pair) and multi-part Shorts detection ("pt. N" / "Part N",
  kept separate and ordered by part number).
- Filtered out non-video posts automatically via each platform's own
  "Post type" field (Facebook: not "Videos"; Instagram: not "IG reel"),
  plus a manual-exclude list (`MANUAL_EXCLUDE_PERMALINKS`) for posts that
  pass as videos but aren't original content (a reshare).
- Added `MANUAL_TITLE_MERGES` for title pairs sharing no words at all
  (e.g. "Snake Bag" / "Handbag Problems" — different names in different
  languages for the same video).
- Added `MANUAL_TITLE_TEXT_FIXES` for cleaning non-Latin script out of
  display titles.
- Fixed the platform-tab filter to show and sort by that platform's own
  metrics, not the cross-platform combined total.
- Fixed a Views/Reach fallback for older Facebook/Instagram exports that
  predate those platforms reporting "Views" as a metric.
