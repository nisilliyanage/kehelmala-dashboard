"""
Step 3 of the pipeline.

Injects data/processed/grouped.json into templates/dashboard_template.html's
__DATA_PLACEHOLDER__ and writes docs/index.html - the page GitHub Pages serves
as the site's home page.
"""
import json
import os
import shutil

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GROUPED_PATH = os.path.join(BASE, 'data', 'processed', 'grouped.json')
TEMPLATE_PATH = os.path.join(BASE, 'templates', 'dashboard_template.html')
OUT_PATH = os.path.join(BASE, 'docs', 'index.html')
LOGO_SRC = os.path.join(BASE, 'assets', 'logo.png')
LOGO_OUT = os.path.join(BASE, 'docs', 'logo.png')


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

    # The sidebar logo (index.html and analytics.html both reference
    # "logo.png" as a sibling file) - copied fresh from assets/ on every
    # build so docs/ never goes stale against it.
    if os.path.exists(LOGO_SRC):
        shutil.copyfile(LOGO_SRC, LOGO_OUT)
        print(f'Copied {LOGO_SRC} -> {LOGO_OUT}')
    else:
        print(f'Note: {LOGO_SRC} not found - sidebar will show the "K" placeholder instead')


if __name__ == '__main__':
    main()
