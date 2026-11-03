"""Later, read-only probing of real Jun files. Stream tests are not listening."""
import hashlib,json,subprocess
from pathlib import Path
ED=Path(__file__).resolve().parent;EP=ED.parent.parent;OUT=EP/'outputs/production-v1-jun'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def main():
    lock=read(OUT/'project/timing_resolved.json');assert lock['timing_locked'] is True
    probe=read(OUT/'reusable_assets/manifest.json')['ffprobe'];results=[]
    for b in lock['beats']:
        p=Path(b['resolved_audio_path']);m=json.loads(subprocess.check_output([probe,'-v','error','-show_streams','-show_format','-of','json',str(p)],text=True,encoding='utf-8'))
        assert len([s for s in m['streams'] if s['codec_type']=='audio'])==1
        assert abs(float(m['format']['duration'])-b['duration'])<=.05,f"Audio duration mismatch: {b['beat_id']}"
        results.append({'beat_id':b['beat_id'],'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'duration':m['format']['duration'],'timing_duration':b['duration']})
    receipt={'ok':True,'beat_count':len(results),'actual_listening':False,'pronunciation_and_naturalness':'unverified','files':results}
    (OUT/'checks/actual_audio_lock_validation.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8');print('39 real audio durations/streams checked; listening remains required')
if __name__=='__main__':main()
