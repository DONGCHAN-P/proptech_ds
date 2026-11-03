"""Read-only cleanup audit; never deletes or moves an input."""
from pathlib import Path
import os,json,hashlib,collections,re,time,sys
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output/cleanup-20261015'
EP=ROOT/'video-agent-studio/episodes/namyangju-wangsuk-20261014'
OUT.mkdir(parents=True,exist_ok=True)
VERIFY_BUNDLE_CONTENT='--verify-bundle-content' in sys.argv
if '--bundle-followup' in sys.argv:
    data=json.loads((OUT/'inventory.json').read_text(encoding='utf-8'))
    digest_cache={};verified=[];deferred=[];counts=collections.Counter()
    def digest_cached(p):
        k=str(p.resolve());st=p.stat();key=(k,st.st_size,st.st_mtime_ns)
        if key not in digest_cache:
            h=hashlib.sha256()
            with p.open('rb') as f:
                for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
            digest_cache[key]=h.hexdigest()
        return digest_cache[key]
    for item in data['files']:
        if item['status']!='defer':continue
        p=Path(item['absolutePath']);r=item['relativePath'];bits=r.split('/')
        if 'public' not in bits:continue
        i=bits.index('public');canonical=ROOT/'video/public'/Path(*bits[i+1:]);row=dict(item)
        try:
            if not p.is_file():row.update(reason='source disappeared during root cleanup; no deletion action',status='defer')
            elif not canonical.is_file():row.update(reason='canonical video/public suffix not found; possible unique asset',status='defer')
            elif p.stat().st_size!=canonical.stat().st_size:row.update(reason='canonical file size differs; retain unique version',status='defer')
            else:
                original=digest_cached(p);canon=digest_cached(canonical)
                if original==canon:
                    row.update(status='delete',reason='full SHA256 identical canonical video/public asset',sha256=original,canonical_sha256=canon,finalrefs=[str(canonical.resolve())]);verified.append(row);continue
                row.update(reason='canonical full SHA256 differs; retain unique version',status='defer')
        except OSError as ex:row.update(reason='read failed; preserve: '+str(ex),status='defer')
        deferred.append(row)
    cache=[];cache_root=ROOT/'video/node_modules/.cache'
    if cache_root.is_dir():
        for d,ds,fs in os.walk(cache_root,followlinks=False):
            ds[:]=[n for n in ds if not Path(d,n).is_symlink() and not getattr(Path(d,n).stat(),'st_file_attributes',0)&1024]
            for n in fs:
                p=Path(d,n);st=p.stat(follow_symlinks=False)
                if p.is_symlink() or getattr(st,'st_file_attributes',0)&1024:continue
                cache.append({'absolutePath':str(p.resolve()),'relativePath':p.relative_to(ROOT).as_posix(),'bytes':st.st_size,'mtime_ns':st.st_mtime_ns,'status':'delete','reason':'Remotion/Webpack generated cache under explicitly scoped video/node_modules/.cache; installed packages excluded'})
    for name,rows in [('delete_bundle_verified.json',verified),('bundle_unique_deferred.json',deferred),('delete_cache.json',cache)]:
        obj={'root':str(ROOT),'actual_delete_performed':False,'files':rows,'summary':{'files':len(rows),'bytes':sum(x['bytes'] for x in rows)}}
        (OUT/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')
        counts[name+'_files']=len(rows);counts[name+'_bytes']=obj['summary']['bytes']
    s=OUT/'summary.md';v=s.read_text(encoding='utf-8');marker='## 추가 선택 가능 캐시'
    if marker in v:v=v.split(marker)[0]
    v=re.split(r'\n## \?[^\n]*\n',v,maxsplit=1)[0]
    v+='## 추가 검증 결과\n\n이 후속 결과는 1차 inventory/protected의 bundle public defer 판정보다 우선합니다. 번들 public 복사본은 대응하는 video/public 정본과 크기 및 전체 SHA256이 같을 때만 삭제 후보에 추가했습니다. 정본 해시는 파일 경로·크기·수정시각별로 한 번만 계산했습니다. 일치하지 않거나 정본이 없는 자료는 보존합니다.\n\n'
    for label,rows in [('검증된 번들 중복',verified),('고유 자료 또는 유보',deferred),('영상 전용 생성 캐시',cache)]:v+=f'- {label}: {len(rows):,}개 / {sum(x["bytes"] for x in rows)/1024**3:.3f} GiB\n'
    v+='\n캐시는 video/node_modules/.cache만 대상으로 하며 설치 패키지와 실행 바이너리는 제외했습니다. 실제 삭제는 총괄이 수행합니다.\n'
    s.write_text(v,encoding='utf-8');print(json.dumps(counts));sys.exit(0)
files=[]; errors=[]; links=[]; dirbytes=collections.Counter(); excluded=collections.Counter()
SKIP={'.git','node_modules','.venv','venv','tools','.aws','.codex','.agents'}
def walk(folder,skip=False):
    try:
        with os.scandir(folder) as it:
            for ent in it:
                try:
                    st=ent.stat(follow_symlinks=False)
                    if ent.is_symlink() or getattr(st,'st_file_attributes',0)&1024:
                        links.append(str(Path(ent.path).absolute()));continue
                    p=Path(ent.path);rel=p.relative_to(ROOT).as_posix()
                    ex=skip or ent.name in SKIP
                    if ent.is_dir(follow_symlinks=False):walk(p,ex)
                    elif ent.is_file(follow_symlinks=False):
                        for par in p.parents:
                            if par==ROOT:break
                            dirbytes[par.relative_to(ROOT).as_posix()]+=st.st_size
                        if ex:excluded[rel.split('/')[0]]+=st.st_size
                        else:files.append({'absolutePath':str(p.absolute()),'relativePath':rel,'bytes':st.st_size,'mtime_ns':st.st_mtime_ns})
                except OSError as e:errors.append({'path':ent.path,'error':str(e)})
    except OSError as e:errors.append({'path':str(folder),'error':str(e)})
walk(ROOT)
index={x['relativePath']:x for x in files}
def sha(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for c in iter(lambda:f.read(4*1024*1024),b''):h.update(c)
    return h.hexdigest()
protected={};evidence={}
def protect(rel,why):
    rel=str(rel).replace('\\','/')
    if rel in index:protected[rel]=why
def prefix(pre,why):
    for r in index:
        if r.startswith(pre):protect(r,why)
base='video-agent-studio/episodes/namyangju-wangsuk-20261014/'
protect(base+'outputs/locator-timeline-v14/namyangju_locator_timeline_full_v14.mp4','v15 assemble/mix/patch direct mandatory base; preserve as self-contained reconstruction input')
protect(base+'outputs/caption-station-v13/brand_outro_v13_no_caption.mp4','v15 assemble/mix direct brand outro input')
protect('video/out/newtown-v14-release.mp4','previous published final longform')
protect('video/out/newtown-v13-release-review.mp4','previous published shorts direct input in analysis/shorts_v1.py; predecessor of v14 release overlay')
for pre in ['video/public/','video/src/','video/assets/','video/out/release-v14/','video/shorts/','output/video_decisions/',base+'narration/',base+'research/',base+'visual/',base+'outputs/youtube-release-v15/',base+'outputs/shorts-release-v1/']:
    prefix(pre,'canonical source, reusable asset, narration/alignment, evidence or published release')
for r in index:
    if any(v in r.lower() for v in ['channel-brand','channel-intro','channel-outro','/bgm/','/music/','/source/','/sources/','/raw/','/original/']):
        if '/bundle' not in r and '-bundle/' not in r:protect(r,'original/reusable media, brand or source material')
# Protect source metadata globally. Retained exact final QA evidence, while old image samples may go.
for r in index:
    p=Path(r)
    if p.suffix.lower() in {'.json','.jsonl','.md','.txt','.csv','.tsv','.xlsx','.xls','.db','.sqlite','.sqlite3','.shp','.shx','.dbf','.prj','.geojson','.pdf','.svg','.py','.js','.cjs','.mjs','.ts','.tsx','.toml','.yaml','.yml','.srt','.vtt','.env','.pem','.key','.log','.html','.css','.sql'} and '/bundle' not in r and '-bundle/' not in r:
        protect(r,'small code/document/config/evidence/data retained by default; no historical evidence destruction')
prefix(base+'qa/readability-cta-v15/','canonical final QA evidence')
# Exact final MP4/SRT + latest ZIP; remove only duplicated delivery copies later by hash.
final=base+'outputs/readability-cta-v15/'
for name in ['namyangju_readability_cta_full_v15.mp4','namyangju_readability_cta_full_v15.srt','namyangju_readability_cta_v15_delivery.zip']:
    protect(final+name,'canonical final deliverable/latest validated delivery ZIP')
# Jobs record is the authority for published paths (both episodes).
for f in files:
    r=f['relativePath']
    if ('release-v14/' in r or 'youtube-release-v15/' in r) and r.endswith('.json'):
        try:
            obj=json.loads(Path(f['absolutePath']).read_text(encoding='utf-8-sig'))
            def visit(v):
                if isinstance(v,dict):
                    for a in v.values():visit(a)
                elif isinstance(v,list):
                    for a in v:visit(a)
                elif isinstance(v,str):
                    s=v.replace('\\','/')
                    if s.endswith(('.mp4','.jpg','.png','.zip')):protect(s,'release job/receipt explicitly references this artifact')
            visit(obj)
        except (ValueError,OSError):pass
rows=[]
for f in files:
    r=f['relativePath'];p=Path(f['absolutePath']);ext=p.suffix.lower();status='preserve';reason=protected.get(r,'uncertain asset/source dependency; retain');refs=[]
    bundle=any('bundle' in x.lower() for x in p.parts[:-1]) and (r.startswith(base+'editor/') or r.startswith('video/bundle'))
    if bundle:
        parts=r.split('/');pub=next((i for i,x in enumerate(parts) if x=='public'),None)
        if pub is None:
            status='delete';reason='generated Remotion bundle runtime; source code and dependency lock retained'
        else:
            canonical='video/public/'+'/'.join(parts[pub+1:]);c=index.get(canonical)
            if VERIFY_BUNDLE_CONTENT and c and c['bytes']==f['bytes'] and sha(c['absolutePath'])==sha(p):
                status='delete';reason='bundle public exact SHA256 duplicate of canonical reusable asset';refs=[canonical]
            else:status='defer';reason='bundle public exact SHA comparison deferred to keep cleanup bounded; preserve canonical and possible unique source'
    elif r not in protected:
        if r.startswith(base+'editor/') and (ext in {'.mp4','.f32','.m4a','.wav'} or '/frames/' in r):
            status='delete';reason='editor generated intermediate media/decoded PCM; canonical final/base, original voice and regeneration code retained'
        elif ext=='.mp4' and (r.startswith(base+'outputs/') or r.startswith('video/out/') or r.startswith('output/longform/')):
            status='delete';reason='superseded preview/intermediate render, not release job artifact or v15 mandatory base'
        elif ext=='.zip' and (r.startswith(base+'outputs/') or r.startswith('output/archive/')):
            status='delete';reason='superseded delivery ZIP; latest canonical final ZIP and originals retained'
        elif (ext in {'.png','.jpg','.jpeg','.webp'} and (r.startswith(base+'qa/') or r.startswith(base+'outputs/')) and any(s in p.name.lower() for s in ['actual_','sample','frame','preview','check','baseline','source_common','source_closing','source_cta','timeline_bbox_case','timeline_plate'])):
            if r.startswith(final):status='preserve';reason='current final render QA and exact regeneration input'
            else:status='delete';reason='historical generated QA/sample frame; JSON findings retained'
        elif '__pycache__/' in r or ext=='.pyc':status='delete';reason='regenerable Python bytecode cache'
    # Duplicate delivery full MP4s are safe only exact hash comparison to protected canonical.
    if 'delivery' in r and ext=='.mp4' and status!='preserve':
        candidates=[v for k,v in index.items() if k in protected and Path(k).name==p.name and v['bytes']==f['bytes']]
        for c in candidates:
            if sha(c['absolutePath'])==sha(p):refs=[c['relativePath']];reason='exact duplicate final MP4; canonical standalone final and latest ZIP retained';status='delete';break
    row=dict(f,status=status,reason=reason,finalrefs=refs)
    if r in protected:row['protectionEvidence']=protected[r]
    rows.append(row)
summary={s:{'files':sum(x['status']==s for x in rows),'bytes':sum(x['bytes'] for x in rows if x['status']==s)} for s in ['preserve','delete','defer']}
data={'root':str(ROOT),'generated_local':time.strftime('%Y-%m-%dT%H:%M:%S'),'read_only_audit':True,'files':rows,'summary':summary,'excluded_environment_bytes':dict(excluded),'top_directories':dict(dirbytes.most_common(80)),'excluded_reparse_paths':links,'scan_errors':errors}
def write(name,obj):(OUT/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')
write('inventory.json',data)
write('deletion_candidates.json',{'root':str(ROOT),'require_guide_complete':True,'actual_delete_performed':False,'files':[x for x in rows if x['status']=='delete'],'summary':summary['delete']})
write('protected.json',{'files':[x for x in rows if x['status']!='delete'],'summary':summary})
write('mp4_inventory.json',[x for x in rows if Path(x['relativePath']).suffix.lower()=='.mp4'])
gib=lambda n:f'{n/1024**3:.3f} GiB'
lines=['# 정리 전 읽기 전용 감사','',f"삭제 후보: {summary['delete']['files']:,}개 / {gib(summary['delete']['bytes'])}",f"보존: {summary['preserve']['files']:,}개 / {gib(summary['preserve']['bytes'])}",f"개별 확인 유보: {summary['defer']['files']:,}개 / {gib(summary['defer']['bytes'])}",'','실제 삭제·이동은 실행하지 않았습니다. 가이드 완료 후 총괄이 명시된 파일만 삭제해야 합니다. Downloads는 범위 밖입니다. reparse/symlink는 순회하지 않았습니다. .git·node_modules·tools·가상환경은 통계만 내고 후보에서 제외했습니다.','','## 최종 재현 의존성','', '- 왕숙 v15는 v14 전체 MP4(음성·미수정 지도·자막의 기준)와 v13 no-caption brand outro MP4를 직접 사용합니다. 두 파일은 보존했습니다. v14를 지우고 완전 재현 가능하다고 말하면 안 됩니다.','- v15 렌더 조각·PCM·번들은 코드로 다시 만들 수 있으므로 삭제 후보입니다. 최종 독립 MP4와 최신 ZIP은 보존합니다.','- 번들 public 자료는 video/public 원본과 SHA256이 정확히 같을 때만 삭제 후보입니다. 일치하지 않는 것은 유보합니다.','- 원본 음성·정렬·지도·계획도·CI·BGM·AI원본과 모든 작은 코드·문서·설정·승인·업로드 기록은 보존했습니다.','','## 상위 디렉터리','']+[f'- `{k}`: {gib(v)}' for k,v in dirbytes.most_common(25)]
(OUT/'summary.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
write('handoff.json',{'role':'cleanup_audit','input_revision':'published namyangju v15 and newtown v14','outputs':[str(OUT/x) for x in ['inventory.json','deletion_candidates.json','protected.json','mp4_inventory.json','summary.md']],'validation':'os.scandir; symlinks/reparse skipped; bundle public comparison deferred and kept; exact final delivery duplicate comparison where applicable; no input mutations','unresolved':'defer assets require individual source ownership review; final cleanup must wait guide complete','next_owner':'root','summary':summary})
print(json.dumps({'summary':summary,'output':str(OUT),'scan_errors':len(errors),'reparse':len(links)},ensure_ascii=False))
