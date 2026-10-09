# Kehelmala Studios — Cross-Platform Video Dashboard

Combines YouTube, Facebook, Instagram and TikTok analytics exports into one
dashboard showing each real-world video's performance once, merged across
platforms (not duplicated per-platform).

Live dashboard: published as a Claude Artifact (link shared separately —
ask Claude to re-share it, or open your last Claude conversation).

## Quick start

```bash
pip install -r requirements.txt
python run.py
```

This reads everything in `data/raw/{youtube,facebook,instagram,tiktok}/`,
matches videos across platforms, and writes `dist/dashboard.html` — a
single self-contained file you can open directly in a browser, or publish
(see "Hosting" below).

## Updating with a fresh week's exports

1. Export fresh data from each platform (see "Where each file comes from"
   below) and drop the files into the matching `data/raw/<platform>/`
   folder. You can leave old files in place — exports with overlapping
   date ranges are de-duplicated automatically (Facebook/Instagram, by
   Post ID, keeping the most recent).
2. Run:
   ```bash
   python run.py
   ```
3. Open `dist/dashboard.html` and spot-check it. If you spot two videos
   that should be one but weren't merged automatically, use the merge
   tool below — you don't need to touch any code.
4. Publish the new `dist/dashboard.html` (see "Hosting").

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
   platform entry from both) and rebuild `dist/dashboard.html`
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

## Where each file comes from

| Folder | Source | Notes |
|---|---|---|
| `data/raw/youtube/` | `legacy_scripts/yt_pull.py` + `yt_merge_shares.py` → a combined `.xlsx`, **or** YouTube Studio's own CSV export (`Table_data.csv`) as a fallback | The `.xlsx` includes likes/comments/a real "Data as of" date; the CSV-only fallback does not (likes/comments show 0, and the "as of" date is left blank) — a warning prints when this fallback is used |
| `data/raw/facebook/` | Meta Business Suite insights export (CSV) | Only rows whose "Post type" is a video are kept |
| `data/raw/instagram/` | Meta Business Suite insights export (CSV) | Only "IG reel" / video rows are kept |
| `data/raw/tiktok/` | TikTok analytics export (CSV) | — |

## Other manual overrides (`config.py`)

- `MANUAL_TITLE_MERGES` — force-merge by matching a substring in the raw
  title/caption (for titles with zero word overlap, e.g. different
  languages for the same video).
- `MANUAL_EXCLUDE_PERMALINKS` — drop specific posts that pass the
  "is this a video" filter but aren't original content (e.g. a reshare).
- `MANUAL_TITLE_TEXT_FIXES` — replace a raw title/caption (e.g. one
  written in Sinhala/Tamil script) with a clean English display title.
- `JACCARD_MATCH_THRESHOLD` / `STOPWORDS` / `CONTAINMENT_MIN_WORD_LEN` —
  tuning knobs for the automatic title-matching heuristic, in
  `src/cluster_videos.py`.

All of these survive a fresh `python run.py` — nothing here gets
overwritten by re-running the pipeline.

## "Data as of"

Each platform's "as of" date comes only from that platform's own export
data — never from today's date / when you happened to run the tool:

- **YouTube** — the "Data as of" column in the combined `.xlsx`.
- **Facebook / Instagram** — the end date in the export's own filename
  (e.g. `...Sep-28-2026-FB3.csv` → `2026-09-28`).
- **TikTok** — the CSV's own "Time" column, shown as-is (TikTok's export
  gives no year, e.g. `"September 28"`).

On the dashboard: viewing a specific platform tab shows that platform's
own latest date. Viewing "All" shows a date only if every platform's
latest date is identical; otherwise it shows "undefined" rather than
blending dates that may not represent the same snapshot.

## Hosting the dashboard

`dist/dashboard.html` is a single self-contained file — no server, no
build step, no dependencies to host. Options:

- **Just share the file** — email it or drop it in shared drive; anyone
  can open it directly in a browser.
- **GitHub Pages** — push this repo (or just `dist/dashboard.html`
  renamed to `index.html`) to a GitHub repo, enable Pages in Settings,
  get a public URL.
- **Netlify Drop** (netlify.com/drop) — drag `dist/dashboard.html` onto
  the page, get a shareable URL in seconds, no account required.
- **Claude Artifact** — ask Claude to publish `dist/dashboard.html` as an
  artifact; you'll get a shareable link that can be updated in place on
  every re-run.

## Project layout

```
config.py                    Manual overrides (see above)
run.py                       Runs the full pipeline (merge → cluster → build)
requirements.txt
src/
  merge_platforms.py         Step 1: reads data/raw/*, writes data/processed/all_posts.json
  cluster_videos.py          Step 2: matches videos across platforms, writes data/processed/grouped.json
  build_dashboard.py         Step 3: injects grouped.json into the template, writes dist/dashboard.html
  merge_videos_cli.py        CLI tool to manually merge two videos (see above)
templates/
  dashboard_template.html    The dashboard page (data-free; __DATA_PLACEHOLDER__ is replaced at build time)
data/
  raw/{youtube,facebook,instagram,tiktok}/   Drop fresh exports here
  processed/                 Intermediate JSON (all_posts.json, grouped.json, manual_group_merges.json)
dist/
  dashboard.html             The built, shareable dashboard
legacy_scripts/
  yt_pull.py, yt_export.py, yt_merge_shares.py   Original YouTube API scripts that build the combined .xlsx
CHANGELOG.md                 Full history of changes made to this project
```
