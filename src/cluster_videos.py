"""
Step 2 of the pipeline.

Reads data/processed/all_posts.json, clusters posts across platforms into one
group per real-world video, and writes data/processed/grouped.json.

After automatic clustering + the static MANUAL_TITLE_MERGES (config.py) are applied,
any merges recorded via `python src/merge_videos_cli.py` (data/processed/manual_group_merges.json)
are applied as a final pass, so merges made through the CLI survive future re-runs on
fresh weekly exports without having to redo them by hand.
"""
import json
import os
import re
import sys
import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IN_PATH = os.path.join(BASE, 'data', 'processed', 'all_posts.json')
OUT_PATH = os.path.join(BASE, 'data', 'processed', 'grouped.json')
MANUAL_GROUP_MERGES_PATH = os.path.join(BASE, 'data', 'processed', 'manual_group_merges.json')

HASHTAG_RE = re.compile(r'#\S+')
LATIN_RE = re.compile(r"[A-Za-z0-9' ]+")
PART_RE = re.compile(r'\b(?:pt\.?|part)\s*(\d+)\b', re.I)


def _date_parts(value):
    text = str(value or '').strip()
    for pattern, date_format in (
        (r'^\d{4}-\d{1,2}-\d{1,2}', '%Y-%m-%d'),
        (r'^\d{1,2}/\d{1,2}/\d{4}', '%m/%d/%Y'),
    ):
        if re.match(pattern, text):
            try:
                return datetime.datetime.strptime(text[:10], date_format).date()
            except ValueError:
                return None
    try:
        return datetime.datetime.strptime(text, '%B %d').date().replace(year=2000)
    except ValueError:
        return None


def _resolve_tiktok_years(by_platform):
    """Use the matching platform date to complete TikTok's yearless dates."""
    other_dates = []
    for platform, posts in by_platform.items():
        if platform == 'TikTok':
            continue
        for post in posts:
            date = _date_parts(post.get('date'))
            if date and date.year != 2000:
                other_dates.append(date)

    if not other_dates:
        return

    for post in by_platform.get('TikTok', []):
        date = _date_parts(post.get('date'))
        if not date or date.year != 2000:
            continue
        years = {candidate.year for candidate in other_dates
                 if candidate.month == date.month and candidate.day == date.day}
        if len(years) == 1:
            post['date'] = date.replace(year=years.pop()).isoformat()


def strip_hashtags(text):
    return HASHTAG_RE.sub('', text or '')


def extract_latin(text):
    return ' '.join(LATIN_RE.findall(text or ''))


CHANNEL_SUFFIX_RE = re.compile(r'\s*\|\s*A\s+Kehelmala\s+.*', re.I)


def clean_display_title(text):
    if not text:
        return ''

    # Prefer the first line with real (non-hashtag) text
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    chosen = ''
    for line in lines:
        if strip_hashtags(line).strip():
            chosen = line
            break
    if not chosen and lines:
        chosen = lines[0]
    elif not chosen:
        chosen = text

    # Remove channel suffixes (e.g. "| A Kehelmala Short")
    chosen = CHANNEL_SUFFIX_RE.sub('', chosen)

    # Remove hashtags and extract Latin characters
    cleaned = strip_hashtags(chosen)
    latin = extract_latin(cleaned).strip()
    latin = re.sub(r'\s+', ' ', latin)
    latin = latin.strip(' -:|;,._')

    if latin:
        return latin

    # Fallback if no Latin letters (e.g. Sinhala/Tamil script title)
    fallback = cleaned.strip(' -:|;,._ \n\r\t')
    fallback = re.sub(r'\s+', ' ', fallback)
    if fallback:
        return fallback

    fallback = strip_hashtags(text).strip(' -:|;,._ \n\r\t')
    fallback = re.sub(r'\s+', ' ', fallback)
    return fallback or text.strip()


def norm_words(text):
    cl = clean_display_title(text)
    words = re.findall(r"[a-z0-9']+", (cl or '').lower())
    wset = {w for w in words if w not in config.STOPWORDS and not w.isdigit()}
    if not wset:
        words = re.findall(r"[a-z0-9']+", (text or '').lower())
        wset = {w for w in words if w not in config.STOPWORDS and not w.isdigit()}
    return wset


