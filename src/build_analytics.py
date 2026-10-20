"""
Builds the second, chart-based analytics page.

Reads data/processed/grouped.json (same data the main list dashboard uses) and
injects it into templates/analytics_template.html, writing docs/analytics.html.
Run as part of run.py, right after build_dashboard.py.
"""
import json
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GROUPED_PATH = os.path.join(BASE, 'data', 'processed', 'grouped.json')
TEMPLATE_PATH = os.path.join(BASE, 'templates', 'analytics_template.html')
OUT_PATH = os.path.join(BASE, 'docs', 'analytics.html')


def main():
    with open(GROUPED_PATH, encoding='utf-8') as f:
        groups_json_text = f.read()
        json.loads(groups_json_text)  # validate

    with open(TEMPLATE_PATH, encoding='utf-8') as f:
        template = f.read()

    if '__DATA_PLACEHOLDER__' not in template:
        raise SystemExit('templates/analytics_template.html is missing __DATA_PLACEHOLDER__')

    out = template.replace('__DATA_PLACEHOLDER__', groups_json_text)

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, 'w', encoding='utf-8') as f:
        f.write(out)
    print(f'Wrote {OUT_PATH} ({len(out)} bytes)')


if __name__ == '__main__':
    main()
