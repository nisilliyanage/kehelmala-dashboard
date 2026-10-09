"""Runs the full pipeline: merge_platforms -> cluster_videos -> build_dashboard."""
import subprocess
import sys
import os

BASE = os.path.dirname(os.path.abspath(__file__))
STEPS = ['src/merge_platforms.py', 'src/cluster_videos.py', 'src/build_dashboard.py']

for step in STEPS:
    print(f'\n=== {step} ===')
    result = subprocess.run([sys.executable, os.path.join(BASE, step)], cwd=BASE)
    if result.returncode != 0:
        print(f'{step} failed, stopping.')
        sys.exit(result.returncode)

print('\nDone. Open dist/dashboard.html or publish it.')
