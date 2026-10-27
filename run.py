"""Runs the full pipeline: merge_platforms -> cluster_videos -> build_dashboard,
then saves a dated snapshot of the processed data to data/snapshots/."""
import datetime
import shutil
import subprocess
import sys
import os

BASE = os.path.dirname(os.path.abspath(__file__))
STEPS = ['src/merge_platforms.py', 'src/cluster_videos.py', 'src/build_dashboard.py', 'src/build_analytics.py']
# Files copied into each snapshot - everything needed to see what the dashboard
# showed on that date without re-running anything.
SNAPSHOT_FILES = ['data/processed/all_posts.json', 'data/processed/grouped.json',
                  'data/processed/manual_group_merges.json']

for step in STEPS:
    print(f'\n=== {step} ===')
    result = subprocess.run([sys.executable, os.path.join(BASE, step)], cwd=BASE)
    if result.returncode != 0:
        print(f'{step} failed, stopping.')
        sys.exit(result.returncode)

# One folder per run date (re-running on the same day overwrites that day's copy).
snap_dir = os.path.join(BASE, 'data', 'snapshots', datetime.date.today().isoformat())
os.makedirs(snap_dir, exist_ok=True)
for rel in SNAPSHOT_FILES:
    src = os.path.join(BASE, rel)
    if os.path.exists(src):
        shutil.copy2(src, snap_dir)
print(f'\nSnapshot saved -> {os.path.relpath(snap_dir, BASE)}')

print('\nDone. Open docs/index.html to check it, then commit and push to publish.')
