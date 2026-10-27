# Kehelmala Studios — Cross-Platform Video Dashboard

Combines YouTube, Facebook, Instagram and TikTok analytics exports into one
dashboard showing each real-world video's performance once, merged across
platforms (not duplicated per-platform).

The dashboard has two pages:

- **Numbers** (`docs/index.html`) — every video, its views/likes/comments/
  shares per platform and combined, searchable and filterable by platform.
- **Charts** (`docs/analytics.html`) — chart-based view of the same data.

Live dashboard: hosted on GitHub Pages from this repo's `docs/` folder.

## Quick start

```bash
pip install -r requirements.txt
python run.py
```

This reads everything in `data/raw/{youtube,facebook,instagram,tiktok}/`,
matches videos across platforms, and writes the finished site into `docs/`
(`index.html`, `analytics.html`, `logo.png`). Open `docs/index.html` in a
browser to check it.

## Updating with a fresh week's exports

1. Export fresh data from each platform (see "Where each file comes from"
   below) and drop the files into the matching `data/raw/<platform>/`
   folder. You can leave old Facebook/Instagram/TikTok files in place —
   exports with overlapping date ranges are de-duplicated automatically
   (Facebook/Instagram by Post ID, keeping the most recent). For YouTube,
   only the newest export is used.
2. Run:
   ```bash
   python run.py
   ```
3. Open `docs/index.html` and spot-check it. If you spot two videos that
   should be one but weren't merged automatically (or one that was merged
   by mistake), use the merge/unmerge tools below — you don't need to touch
   any code.
4. Publish: commit and push. GitHub Pages serves `docs/` directly, so the
   live dashboard updates a minute or two after the push.
   ```bash
   git add -A
   git commit -m "Weekly update"
   git push
   ```

## Where each file comes from

| Folder | Source | Notes |
|---|---|---|
| `data/raw/youtube/` | YouTube Studio export (see below) | Only the newest export is used |
| `data/raw/facebook/` | Meta Business Suite insights export (CSV) | Only rows whose "Post type" is a video are kept |
| `data/raw/instagram/` | Meta Business Suite insights export (CSV) | Only "IG reel" / video rows are kept |
| `data/raw/tiktok/` | TikTok analytics export (CSV) | Only covers the top 15 videos |
| `data/raw/tiktok/public/` | TikTok public profile (JSON) | Every other public video; newest file is used |

### TikTok public profile data

TikTok's analytics export only includes the 15 best-performing videos. The
rest are read from the channel's public profile page
(tiktok.com/@kehelmalastudios), one video page at a time, and saved as
`data/raw/tiktok/public/tiktok_public_<date>.json`. That date becomes
TikTok's "Data as of". Each file is a list of
`{id, title, date, views, likes, comments, shares, saves}` (hashtags are
dropped from titles; the link is built from the id).

- Only the newest file is used; older ones stay as dated backups.
- **Public numbers are rounded.** TikTok's public pages round anything
  above roughly 10K to three significant figures (1,592,137 views shows as
  1,600,000). Smaller counts are exact.
- So when a video is in both the export and the profile file, the export's
  exact numbers are used.
- Posts TikTok hides from logged-out visitors aren't on the public profile,
  so they still show "Data unavailable".
- This is collected in a normal browser at a slow pace, and it backs off
  when TikTok rate-limits.

### YouTube Studio export

1. YouTube Studio → **Analytics** → **Advanced mode**.
2. Choose the **Content** view (per video), and set the date range to
   **Lifetime** — otherwise views only cover the chosen period.
3. Make sure these columns are included: **Views, Likes, Comments added,
   Shares, Duration** (any missing column shows as 0 on the dashboard, and
   a warning prints when you run `python run.py`).
4. **Export current view** → **Comma-separated values (.csv)**.
5. Unzip it and drop the **whole folder** into `data/raw/youtube/`. Keep the
   folder's own name (e.g. `Content 2024-04-13_2026-10-19 Kehelmala Studios`)
   — the end date in that name is where YouTube's "Data as of" date comes
   from.

The pipeline reads the `Table data.csv` inside the newest export folder
(`Chart data.csv` / `Totals.csv` are ignored). Each video's link is built
from its video ID.

*Transition note:* until the first full Studio export (with Likes/Comments)
is dropped in, the older combined workbook `youtube_export_with_shares.xlsx`
(built by the API scripts in `legacy_scripts/`) is used instead, so the
dashboard doesn't lose YouTube likes/comments in the meantime. Once a full
Studio export is in place, the `.xlsx`, the old top-level `Table data.csv`
and `legacy_scripts/` can be deleted.

## Dated backups

Every `python run.py` also copies the processed data into
`data/snapshots/<run date>/` (e.g. `data/snapshots/2026-10-27/`):

- `all_posts.json` — every post from every platform, with its numbers on that date
- `grouped.json` — the merged per-video data the dashboard was built from
- `manual_group_merges.json` — the manual merges in effect at the time

Re-running on the same day overwrites that day's folder; earlier dates are
never touched. Snapshots are plain files committed with the rest of the
repo, so pushing to GitHub is the off-site backup — no database needed.
To compare two dates, open the same video in two snapshots' `grouped.json`.

## Merging two videos manually

The automatic matcher compares titles across platforms and merges what
looks like the same video. It won't always get it right — different
languages, a caption that's just hashtags, heavily abbreviated titles,
etc. When you spot two entries on the dashboard that are really the same
video, merge them from the command line instead of hand-editing data:

