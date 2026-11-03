"""Check local report links, images, responsive layout and case explorer."""
from pathlib import Path
from urllib.parse import unquote
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
import csv
import io
import json
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from diagnostics import OUT,sha,save

def run():
    report=OUT.parent.parent/'reports/지역별 집값 예측 실패 진단.html'
    soup=BeautifulSoup(report.read_text('utf-8'),'html.parser')
    ids=[node['id'] for node in soup.select('[id]')]
    assert len(ids)==len(set(ids))
    checked=0
    for anchor in soup.select('a[href]'):
        link=anchor['href']
        if link.startswith(('https:','http:')):continue
        if link.startswith('#'):assert link[1:] in ids
        else:assert (report.parent/unquote(link)).resolve().exists(),link
        checked+=1
    assert len(soup.select('img'))==5
    assert all(node['src'].startswith('data:image/png;base64,') for node in soup.select('img'))
    qa=OUT/'html_qa';qa.mkdir(exist_ok=True)
    errors=[];requests=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True)
        page=browser.new_page(viewport={'width':1440,'height':1050},accept_downloads=True)
        page.on('pageerror',lambda error:errors.append(str(error)))
        page.on('request',lambda request:requests.append(request.url))
        page.goto(report.as_uri(),wait_until='load');page.wait_for_selector('body[data-ready="true"]')
        assert page.locator('#case-table tr').count()==25
        page.screenshot(path=str(qa/'desktop-top.png'))
        assert page.locator('img').evaluate_all('(xs)=>xs.every(x=>x.complete&&x.naturalWidth>0)')
        page.locator('#case-level').select_option('district')
        page.locator('#case-search').fill('서대문')
        assert page.locator('#case-table tr').count()==1
        assert '33.26%' in page.locator('#case-table').inner_text()
        page.locator('#case-search').fill('없는지역xyz')
        assert '검색 결과가 없습니다' in page.locator('#case-table').inner_text()
        page.locator('#case-search').fill('')
        with page.expect_download() as download:page.locator('#case-download').click()
        path=qa/'selected_cases.csv';download.value.save_as(path)
        rows=list(csv.DictReader(io.StringIO(path.read_text('utf-8-sig'))))
        assert len(rows)==25 and all(row['level']=='district' for row in rows)
        page.locator('#cases').scroll_into_view_if_needed()
        page.screenshot(path=str(qa/'desktop-cases.png'))
        widths=[]
        for width in [1440,1024,768,390]:
            page.set_viewport_size({'width':width,'height':1000})
            page.evaluate('window.scrollTo(0,0)')
            dimensions=page.evaluate('({width:innerWidth,scroll:document.documentElement.scrollWidth})')
            assert dimensions['scroll']<=width+1,dimensions
            assert not page.locator('h1,h2,.kpi strong').evaluate_all('(xs)=>xs.some(x=>x.scrollWidth>x.clientWidth+2)')
            widths.append(dimensions)
            if width==390:
                page.screenshot(path=str(qa/'mobile-top.png'))
                page.locator('#section-5').scroll_into_view_if_needed()
                page.screenshot(path=str(qa/'mobile-findings.png'))
        page.set_viewport_size({'width':1024,'height':1050});page.emulate_media(media='print')
        page.evaluate('window.scrollTo(0,0)');page.screenshot(path=str(qa/'print-preview.png'))
        assert not errors,errors
        assert all(url.startswith(('file:','data:','blob:')) for url in requests)
        browser.close()
    result={'report_sha256':sha(report),'local_links_and_anchors_checked':checked,'embedded_figures':5,
            'unique_ids':len(ids),'search_filter_download_checked':True,'download_rows':len(rows),
            'responsive_widths':widths,'javascript_errors':errors,'external_resource_requests':0,'passed':True}
    save(qa/'browser_checks.json',result)
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__':run()
