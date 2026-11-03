"""Offline browser checks for the design prototype, not production feature QA."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
PAGE = ROOT / 'web/design/20261019/index.html'
CHROME = ROOT / 'video/node_modules/.remotion/chrome-headless-shell/win64/chrome-headless-shell-win64/chrome-headless-shell.exe'
results = []
with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=str(CHROME), headless=True)
    for width, height, name in [(1440, 1080, 'desktop'), (390, 844, 'mobile')]:
        page = browser.new_page(viewport={'width': width, 'height': height}, reduced_motion='reduce')
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto(PAGE.as_uri())
        page.screenshot(path=str(HERE / f'{name}_budget.png'), full_page=True)
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), 'Budget horizontal overflow'
        page.locator('#toRecommend').click()
        for step in range(6):
            page.locator('.choice').first.click()
            page.locator('#next').click()
        assert page.locator('#login').is_visible()
        page.keyboard.press('Escape')
        assert not page.locator('#login').is_visible()
        page.screenshot(path=str(HERE / f'{name}_recommend.png'), full_page=True)
        page.locator('[data-page="map"]').click()
        assert page.locator('#map').is_visible()
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), 'Map horizontal overflow'
        page.locator('[data-layer="schools"]').click()
        assert page.locator('#schools').evaluate('(e) => getComputedStyle(e).display') == 'none'
        page.screenshot(path=str(HERE / f'{name}_map.png'), full_page=True)
        assert not errors, errors
        assert page.evaluate('localStorage.length') == 0
        results.append(dict(viewport=[width, height], navigation=True, wizard_gate_modal=True,
                            escape_closes=True, layer_toggle=True, no_horizontal_overflow=True,
                            js_errors=errors, persistent_user_data=False))
        page.close()
    browser.close()
(HERE / 'prototype_checks.json').write_text(json.dumps(results, indent=2), encoding='utf-8')
print(json.dumps({'status': 'passed', 'viewports': len(results), 'screenshots': 6,
                  'scope': 'Offline design prototype only; no real auth, calculator or recommendation executed.'}))