```bash
python src/merge_videos_cli.py
```

It will:
1. List every current video title with its total views, so you can find
   the two you mean.
2. Ask you to pick the first and second video — type the list number
   shown, or the title itself (a partial title works if it's unambiguous).
3. Ask which title the merged result should use (press Enter to accept
   the suggested default — whichever of the two has more views).
4. Combine them (adds up views/likes/comments/shares, keeps every
   platform entry from both) and rebuild both pages in `docs/`
   immediately so you can check the result.

The merge is also written to `data/processed/manual_group_merges.json`,
so it's remembered automatically the next time you run `python run.py`
on a fresh week's exports — you never have to redo it.

Non-interactive form, for scripting or if you already know the exact
titles:
```bash
python src/merge_videos_cli.py --a "Title One" --b "Title Two" --result "Title One"
```

If you'd rather hand-edit, the older mechanism still works too: add an
entry to `MANUAL_TITLE_MERGES` in `config.py` (useful when you want to
match on a short, distinctive substring rather than the full titles).

## Undoing a wrong merge

If the matcher (or an earlier manual merge) lumped together posts that are
actually different videos, split them back apart:

```bash
python src/unmerge_videos_cli.py
```

It lists every video that has entries from more than one post, lets you
pick one, shows each individual post inside it, and asks which ones to pull
out into a separate video (and what to call it). Both pages in `docs/` are
rebuilt immediately.

The split is recorded in `data/processed/manual_group_splits.json` and
those posts are never merged back together on future runs, however similar
their titles look.

Non-interactive form:
```bash
python src/unmerge_videos_cli.py --group "Title" --take "YouTube:1,Facebook:0" --new-title "New Title"
```

## Other manual overrides (`config.py`)

- `TITLE_RENAMES` — change how a video's title is displayed on the
  dashboard (key = current title, value = the title you want).
- `MANUAL_TITLE_MERGES` — force-merge by matching a substring in the raw
  title/caption (for titles with zero word overlap, e.g. different
  languages for the same video).
- `MANUAL_EXCLUDE_PERMALINKS` — drop specific posts that pass the
  "is this a video" filter but aren't original content (e.g. a reshare).
- `MANUAL_TITLE_TEXT_FIXES` — replace a raw title/caption (e.g. one
  written in Sinhala/Tamil script) with a clean English display title.
- `JACCARD_MATCH_THRESHOLD` / `STOPWORDS` / `CONTAINMENT_MIN_WORD_LEN` —
  tuning knobs for the automatic title-matching heuristic.

All of these survive a fresh `python run.py` — nothing here gets
overwritten by re-running the pipeline.

## Dates

Every date on the dashboard is shown as **DD/MM/YYYY**. Internally the
pipeline stores all dates as `YYYY-MM-DD`, whatever format each platform
exports them in.

TikTok's export gives no year. Each TikTok video's year is filled from the
matching video's full date on another platform; a TikTok video with no
match on another platform shows its date without a year (e.g. "April 24").

## "Data as of"

Each platform's "as of" date comes only from that platform's own export
— never from today's date / when you happened to run the tool:

- **YouTube** — the end date in the Studio export's folder name.
- **Facebook / Instagram** — the end date in the export's own filename
  (e.g. `...Sep-28-2026-FB3.csv` → 28/09/2026).
- **TikTok** — the export's own "Time" column. It has no year, so the year
  is the earliest one that puts it on or after the newest TikTok post.

On the dashboard: viewing a specific platform tab shows that platform's
own latest date ("Not available" if its export didn't include one).
Viewing "All" shows a single date when every platform's latest date is the
same, and "Varies by platform" otherwise — click a platform tab to see each
one's date.

## Hosting the dashboard

The site is served by GitHub Pages from the `docs/` folder of the `main`
branch (repo **Settings → Pages → Build and deployment → Deploy from a
branch → `main` / `/docs`**). `python run.py` writes straight into `docs/`,
so publishing is just commit + push. `docs/.nojekyll` tells Pages to serve
the files as-is.

GitHub Pages on a free account requires the repository to be public, which
means the raw exports in `data/raw/` are publicly visible too.

## Project layout

```
config.py                    Manual overrides (see above)
run.py                       Runs the full pipeline (merge → cluster → build both pages)
requirements.txt
assets/
  logo.png                   Sidebar logo, copied into docs/ on every build
src/
  merge_platforms.py         Step 1: reads data/raw/*, writes data/processed/all_posts.json
  cluster_videos.py          Step 2: matches videos across platforms, writes data/processed/grouped.json
  build_dashboard.py         Step 3: builds docs/index.html (Numbers page) + copies the logo
  build_analytics.py         Step 4: builds docs/analytics.html (Charts page)
  merge_videos_cli.py        CLI tool to manually merge two videos
  unmerge_videos_cli.py      CLI tool to split a wrong merge back apart
templates/
  dashboard_template.html    Numbers page (data-free; __DATA_PLACEHOLDER__ is replaced at build time)
  analytics_template.html    Charts page (same placeholder mechanism)
data/
  raw/{youtube,facebook,instagram,tiktok}/   Drop fresh exports here
  processed/                 Intermediate JSON (all_posts.json, grouped.json, manual merge/split records)
docs/                        The built site that GitHub Pages serves — don't edit by hand, it's overwritten on every build
legacy_scripts/              Original YouTube API scripts (only needed for the old .xlsx; see transition note above)
CHANGELOG.md                 History of changes made to this project
```