def part_number(text):
    m = PART_RE.search(text or '')
    return int(m.group(1)) if m else None


def match_score(a_words, b_words):
    if not a_words or not b_words:
        return 0.0
    inter = a_words & b_words
    union = a_words | b_words
    jaccard = len(inter) / len(union) if union else 0.0

    # Containment exception: a short, distinctive title fully contained in a longer one
    # (common when one platform's caption is terse and the other's is descriptive).
    smaller, larger = (a_words, b_words) if len(a_words) <= len(b_words) else (b_words, a_words)
    distinctive = {w for w in smaller if len(w) >= config.CONTAINMENT_MIN_WORD_LEN}
    if distinctive and distinctive.issubset(larger):
        return max(jaccard, 0.99)

    return jaccard


def _manual_merge_title(raw_title):
    low = (raw_title or '').lower()
    for rule in config.MANUAL_TITLE_MERGES:
        if any(frag.lower() in low for frag in rule['match']):
            return rule['title']
    return None


def cluster(posts):
    youtube = [p for p in posts if p['platform'] == 'YouTube']
    others = [p for p in posts if p['platform'] != 'YouTube']

    clusters = []  # list of {'title': str, 'posts': [...]}

    for p in youtube:
        c_title = clean_display_title(p['title'])
        words = norm_words(p['title'])
        placed = False
        for c in clusters:
            if c_title and c['title'].strip().lower() == c_title.strip().lower():
                c['posts'].append(p)
                c['words'] |= words
                placed = True
                break
            elif match_score(words, c['words']) >= config.JACCARD_MATCH_THRESHOLD:
                c['posts'].append(p)
                c['words'] |= words
                placed = True
                break
        if not placed:
            clusters.append({'title': c_title, 'words': set(words), 'posts': [p]})

    for p in others:
        c_title = clean_display_title(p['title'])
        words = norm_words(p['title'])

        exact_match = None
        if c_title:
            for c in clusters:
                if c['title'].strip().lower() == c_title.strip().lower():
                    exact_match = c
                    break

        if exact_match is not None:
            exact_match['posts'].append(p)
            exact_match['words'] |= words
        else:
            best, best_score = None, 0.0
            for c in clusters:
                score = match_score(words, c['words'])
                if score > best_score:
                    best, best_score = c, score
            if best is not None and best_score >= config.JACCARD_MATCH_THRESHOLD:
                best['posts'].append(p)
                best['words'] |= words
            else:
                clusters.append({'title': c_title, 'words': set(words), 'posts': [p]})

    # Static manual merges (config.py) — merge by raw-title substring match.
    for p in [pp for c in clusters for pp in c['posts']]:
        forced_title = _manual_merge_title(p['title'])
        if not forced_title:
            continue
        target = next((c for c in clusters if c['title'] == forced_title), None)
        if target is None:
            target = {'title': forced_title, 'words': set(), 'posts': []}
            clusters.append(target)
        home = next(c for c in clusters if p in c['posts'])
        if home is not target:
            home['posts'].remove(p)
            target['posts'].append(p)
            target['title'] = forced_title

    clusters = [c for c in clusters if c['posts']]
    for c in clusters:
        if _manual_merge_title(c['title']) is None:
            for p in c['posts']:
                ft = _manual_merge_title(p['title'])
                if ft:
                    c['title'] = ft
                    break

    # Merge any clusters that have identical clean display titles
    merged_clusters = []
    by_title = {}
    for c in clusters:
        t_key = c['title'].strip().lower()
        if t_key and t_key in by_title:
            existing = by_title[t_key]
            existing['posts'].extend(c['posts'])
            existing['words'] |= c['words']
        else:
            if t_key:
                by_title[t_key] = c
            merged_clusters.append(c)

    return merged_clusters


