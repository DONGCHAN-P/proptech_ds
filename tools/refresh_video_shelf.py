"""Maintain short user-facing NTFS paths without moving production dependencies."""
from pathlib import Path
import os, json, hashlib, datetime

ROOT=Path(__file__).resolve().parents[1]
def inside(path):
    p=(ROOT/path).resolve()
    p.relative_to(ROOT)
    return p
def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(4*1024*1024),b''):h.update(block)
    return h.hexdigest()
def refresh():
    cfg=json.loads((ROOT/'config/video_shelf.json').read_text(encoding='utf8'))
    shelf=inside(cfg['shelf']);shelf.mkdir(exist_ok=True)
    manifest=shelf/'경로목록.json'
    previous=json.loads(manifest.read_text(encoding='utf8')) if manifest.exists() else {'files':[]}
    old={r['alias']:r for r in previous['files']}
    # Preflight every source and every replacement before changing any managed link.
    plans=[]
    for entry in cfg['entries']:
        folder=(shelf/entry['name']).resolve();folder.relative_to(shelf)
        for filename,source in entry['files'].items():
            target=inside(source)
            if not target.is_file():raise FileNotFoundError(target)
            dest=(folder/filename).resolve();dest.relative_to(shelf)
            key=dest.relative_to(ROOT).as_posix();same=dest.exists() and os.path.samefile(dest,target)
            if dest.exists() and not same:
                prior=old.get(key)
                if not prior or digest(dest)!=prior['sha256']:
                    raise RuntimeError(f'보존: 관리되지 않았거나 수정된 파일 {dest}')
            plans.append((dest,target,key,same))
        junction=folder/'작업폴더';target=inside(entry['workspace'])
        if not target.is_dir():raise NotADirectoryError(target)
        if os.path.lexists(junction) and not os.path.samefile(junction,target):
            raise RuntimeError(f'보존: 다른 작업폴더 연결 {junction}')
    records=[]
    for dest,target,key,same in plans:
        dest.parent.mkdir(exist_ok=True)
        if not same:
            if dest.exists():dest.unlink() # Only a verified, manifest-managed file alias.
            os.link(target,dest)
        assert os.path.samefile(dest,target)
        records.append({'alias':key,'source':target.relative_to(ROOT).as_posix(),'sha256':digest(target),'bytes':target.stat().st_size,'type':'NTFS hardlink'})
    for entry in cfg['entries']:
        folder=shelf/entry['name'];junction=folder/'작업폴더';target=inside(entry['workspace'])
        if not os.path.lexists(junction):
            import _winapi
            _winapi.CreateJunction(str(target),str(junction))
        assert os.path.samefile(junction,target)
        lines=[f"# {entry['name']}",'',entry['status'],'','- `영상.mp4`: 현재 기준 영상','- `자막.srt`: 해당 영상 자막','- `작업폴더`: 기존 제작 폴더로 연결','',
               '짧은 경로의 파일은 원본과 같은 NTFS 파일입니다. 내용을 수정하면 원본에도 반영될 수 있습니다. 버전 작업은 작업폴더의 원래 파일에서 진행하고 완료 후 이 목록을 갱신합니다.','',
               '## 현재 연결 원본','']
        for row in records:
            if Path(row['alias']).parent.name==entry['name']:lines.append(f"- `{Path(row['alias']).name}` → `{row['source']}`")
        (folder/'파일안내.md').write_text('\n'.join(lines)+'\n',encoding='utf8')
    report={'updated_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'strategy':'short hardlinks + workspace junctions; original production paths preserved','original_files_moved':0,'original_files_deleted':0,'additional_media_data_bytes':0,'files':records,'workspaces':[{'alias':(shelf/e['name']/'작업폴더').relative_to(ROOT).as_posix(),'source':e['workspace']} for e in cfg['entries']]}
    manifest.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
    (shelf/'README.md').write_text('# 영상 파일은 여기서 찾으세요\n\n편별 폴더의 `영상.mp4`, `대본.md`, `자막.srt`를 사용합니다. 상세 제작 자료와 과거 버전은 `작업폴더` 안에 있습니다.\n\n'+ '\n'.join(f"- [{e['name']}]({e['name']}/파일안내.md): {e['status']}" for e in cfg['entries'])+'\n\n원본 파일은 이동·삭제하지 않았습니다. 큰 영상은 복사본이 아닌 하드링크이므로 저장 데이터가 추가되지 않습니다.\n\n새 버전 완료 시 `config/video_shelf.json`의 연결 원본과 상태를 갱신한 뒤 `tools/python311/python.exe -X utf8 tools/refresh_video_shelf.py`를 실행합니다. 승인·출처·검수 기록은 원래 제작 경로를 유지합니다.\n',encoding='utf8')
    print(json.dumps({'shelf':str(shelf),'files':len(records),'workspaces':len(cfg['entries']),'originals_moved_or_deleted':0,'additional_media_data_bytes':0},ensure_ascii=False))
if __name__=='__main__':refresh()
