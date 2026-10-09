"""
Step 3 of the pipeline.

Injects data/processed/grouped.json into templates/dashboard_template.html's
__DATA_PLACEHOLDER__ and writes dist/dashboard.html.
"""
import json
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GROUPED_PATH = os.path.join(BASE, 'data', 'processed', 'grouped.json')
TEMPLATE_PATH = os.path.join(BASE, 'templates', 'dashboard_template.html')
OUT_PATH = os.path.join(BASE, 'dist', 'dashboard.html')


def main():
    with open(GROUPED_PATH, encoding='utf-8') as f:
        groups_json_text = f.read()
        json.loads(groups_json_text)  # validate

    with open(TEMPLATE_PATH, encoding='utf-8') as f:
        template = f.read()

    if '__DATA_PLACEHOLDER__' not in template:
        raise SystemExit('templates/dashboard_template.html is missing __DATA_PLACEHOLDER__')

    out = template.replace('__DATA_PLACEHOLDER__', groups_json_text)

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, 'w', encoding='utf-8') as f:
        f.write(out)
    print(f'Wrote {OUT_PATH} ({len(out)} bytes)')


if __name__ == '__main__':
    main()
