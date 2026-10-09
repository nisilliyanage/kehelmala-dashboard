"""
Interactive CLI for manually merging two videos that the automatic cross-platform
matcher put into separate groups.

Usage:
    python src/merge_videos_cli.py

It will:
  1. List every current group title (with view counts, so you can tell them apart).
  2. Ask you to pick two titles to merge (by number or by typing the exact title).
  3. Ask which resulting title the merged group should take (defaults to the bigger
     of the two by total views).
  4. Record the merge in data/processed/manual_group_merges.json — a durable record
     that cluster_videos.py re-applies every time you re-run the pipeline on fresh
     weekly exports, so you never have to redo a merge.
  5. Apply the merge to the current data/processed/grouped.json immediately and
     rebuild dist/dashboard.html, so you can see the result right away.

You can also run it non-interactively:
    python src/merge_videos_cli.py --a "Title One" --b "Title Two" --result "Title One"
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src import cluster_videos  # noqa: E402

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GROUPED_PATH = os.path.join(BASE, 'data', 'processed', 'grouped.json')
MANUAL_GROUP_MERGES_PATH = os.path.join(BASE, 'data', 'processed', 'manual_group_merges.json')


def load_groups():
    if not os.path.exists(GROUPED_PATH):
        print(f'No {GROUPED_PATH} found yet. Run `python run.py` first to build it.')
        sys.exit(1)
    with open(GROUPED_PATH, encoding='utf-8') as f:
        return json.load(f)


def load_merge_log():
    if os.path.exists(MANUAL_GROUP_MERGES_PATH):
        with open(MANUAL_GROUP_MERGES_PATH, encoding='utf-8') as f:
            return json.load(f)
    return []


def save_merge_log(log):
    with open(MANUAL_GROUP_MERGES_PATH, 'w', encoding='utf-8') as f:
        json.dump(log, f, ensure_ascii=False, indent=2)


def print_titles(groups):
    for i, g in enumerate(groups, 1):
        plats = ', '.join(sorted(g['platforms'].keys()))
        print(f'  [{i:>3}] {g["title"]}  ({g["tot_v"]:,} total views; {plats})')


def resolve_title(groups, token, label):
    """Accepts either a list index (e.g. "12") or an exact/partial title."""
    token = token.strip()
    if token.isdigit():
        idx = int(token) - 1
        if 0 <= idx < len(groups):
            return groups[idx]['title']
        print(f'No group numbered {token}.')
        return None

    matches = [g for g in groups if g['title'].strip().lower() == token.lower()]
    if len(matches) == 1:
        return matches[0]['title']

    partial = [g for g in groups if token.lower() in g['title'].lower()]
    if len(partial) == 1:
        return partial[0]['title']
    if len(partial) > 1:
        print(f'"{token}" matches more than one title for {label} — be more specific, or use the list number:')
        print_titles(partial)
        return None

    print(f'No group title matches "{token}" for {label}.')
    return None


def do_merge(groups, title_a, title_b, result_title):
    groups = cluster_videos._merge_two_groups(groups, title_a, title_b, result_title)
    groups.sort(key=lambda g: -g['tot_v'])
    return groups


def rebuild_dashboard():
    import subprocess
    result = subprocess.run([sys.executable, os.path.join(BASE, 'src', 'build_dashboard.py')], cwd=BASE)
    return result.returncode == 0


def run_interactive():
    groups = load_groups()
    print(f'{len(groups)} groups currently in data/processed/grouped.json:\n')
    print_titles(groups)

    print('\nEnter the two titles to merge (by list number or exact/partial title).')
    tok_a = input('First video:  ').strip()
    title_a = resolve_title(groups, tok_a, 'the first video')
    if not title_a:
        return
    tok_b = input('Second video: ').strip()
    title_b = resolve_title(groups, tok_b, 'the second video')
    if not title_b:
        return
    if title_a.lower() == title_b.lower():
        print('Those are the same group already — nothing to merge.')
        return

    ga = next(g for g in groups if g['title'].lower() == title_a.lower())
    gb = next(g for g in groups if g['title'].lower() == title_b.lower())
    default_result = title_a if ga['tot_v'] >= gb['tot_v'] else title_b

    print(f'\nMerging:\n  A) {title_a}  ({ga["tot_v"]:,} views)\n  B) {title_b}  ({gb["tot_v"]:,} views)')
    result_title = input(f'Resulting title to use [{default_result}]: ').strip() or default_result

    confirm = input(f'\nMerge "{title_a}" + "{title_b}" -> "{result_title}"? [y/N] ').strip().lower()
    if confirm != 'y':
        print('Cancelled.')
        return

    groups = do_merge(groups, title_a, title_b, result_title)
    with open(GROUPED_PATH, 'w', encoding='utf-8') as f:
        json.dump(groups, f, ensure_ascii=False, indent=2)

    log = load_merge_log()
    log.append({'title_a': title_a, 'title_b': title_b, 'result_title': result_title})
    save_merge_log(log)

    ok = rebuild_dashboard()
    print(f'\nMerged. grouped.json updated, merge recorded in {os.path.relpath(MANUAL_GROUP_MERGES_PATH, BASE)}.')
    if ok:
        print('dist/dashboard.html rebuilt — publish it to update the live dashboard.')
    else:
        print('Rebuild of dist/dashboard.html failed — check the error above.')


def run_noninteractive(args):
    groups = load_groups()
    title_a = resolve_title(groups, args.a, '--a')
    title_b = resolve_title(groups, args.b, '--b')
    if not title_a or not title_b:
        sys.exit(1)
    result_title = args.result or title_a

    groups = do_merge(groups, title_a, title_b, result_title)
    with open(GROUPED_PATH, 'w', encoding='utf-8') as f:
        json.dump(groups, f, ensure_ascii=False, indent=2)

    log = load_merge_log()
    log.append({'title_a': title_a, 'title_b': title_b, 'result_title': result_title})
    save_merge_log(log)

    ok = rebuild_dashboard()
    print(f'Merged "{title_a}" + "{title_b}" -> "{result_title}".')
    if not ok:
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--a', help='First video title (or list number) — skips interactive prompts')
    parser.add_argument('--b', help='Second video title (or list number)')
    parser.add_argument('--result', help='Resulting title to use (defaults to --a)')
    args = parser.parse_args()

    if args.a and args.b:
        run_noninteractive(args)
    else:
        run_interactive()


if __name__ == '__main__':
    main()
