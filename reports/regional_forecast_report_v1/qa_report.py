"""Inspect the generated offline report and exercise its browser controls."""
from pathlib import Path
from urllib.parse import unquote
import csv
import hashlib
import io
import json
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

HERE=Path(__file__).resolve().parent
REPORT=HERE.parent/'지역별 집값 예측 반복 검증.html'
QA=HERE/'qa';QA.mkdir(exist_ok=True)
soup=BeautifulSoup(REPORT.read_text('utf-8'),'html.parser')
data=json.loads(soup.select_one('#report-data').string)
ids=[tag['id'] for tag in soup.select('[id]')]
assert len(ids)==len(set(ids)),'Duplicate IDs'
links=0
for anchor in soup.select('a[href]'):
    href=anchor['href']
    if href.startswith(('https:','http:')):continue
    if href.startswith('#'):assert href[1:] in ids,href
    else:assert (REPORT.parent/unquote(href)).resolve().exists(),href
    links+=1
checks={'local_links_and_anchors':links,'self_contained':not bool(soup.select('script[src],link[href],img[src]')),
        'unique_ids':len(ids),'score_rows':len(data['scores']),'regional_rows':len(data['regional'])}
errors=[];requests=[]
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True)
    context=browser.new_context(viewport={'width':1440,'height':1050},device_scale_factor=1,accept_downloads=True)
    page=context.new_page()
    page.on('pageerror',lambda error:errors.append(str(error)))
    page.on('request',lambda request:requests.append(request.url))
    page.goto(REPORT.as_uri(),wait_until='load')
    page.wait_for_selector('body[data-ready="true"]')
    page.screenshot(path=str(QA/'desktop-top.png'))
    assert page.locator('#model-bars .rank-row').count()==9
    assert page.locator('#error-line circle').count()==38
    assert page.locator('#coverage-chart rect').count()==8
    page.locator('#error-line circle').first.focus()
    assert '2017-01' in page.locator('#line-readout').inner_text()
    assert page.locator('#forecast-table tr').count()==11
    expected_forecast=next(r for r in data['forecasts'] if r['name']=='서울' and r['level']=='province')
    forecast_row=page.locator('#forecast-table tr').filter(has=page.get_by_role('rowheader',name='서울',exact=True))
    assert forecast_row.locator('td').first.inner_text()==f'{expected_forecast["baseline_pct"]:+.2f}%'
    comparisons=[]
    for window in ['all_regimes','boom','turn','recent']:
        page.locator('#period').select_option(window)
        for level in ['province','district']:
            page.locator('#level').select_option(level)
            a=next(r for r in data['scores'] if r['window']==window and r['level']==level and r['model']=='v3_hgb')
            b=next(r for r in data['scores'] if r['window']==window and r['level']==level and r['model']=='hgb_t2_120m')
            row=page.locator('#metrics-table tr').first
            assert row.locator('td').nth(0).inner_text()==f'{a["mae_pp"]:.3f}'
            assert row.locator('td').nth(1).inner_text()==f'{b["mae_pp"]:.3f}'
            shown=int(page.locator('#regions-caption').inner_text().split(' · ')[-1].replace('개 지역',''))
            expected=len([r for r in data['regional'] if r['window']==window and r['level']==level and r['model']=='hgb_t2_120m'])
            assert shown==expected
            comparisons.append(dict(window=window,level=level,regions=shown,mae_old=a['mae_pp'],mae_candidate=b['mae_pp']))
    checks['period_level_combinations']=comparisons
    page.locator('#metric').select_option('balanced_mae_pp')
    assert '균형 MAE' in page.locator('#rank-title').inner_text()
    page.locator('#metric').select_option('p90_ae_pp')
    assert 'p90' in page.locator('#rank-title').inner_text()
    page.locator('#period').select_option('all_regimes')
    page.locator('#region-search').fill('서울')
    assert page.locator('#region-table tr').count()>0
    assert all('서울' in x for x in page.locator('#region-table th').all_text_contents())
    page.locator('#region-search').fill('없는지역xyz')
    assert '검색 결과가 없습니다' in page.locator('#region-table').inner_text()
    page.locator('#region-search').fill('')
    page.locator('#next-page').click()
    assert page.locator('#page-caption').inner_text().startswith('21–')
    page.locator('#prev-page').click()
    page.locator('#region-sort').select_option('worse')
    assert '-' in page.locator('#region-table tr').first.inner_text()
    checks['search_sort_pagination']=True
    with page.expect_download() as pending:
        page.locator('#download-scores').click()
    downloaded=pending.value
    dest=QA/'downloaded_scores.csv';downloaded.save_as(dest)
    downloaded_rows=list(csv.DictReader(io.StringIO(dest.read_text('utf-8-sig'))))
    assert len(downloaded_rows)==32
    with page.expect_download() as pending:
        page.locator('#download-regions').click()
    dest=QA/'downloaded_regions.csv';pending.value.save_as(dest)
    downloaded_regions=list(csv.DictReader(io.StringIO(dest.read_text('utf-8-sig'))))
    assert len(downloaded_regions)==119
    checks['csv_downloads']={'models':len(downloaded_rows),'regions':len(downloaded_regions)}
    with page.expect_download() as pending:
        page.locator('#download-forecasts').click()
    dest=QA/'downloaded_forecasts.csv';pending.value.save_as(dest)
    downloaded_forecasts=list(csv.DictReader(io.StringIO(dest.read_text('utf-8-sig'))))
    assert len(downloaded_forecasts)==130
    checks['csv_downloads']['forecasts']=len(downloaded_forecasts)
    page.locator('#metric').select_option('mae_pp')
    page.locator('#period').select_option('recent')
    page.locator('#level').select_option('province')
    page.locator('#performance').scroll_into_view_if_needed()
    page.screenshot(path=str(QA/'desktop-performance.png'))
    page.locator('#regions').scroll_into_view_if_needed()
    page.screenshot(path=str(QA/'desktop-regions.png'))
    page.locator('#intervals').scroll_into_view_if_needed()
    page.screenshot(path=str(QA/'desktop-intervals.png'))
    layout=[]
    for width in [1440,1024,768,390]:
        page.set_viewport_size({'width':width,'height':950})
        page.evaluate('window.scrollTo(0,0)')
        dimensions=page.evaluate('({width:innerWidth,scroll:document.documentElement.scrollWidth})')
        assert dimensions['scroll']<=width+1,dimensions
        clipped=page.locator('h1,h2,h3,.finding strong,.kpi strong').evaluate_all('(nodes)=>nodes.filter(n=>n.scrollWidth>n.clientWidth+2).map(n=>n.textContent)')
        assert not clipped,clipped
        layout.append(dimensions)
        if width==390:
            page.screenshot(path=str(QA/'mobile-top.png'))
            page.locator('#performance').scroll_into_view_if_needed()
            page.screenshot(path=str(QA/'mobile-performance.png'))
            page.locator('#regions').scroll_into_view_if_needed()
            page.screenshot(path=str(QA/'mobile-regions.png'))
    checks['responsive_widths']=layout
    page.set_viewport_size({'width':1024,'height':1050})
    page.emulate_media(media='print')
    page.evaluate('window.scrollTo(0,0)')
    page.screenshot(path=str(QA/'print-preview.png'))
    checks['print_preview']=True
    assert not errors,errors
    assert all(url.startswith(('file:','blob:','data:')) for url in requests),requests
    checks['javascript_errors']=errors
    checks['external_requests']=0
    browser.close()
checks['report_sha256']=hashlib.sha256(REPORT.read_bytes()).hexdigest()
checks['passed']=True
(QA/'browser_checks.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2),'utf-8')
print(json.dumps(checks,ensure_ascii=False,indent=2))
