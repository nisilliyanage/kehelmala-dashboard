# Changelog

Record of changes made to the dashboard, newest first.

## 2026-10-27

- **TikTok rows with no data say "Data unavailable"** instead of "Not posted
  here". TikTok's export only includes the top 15 videos, so a missing row
  doesn't mean the video wasn't posted there.
- **TikTok videos beyond the top 15.** Stats for every other public video
  are read from the public TikTok profile into
  `data/raw/tiktok/public/tiktok_public_<date>.json` and merged with the
  export. The TikTok tab's "Data as of" shows that date and says
  "TikTok export + public profile". TikTok now appears on 130 of 145
  videos, up from 15. Public numbers above ~10K are rounded by TikTok, so
  the 15 videos in the export keep the export's exact figures.
- Split the 2024 "The Morning After" TikTok out of the 2026 "Morning
  After" group, and merged the 2026 "Fit on" TikTok into "Fit On".
- **Split three over-merged films into separate videos on every platform.**
  "Gift Box" (Jul 2024), "Santa's Gift" (Dec 2024) and "The Gift" (Aug 2025)
  had been one row. So had "The Fit" (Oct 2025) and "Fit On" (Jun 2026).
  The YouTube upload titled just "Gift" (13/10/2025) sits under The Gift.
- **Fixed "Wrong Number" / "Interrogation".** The social posts call them
  "Caller Unknown" and "Caller Unknown 2" (2024). YouTube calls them
  "Wrong Number?" and "Interrogation (Wrong Number 2)" (2025). Both social
  posts had been merged into one row and both YouTube uploads into another.
  Two `MANUAL_TITLE_MERGES` rules in `config.py` now pair each film
  correctly.
- **Titles keep their punctuation.** Apostrophes, brackets, slashes, `?`,
  `!` and commas used to be stripped, so titles showed as "You re my Garden
  of Eden" or "Wrong Number". Each video now has a `display` title that
  keeps them and drops only the Sinhala/Tamil translations. The stripped
  `title` is still used for matching, renames and the merge/split records,
  so existing fixes keep working. Both pages also escape titles before
  inserting them.
- **Dated backups.** Every `python run.py` now saves a copy of the processed
  data to `data/snapshots/<run date>/` (see "Dated backups" in the README).

## 2026-10-20

- **UI redesign of both pages (Apple-style).**
  - Shared design tokens, softer card surfaces, and a smaller, tighter
    heading that no longer wraps onto two lines.
  - KPI numbers scale with their card, so totals like 238,710,067 no longer
    get cut off.
  - Numbers page: the platform tabs are now a segmented control with a
    sliding thumb. The tabs, search and column headers stay pinned in a
    translucent bar while you scroll. Rows expand smoothly, sort arrows show
    the current order, and rows and headers work from the keyboard.
  - Charts page: platform toggles have colour swatches and checkmarks, which
    fixes the white-on-white TikTok button. Bars grow in on load and glide
    when the selection changes. Value labels pick dark or white ink to stay
    readable on light bars.
  - Both pages respect reduced motion, reduced transparency and
    increased-contrast settings. On narrow screens the nav becomes a sticky
    top bar.
  - Removed the stray nested `<html>` document wrapper in the Numbers
    template.
- **New pastel platform colours ("Peach & sky"), the same on both pages.**
  YouTube `#E88761`, Facebook `#78BCEF`, Instagram `#A782E1`, TikTok
  `#16CFA0`. They replace the warm dots on the Numbers page and the slate
  greys on the Charts page, which didn't match each other, and the greys were
  hard to tell apart. All four stay distinct from one another, including for
  colourblind readers (checked with the dataviz palette validator). Labels
  inside chart marks now pick dark or white text by contrast, so they stay
  readable on the light fills.

- **The build now publishes straight to GitHub Pages' folder.** `python run.py`
  writes `docs/index.html` (Numbers page), `docs/analytics.html` (Charts page)
  and `docs/logo.png`, so publishing is just commit + push. The old `dist/`
  folder is gone, and the sidebar links now point at `index.html` instead of
  `dashboard.html`. Added `docs/.nojekyll` so Pages serves files as-is.
- **The merge/unmerge CLIs now rebuild the Charts page too.** Before, they only
  rebuilt the Numbers page, so the Charts page went stale after a manual merge
  until the next full `python run.py`.
- **YouTube now comes from YouTube Studio's own CSV export.**
  - Reads the newest `Table data.csv` under `data/raw/youtube/` (an unzipped
    Studio export folder works as-is); `Chart data.csv` / `Totals.csv` are
    ignored.
  - Picks up Likes, Comments added and Shares when they're in the export, and
    warns about any that are missing.
  - Builds each video's link from its ID (Studio's table has no URL column).
  - Fixed publish dates: Studio writes them as `"Jun 30, 2025"`, which the old
    fallback cut down to `"Jun 30, 20"`.
  - "Data as of" comes from the end date in the export folder's name
    (`Content 2024-04-13_2026-10-19 ...`).
  - The old API-built `.xlsx` is still used until a Studio export with
    Likes/Comments columns is dropped in, so YouTube likes/comments don't drop
    to 0 during the switch.
- **All dates now show as DD/MM/YYYY, including "Data as of".** Every date is
  stored as `YYYY-MM-DD` in the pipeline. Facebook/Instagram used to be stored
  as US-style `MM/DD/YYYY` and only reformatted for display. TikTok's yearless
  export date (e.g. "September 28") now gets its year from the export's own post
  dates, so it can be compared with the other platforms.
- **"Data as of" wording:** "All" shows "Varies by platform" (instead of
  "undefined") when the platforms' export dates differ. A single platform with
  no export date shows "Not available".
- Added `.gitignore` (Python caches, virtualenv, editor files) and stopped
  tracking `__pycache__/`.
- README: covers the Charts page, the unmerge tool, `TITLE_RENAMES`, the
  YouTube Studio export steps and the GitHub Pages setup.

## 2026-10-13

- Added the Charts page (`templates/analytics_template.html`, built by
  `src/build_analytics.py`) alongside the Numbers page, with sidebar navigation
  and the studio logo.

## 2026-10-09

- Added `src/unmerge_videos_cli.py` to split a wrong merge back apart; splits
  are recorded in `data/processed/manual_group_splits.json` and respected on
  every future run.
- Unified the dashboard's "Published" date display to DD/MM/YYYY; TikTok's
  yearless dates take their year from the same video on another platform.
- Added `TITLE_RENAMES` to `config.py` for changing display titles.
- Moved the published dashboard to `docs/index.html` for GitHub Pages.

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
    addition, so the published dashboard itself is untouched.

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