def build_groups(clusters):
    groups = []
    for c in clusters:
        by_platform = {}
        for p in c['posts']:
            by_platform.setdefault(p['platform'], []).append(p)
        _resolve_tiktok_years(by_platform)

        platforms = {}
        for plat, plist in by_platform.items():
            plist = sorted(plist, key=lambda x: -(x.get('views') or 0))
            entries = []
            for i, p in enumerate(plist):
                label = None
                if plat == 'YouTube':
                    part = part_number(p['title'])
                    if part is not None:
                        label = f'Part {part}'
                    elif len(plist) > 1:
                        label = 'Standard' if i == 0 else 'Short'
                elif len(plist) > 1:
                    label = f'Post {i + 1}'
                entries.append({
                    'v': p.get('views') or 0,
                    'l': p.get('likes') or 0,
                    'c': p.get('comments') or 0,
                    's': p.get('shares') or 0,
                    'd': p.get('date'),
                    'u': p.get('permalink'),
                    'asof': p.get('asof'),
                    'label': label,
                })
            platforms[plat] = entries

        tot_v = sum(e['v'] for plist in platforms.values() for e in plist)
        tot_l = sum(e['l'] for plist in platforms.values() for e in plist)
        tot_c = sum(e['c'] for plist in platforms.values() for e in plist)
        tot_s = sum(e['s'] for plist in platforms.values() for e in plist)

        groups.append({
            'title': clean_display_title(c['title']),
            'genre': 'Untagged',
            'platforms': platforms,
            'tot_v': tot_v,
            'tot_l': tot_l,
            'tot_c': tot_c,
            'tot_s': tot_s,
            'n_platforms': len(platforms),
        })
    return groups


def _merge_two_groups(groups, title_a, title_b, result_title):
    """Merge group title_a into title_b (or vice versa), combining per-platform entry
    lists and recomputing totals. Matching is case-insensitive exact title match.
    Returns the (possibly unchanged) groups list."""
    def find(t):
        tl = (t or '').strip().lower()
        for g in groups:
            if g['title'].strip().lower() == tl:
                return g
        return None

    ga, gb = find(title_a), find(title_b)
    if ga is None or gb is None or ga is gb:
        return groups  # nothing to do — titles no longer exist as separate groups

    for plat, entries in gb['platforms'].items():
        ga['platforms'].setdefault(plat, []).extend(entries)
    ga['title'] = clean_display_title(result_title)
    ga['tot_v'] += gb['tot_v']
    ga['tot_l'] += gb['tot_l']
    ga['tot_c'] += gb['tot_c']
    ga['tot_s'] += gb['tot_s']
    ga['n_platforms'] = len(ga['platforms'])

    groups.remove(gb)
    return groups


def apply_manual_group_merges(groups):
    if not os.path.exists(MANUAL_GROUP_MERGES_PATH):
        return groups
    with open(MANUAL_GROUP_MERGES_PATH, encoding='utf-8') as f:
        merges = json.load(f)
    for m in merges:
        groups = _merge_two_groups(groups, m['title_a'], m['title_b'], m['result_title'])
    return groups


def apply_title_renames(groups):
    renames = getattr(config, 'TITLE_RENAMES', {})
    if not renames:
        return groups
    lookup = {str(k).strip().lower(): str(v).strip() for k, v in renames.items() if k and v}
    for g in groups:
        key = g['title'].strip().lower()
        if key in lookup:
            g['title'] = lookup[key]

    # If any renames combined two groups under the same title, merge them
    merged = []
    by_title = {}
    for g in groups:
        k = g['title'].strip().lower()
        if k in by_title:
            target = by_title[k]
            for plat, entries in g['platforms'].items():
                target['platforms'].setdefault(plat, []).extend(entries)
            target['tot_v'] += g['tot_v']
            target['tot_l'] += g['tot_l']
            target['tot_c'] += g['tot_c']
            target['tot_s'] += g['tot_s']
            target['n_platforms'] = len(target['platforms'])
        else:
            by_title[k] = g
            merged.append(g)
    return merged


def main():
    with open(IN_PATH, encoding='utf-8') as f:
        posts = json.load(f)

    clusters = cluster(posts)
    groups = build_groups(clusters)
    groups = apply_manual_group_merges(groups)
    groups = apply_title_renames(groups)
    groups.sort(key=lambda g: -g['tot_v'])

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(groups, f, ensure_ascii=False, indent=2)
    print(f'Wrote {len(groups)} groups -> {OUT_PATH}')


if __name__ == '__main__':
    main()
