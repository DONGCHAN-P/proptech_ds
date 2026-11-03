"""Real local-server browser flow; synthetic review accounts, no paid calls."""
from pathlib import Path
import json
import uuid
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output/jipgorithm-review-v1'
OUT.mkdir(parents=True, exist_ok=True)
CHROME = ROOT / 'video/node_modules/.remotion/chrome-headless-shell/win64/chrome-headless-shell-win64/chrome-headless-shell.exe'
BASE = 'http://127.0.0.1:8010'
report = []
with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=str(CHROME), headless=True)
    for width, height, name in [(1440, 1000, 'desktop'), (390, 844, 'mobile')]:
        context = browser.new_context(viewport={'width': width, 'height': height})
        page = context.new_page()
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto(BASE, wait_until='networkidle')
        assert context.request.post(BASE + '/api/match', data={}).status == 401
        page.locator('#calculate').click()
        page.wait_for_function("document.querySelector('#resultPrice').textContent !== '—'")
        assert page.locator('#resultActions').is_visible()
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), 'Home overflow'
        page.screenshot(path=str(OUT / f'{name}_budget.png'), full_page=True)
        page.locator('#saveBudget').click()
        page.locator('.jg-switch').click()
        page.locator('.jg-dialog input[name="email"]').fill('browser-' + uuid.uuid4().hex[:12] + '@example.invalid')
        page.locator('.jg-dialog input[name="password"]').fill(uuid.uuid4().hex)
        page.locator('.jg-submit').click()
        page.wait_for_function("document.querySelector('.jg-back').hidden")
        page.wait_for_function("document.querySelector('#formStatus').textContent.includes('보관')")
        assert 'jip_session' not in page.evaluate('document.cookie'), 'Session must be HttpOnly'
        page.locator('#findWithBudget').click()
        page.wait_for_function('window.WIZ && window.JIP')
        # Exercise the real six-step UI: household, budget, area, work, region, priorities.
        page.locator('.opt[data-k="couple"]').click()
        page.locator('#budgetRange').wait_for(state='visible')
        page.locator('#nextBtn').click()
        page.wait_for_timeout(400)
        page.locator('#nextBtn').click()
        page.locator('#workSkip').wait_for(state='visible')
        page.locator('#workSkip').click()
        page.wait_for_timeout(400)
        page.locator('#nextBtn').click()
        page.wait_for_timeout(400)
        page.locator('#nextBtn').click()
        page.locator('#result').wait_for(state='visible', timeout=120000)
        page.wait_for_timeout(1000)
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), 'Results overflow'
        assert page.locator('.rcard').count() <= 5
        page.screenshot(path=str(OUT / f'{name}_recommendation.png'), full_page=True)
        page.locator('#shareBtn').click()
        page.wait_for_timeout(500)
        page.goto(BASE + '/saved.html', wait_until='networkidle')
        page.wait_for_function("document.querySelectorAll('#items article').length >= 2")
        page.screenshot(path=str(OUT / f'{name}_saved.png'), full_page=True)
        page.goto(BASE + '/explore.html', wait_until='domcontentloaded')
        page.wait_for_function('typeof L !== "undefined"', timeout=30000)
        page.wait_for_timeout(2000)
        assert page.locator('.leaflet-jipBoundaries-pane canvas, .leaflet-jipBoundaries-pane path').count() > 0 or page.locator('.leaflet-tile-loaded').count() > 0, 'Missing geographic basemap'
        page.screenshot(path=str(OUT / f'{name}_map.png'), full_page=True)
        assert not errors, errors
        report.append(dict(viewport=[width,height], actual_budget=True, signup=True,
                           six_step_recommendation=True, private_saved_items=True,
                           http_only_session=True, public_map=True, js_errors=errors))
        context.close()
    browser.close()
(OUT / 'browser_checks.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf8')
print(json.dumps({'status':'passed','viewports':len(report),'screenshots':8,'real_backend':True}))
