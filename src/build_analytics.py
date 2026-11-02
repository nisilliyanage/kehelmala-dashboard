"""
Builds the second, chart-based analytics page.

Reads data/processed/grouped.json (same data the main list dashboard uses) and
injects it into templates/analytics_template.html, writing docs/analytics.html.
Also injects per-post totals from the most recent snapshot saved before today,
so the page can show change since then. Run as part of run.py, right after
build_dashboard.py (and before run.py saves today's snapshot).
"""
import datetime
import json
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GROUPED_PATH = os.path.join(BASE, 'data', 'processed', 'grouped.json')
SNAPSHOTS_DIR = os.path.join(BASE, 'data', 'snapshots')
TEMPLATE_PATH = os.path.join(BASE, 'templates', 'analytics_template.html')
OUT_PATH = os.path.join(BASE, 'docs', 'analytics.html')
PLACEHOLDERS = ['__DATA_PLACEHOLDER__', '__PREV_PLACEHOLDER__', '__BUILD_DATE__']


def previous_snapshot(today):
    """Latest snapshot dated before today, as {date, posts: {url: [v, l, c, s]}}, or None.

    Keyed by post URL rather than by group, so regrouping videos between runs
    doesn't throw the comparison off. Today's own snapshot (from an earlier run
    today) is skipped - comparing against it would always show no change.
    """
    if not os.path.isdir(SNAPSHOTS_DIR):
        return None
    dates = sorted(d for d in os.listdir(SNAPSHOTS_DIR)
                   if d < today and os.path.isfile(os.path.join(SNAPSHOTS_DIR, d, 'grouped.json')))
    if not dates:
        return None
    with open(os.path.join(SNAPSHOTS_DIR, dates[-1], 'grouped.json'), encoding='utf-8') as f:
        groups = json.load(f)
    posts = {}
    for g in groups:
        for entries in g['platforms'].values():
            for e in entries:
                if e.get('u'):
                    posts[e['u']] = [e['v'], e['l'], e['c'], e['s']]
    return {'date': dates[-1], 'posts': posts}


def main():
    with open(GROUPED_PATH, encoding='utf-8') as f:
        groups_json_text = f.read()
        json.loads(groups_json_text)  # validate

    with open(TEMPLATE_PATH, encoding='utf-8') as f:
        template = f.read()

    for ph in PLACEHOLDERS:
        if ph not in template:
            raise SystemExit(f'templates/analytics_template.html is missing {ph}')

    today = datetime.date.today().isoformat()
    prev = previous_snapshot(today)
    # Small placeholders first, so nothing inside the data can collide with them.
    out = (template
           .replace('__PREV_PLACEHOLDER__', json.dumps(prev, ensure_ascii=False))
           .replace('__BUILD_DATE__', today)
           .replace('__DATA_PLACEHOLDER__', groups_json_text))

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, 'w', encoding='utf-8') as f:
        f.write(out)
    print(f'Wrote {OUT_PATH} ({len(out)} bytes)'
          + (f', comparing against snapshot {prev["date"]}' if prev else ', no earlier snapshot to compare'))


if __name__ == '__main__':
    main()
