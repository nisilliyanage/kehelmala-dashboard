"""
Interactive CLI to undo a wrong merge — either one the automatic matcher made on its
own, or one made earlier via src/merge_videos_cli.py.

Usage:
    python src/unmerge_videos_cli.py

It will:
  1. List every current group with more than one platform entry (the only groups a
     wrong merge could hide in), with its title and which platforms/entries it holds.
  2. Ask you to pick the group to fix.
  3. List every individual entry in that group (one line per YouTube video / Facebook
     post / Instagram post / TikTok post it currently contains), numbered.
  4. Ask which entries to pull OUT into their own, separate group.
  5. Ask what title the new, split-off group should have.
  6. Split them out, recompute both groups' totals, and rebuild dist/dashboard.html
     immediately so you can check the result.

The split is recorded in data/processed/manual_group_splits.json as a block-list:
those specific entries are never clustered back together on a future pipeline run,
however similar their titles score — so an unmerge made today survives next week's
fresh exports without having to redo it. (This is separate from, and checked in
addition to, any entry in data/processed/manual_group_merges.json — if the group you're
splitting was created by a CLI merge recorded there, that now-stale merge record is
removed automatically so it can't immediately re-merge them.)

Non-interactive form, for scripting:
    python src/unmerge_videos_cli.py --group "Title" --take "YouTube:1,Facebook:0" --new-title "New Title"
    (--take platform:index pairs are 0-based within that platform's list, as shown by
    --list-entries)
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
MANUAL_GROUP_SPLITS_PATH = os.path.join(BASE, 'data', 'processed', 'manual_group_splits.json')


def load_groups():
    if not os.path.exists(GROUPED_PATH):
        print(f'No {GROUPED_PATH} found yet. Run `python run.py` first to build it.')
        sys.exit(1)
    with open(GROUPED_PATH, encoding='utf-8') as f:
        return json.load(f)


def save_groups(groups):
    with open(GROUPED_PATH, 'w', encoding='utf-8') as f:
        json.dump(groups, f, ensure_ascii=False, indent=2)


def load_json_list(path):
    if os.path.exists(path):
        with open(path, encoding='utf-8') as f:
            return json.load(f)
    return []


def save_json_list(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def mergeable_groups(groups):
    """Groups where a wrong merge could actually be hiding — more than one entry
    total, whether across platforms or within the same platform (e.g. two YouTube
    videos wrongly paired as Standard/Short)."""
    return [g for g in groups if sum(len(es) for es in g['platforms'].values()) > 1]


def print_groups(groups):
    for i, g in enumerate(groups, 1):
        n_entries = sum(len(es) for es in g['platforms'].values())
        plats = ', '.join(f'{p}×{len(es)}' if len(es) > 1 else p for p, es in g['platforms'].items())
        print(f'  [{i:>3}] {g["title"]}  ({n_entries} entries: {plats}; {g["tot_v"]:,} total views)')


def list_entries(group):
    """Returns a flat, numbered list of (platform, entry) for this group, in a
    stable order (platform insertion order, then by views desc, matching how
    they're stored)."""
    out = []
    for plat, entries in group['platforms'].items():
        for e in entries:
            out.append((plat, e))
    return out


def print_entries(entries):
    for i, (plat, e) in enumerate(entries, 1):
        label = f' [{e["label"]}]' if e.get('label') else ''
        url = e.get('u') or '(no link on file)'
        print(f'  [{i:>2}] {plat}{label} — {e["v"]:,} views — {url}')


def resolve_group(groups, token):
    token = token.strip()
    if token.isdigit():
        idx = int(token) - 1
        if 0 <= idx < len(groups):
            return groups[idx]
        print(f'No group numbered {token}.')
        return None
    matches = [g for g in groups if g['title'].strip().lower() == token.lower()]
    if len(matches) == 1:
        return matches[0]
    partial = [g for g in groups if token.lower() in g['title'].lower()]
    if len(partial) == 1:
        return partial[0]
    if len(partial) > 1:
        print(f'"{token}" matches more than one title — be more specific, or use the list number:')
        print_groups(partial)
        return None
    print(f'No group title matches "{token}".')
    return None


def _record_split(src_group, new_group):
    side_a = [cluster_videos.entry_identity(plat, e) for plat, es in src_group['platforms'].items() for e in es]
    side_b = [cluster_videos.entry_identity(plat, e) for plat, es in new_group['platforms'].items() for e in es]
    if not side_a or not side_b:
        return  # nothing left on one side (e.g. the group was just renamed) — no block needed
    splits = load_json_list(MANUAL_GROUP_SPLITS_PATH)
    splits.append({'side_a': side_a, 'side_b': side_b})
    save_json_list(MANUAL_GROUP_SPLITS_PATH, splits)


def _clean_stale_merge_record(original_title):
    """If this group's title matches the result_title of an earlier CLI merge
    (manual_group_merges.json), that merge record is now stale — remove it so the
    pipeline doesn't immediately try to re-merge on the next run."""
    merges = load_json_list(MANUAL_GROUP_MERGES_PATH)
    kept = [m for m in merges if m.get('result_title', '').strip().lower() != original_title.strip().lower()]
    removed = len(merges) - len(kept)
    if removed:
        save_json_list(MANUAL_GROUP_MERGES_PATH, kept)
        print(f'Removed {removed} now-stale entry/entries from '
              f'{os.path.relpath(MANUAL_GROUP_MERGES_PATH, BASE)} (it recorded a merge '
              f'into "{original_title}", which you just partly undid).')


def rebuild_dashboard():
    import subprocess
    result = subprocess.run([sys.executable, os.path.join(BASE, 'src', 'build_dashboard.py')], cwd=BASE)
    return result.returncode == 0


def do_split(groups, group_title, entries_to_move, new_title):
    groups, src, new_group = cluster_videos.split_group(groups, group_title, entries_to_move)
    new_group['title'] = new_title
    groups.sort(key=lambda g: -g['tot_v'])
    _record_split(src, new_group)
    return groups, src, new_group


def run_interactive():
    groups = load_groups()
    candidates = mergeable_groups(groups)
    if not candidates:
        print('No group currently has more than one entry — nothing to unmerge.')
        return
    print(f'{len(candidates)} group(s) with more than one entry (only these could hide a wrong merge):\n')
    print_groups(candidates)

    tok = input('\nWhich group do you want to fix? (number or title) ').strip()
    group = resolve_group(candidates, tok)
    if not group:
        return

    entries = list_entries(group)
    print(f'\n"{group["title"]}" currently has:')
    print_entries(entries)

    sel = input('\nWhich entries should be pulled OUT into their own group? '
                 '(comma-separated numbers, e.g. "2,4") ').strip()
    try:
        idxs = sorted({int(x.strip()) for x in sel.split(',') if x.strip()})
    except ValueError:
        print('Could not parse that as a list of numbers.')
        return
    if not idxs or any(i < 1 or i > len(entries) for i in idxs):
        print('Invalid selection.')
        return
    if len(idxs) == len(entries):
        print("That's every entry in the group — splitting all of them out isn't an "
              "unmerge, it would just rename the group. Leave at least one behind.")
        return

    to_move = [entries[i - 1] for i in idxs]
    print('\nPulling out:')
    print_entries(to_move)

    default_new_title = group['title']
    new_title = input(f'\nTitle for the new split-off group [{default_new_title}]: ').strip() or default_new_title

    confirm = input(f'\nSplit {len(to_move)} entr{"y" if len(to_move)==1 else "ies"} out of '
                     f'"{group["title"]}" into a new group "{new_title}"? [y/N] ').strip().lower()
    if confirm != 'y':
        print('Cancelled.')
        return

    original_title = group['title']
    groups, src, new_group = do_split(groups, original_title, to_move, new_title)
    save_groups(groups)
    _clean_stale_merge_record(original_title)

    ok = rebuild_dashboard()
    print(f'\nSplit done. "{src["title"]}" now has {sum(len(es) for es in src["platforms"].values())} '
          f'entr{"y" if sum(len(es) for es in src["platforms"].values())==1 else "ies"} '
          f'({src["tot_v"]:,} views); new group "{new_group["title"]}" has '
          f'{sum(len(es) for es in new_group["platforms"].values())} '
          f'({new_group["tot_v"]:,} views).')
    print(f'Recorded in {os.path.relpath(MANUAL_GROUP_SPLITS_PATH, BASE)} so this split survives future runs.')
    if ok:
        print('dist/dashboard.html rebuilt — publish it to update the live dashboard.')
    else:
        print('Rebuild of dist/dashboard.html failed — check the error above.')


def run_noninteractive(args):
    groups = load_groups()
    group = resolve_group(groups, args.group)
    if not group:
        sys.exit(1)
    entries = list_entries(group)

    to_move = []
    for spec in args.take.split(','):
        plat, idx = spec.split(':')
        plat_entries = group['platforms'].get(plat.strip())
        if plat_entries is None:
            print(f'Group has no platform "{plat}". Platforms present: {list(group["platforms"])}')
            sys.exit(1)
        i = int(idx)
        if not (0 <= i < len(plat_entries)):
            print(f'{plat} only has {len(plat_entries)} entr(y/ies) (0-indexed); got index {i}.')
            sys.exit(1)
        to_move.append((plat.strip(), plat_entries[i]))

    if len(to_move) == len(entries):
        print("That's every entry in the group — refusing (would just rename the group).")
        sys.exit(1)

    original_title = group['title']
    new_title = args.new_title or original_title
    groups, src, new_group = do_split(groups, original_title, to_move, new_title)
    save_groups(groups)
    _clean_stale_merge_record(original_title)
    ok = rebuild_dashboard()
    print(f'Split {len(to_move)} entr(y/ies) out of "{original_title}" into "{new_title}".')
    if not ok:
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--group', help='Group title (or list number) to split — skips interactive prompts')
    parser.add_argument('--take', help='Comma-separated "Platform:index" pairs to pull out, e.g. "YouTube:1,Facebook:0"')
    parser.add_argument('--new-title', help='Title for the new split-off group (defaults to the original title)')
    parser.add_argument('--list-entries', metavar='GROUP', help='Just print the numbered entries for GROUP (title or list number) and exit')
    args = parser.parse_args()

    if args.list_entries:
        groups = load_groups()
        group = resolve_group(groups, args.list_entries)
        if not group:
            sys.exit(1)
        entries = list_entries(group)
        print(f'"{group["title"]}":')
        for i, (plat, e) in enumerate(entries):
            label = f' [{e["label"]}]' if e.get('label') else ''
            print(f'  {plat}:{i}{label} — {e["v"]:,} views — {e.get("u") or "(no link on file)"}')
        return

    if args.group and args.take:
        run_noninteractive(args)
    else:
        run_interactive()


if __name__ == '__main__':
    main()
