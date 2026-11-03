import json,hashlib,subprocess
from pathlib import Path
q=Path(__file__).parent;ep=q.parents[1];out=ep/'outputs/production-v8-labels';old=ep/'outputs/production-v8-preview'
def rd(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def wr(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
v=out/'changneung_full_v8_labels.mp4';expected='791edec8d1ade9b13d2e3dfd9f240dd7bf56e40ebc02dbb5f5d8643c8889b5c3';assert sha(v)==expected
snap=rd(ep/'editor/production-v8-labels/input_snapshot.json');assert all(sha(Path(x['path']))==x['sha256'] for x in snap)
before=(old/'changneung_v8_preview.srt').read_text(encoding='utf-8-sig').strip().split('\n\n');after=(out/'changneung_v8_labels.srt').read_text(encoding='utf-8-sig').strip().split('\n\n');assert len(before)==len(after)==213
diff=[]
for a,b in zip(before,after):
 aa=a.splitlines();bb=b.splitlines();assert aa[:2]==bb[:2]
 if aa[2:]!=bb[2:]:diff.append({'index':aa[0],'time':aa[1],'before':' '.join(aa[2:]),'after':' '.join(bb[2:])})
assert len(diff)==3
ff=Path('C:/projects/realestate_reco/video/node_modules/@remotion/compositor-win32-x64-msvc/ffmpeg.exe')
audio=[]
for label,source in [('before',old/'changneung_full_v8_preview.mp4'),('after',v)]:
 target=q/(label+'_identity.aac')
 r=subprocess.run([str(ff),'-v','error','-y','-i',str(source),'-map','0:a:0','-c:a','copy','-f','adts',str(target)],capture_output=True,text=True)
 assert r.returncode==0 and not r.stderr
 audio.append(sha(target))
assert audio[0]==audio[1]
report={'status':'passed_with_limits','checked_revision':expected,'file':'outputs/production-v8-labels/changneung_full_v8_labels.mp4','bytes':v.stat().st_size,'required_unresolved':[],'critical_open':[],'scope':'v8.1 시설번호→예정부지 표시/3자막/지도라벨 리더 국소검수. 불변영역은 v8 QA승계','coverage':{'actual_encoded_samples':26,'sheets_viewed':3,'full_resolution_key_frames':[25796,25021,24818,23586],'mobile512_viewed':4,'actual_listening':False,'continuous_human_playback':False},'technical_independent':{'method':'local ffprobe count_frames full video/audio decode','exit_code':0,'stderr':'','video_frames':31790,'audio_frames':49672,'duration_s':1059.666667,'video':'H264 1920x1080 30fps','audio':'AAC 48000Hz 2ch','sha_match':True,'aac_adts_sha256':audio[0],'audio_bitstream_before_after_identical':True},'caption_diff':diff,'caption_timestamps_and_213_count_identical':True,'input_snapshot_hashes_unchanged':True,'verified':['S1 f25796 학교·유치원 우측2슬롯과 원필지앵커리더, 하천계획·공원계획과 텍스트겹침 해소 직접확인','S4/S5/생활필지 예정부지라벨·locator·입주/개교목표·미정 유지, 시설코드는화면일반표현으로교체; 내부원자료코드는보존','S5 2028.03개교목표/S4입주예정월과같은2030.03목표/S1개교미정, 수정3문장주어자연스러움·단위날짜보호 확인','변경시작끝 인접표본과확대단계/모바일에서잘림·본문자막가림·학교라벨서로겹침없음','출처자막아래/계획위치·목표와실제개교구분 유지','새최종SHA·기술전체decode·213자막시간불변·3표시문구변경·AACstream자체동일검사'],'inherited_review':{'file':'qa/production-v8-preview/final_review.json','source_video_sha256':'5131dbfe48a203ffa13d3ca9104c23baf9d53038880b8b99b4f4266eb39567c8','scope':'본패치변경외구간·사실·음성·타임록. 과거표본을새SHA프레임이라고주장하지않음'},'limits':['사용자요청음성불변범위로원래시설번호낭독유지; 표시자막과한글자씩일치하는버전아님','실제청취·연속재생미실시.표본시각검사와전체decode를구분','timestamp seek경계표본1f반올림가능,경계타임록은JSON/SRT대조','모바일지도의세부라벨/출처는작으며우측요약과본문자막을함께확인'],'paid_or_upload_performed':False}
wr(q/'final_review.json',report)
wr(q/'findings.json',[{'issue_id':'QAV8L-001','scene_id':'M005 S1 school','timecode':'f25796 / 859.867s','severity':'required','문제':'이전중간본 학교라벨과하천계획겹침','evidence':'최종791edec8 actual f25796 원본픽셀확인/우측분리슬롯+리더로겹침없음','수정안':'원필지앵커리더와우측고정여백슬롯으로분산','owner':'editor_v6','status':'closed_verified','checked_revision':expected}])
wr(q/'handoff.json',{'status':'passed_with_limits','outputs':['qa/production-v8-labels/final_review.json','qa/production-v8-labels/findings.json'],'video_sha256':expected,'required_unresolved':[],'next_owner':'director completed artifact update','original_v8_final_review_modified':False,'actual_listening':False,'continuous_human_playback':False})
print(json.dumps({'status':report['status'],'required_unresolved':[],'sha256':expected,'audio_identity':audio[0],'caption_diff':3},ensure_ascii=False))
