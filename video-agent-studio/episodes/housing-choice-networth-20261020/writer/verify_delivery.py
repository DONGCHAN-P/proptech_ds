from pathlib import Path
import hashlib,json,re,shutil
p=Path(__file__).resolve().parents[1];root=p.parents[2];w=p/'writer';out=p/'outputs/script-review-v1';d=p/'director/claude-story-v1'
report=root/'reports/거주비를 포함한 주거 선택 비교.md'
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
s=(w/'script_v1.md').read_text(encoding='utf-8')
packet=json.loads((d/'packet.json').read_text(encoding='utf-8'))
assert packet['revised_script']==s
for prefix in ['round1.','']:
 r=json.loads((d/(prefix+'receipt.json')).read_text(encoding='utf-8'))
 assert r['exit_status']==0 and r['is_error'] is False
 assert r['input_sha256']==sha(d/(prefix+'input.txt'))
for name in ['packet.json','input.txt','stdout.json','stderr.log','review.md','receipt.json']:
 shutil.copy2(d/name,d/('round2.'+name))
for name in ['script_v1.md','visual_storyboard.md','source_ledger.json','claim_map.json','scene_proposals.json','narration_handoff.json','consensus_record.md','verification_notes.md']:
 shutil.copy2(w/name,out/name)
shutil.copy2(w/'script_v1.md',w/'script.md')
sources=json.loads((w/'source_ledger.json').read_text(encoding='utf-8'))
source_urls={x['url']for x in sources['sources'] if'url'in x}
report_urls=set(re.findall(r'https?://[^\s)]+',report.read_text(encoding='utf-8')))
assert report_urls<=source_urls
for payload in [s,packet['revised_script'],json.dumps(packet,ensure_ascii=False)]:
 assert 'docs.google.com' not in payload and '15_8AAd' not in payload
assert all(x in s for x in ['21%','25만원','120만원','실제 상품별 세금'])
assert len(re.findall(r'^## \d+\. [^\n]+$',s,re.M))==10
body=''.join(x for x in s.splitlines() if x and not x.startswith('#') and not x.startswith('버전:') and not x.startswith('낭독 분량'))
paths=[report,w/'script_v1.md',w/'script.md',w/'visual_storyboard.md',w/'source_ledger.json',w/'consensus_record.md',w/'scene_proposals.json',d/'round1.receipt.json',d/'round2.receipt.json']
manifest={'revision':'delivery-v1','status':'draft_not_user_approved','narration_chars':len(body),'estimate_minutes':[13,16],'scenes':25,'report_unique_urls':len(report_urls),'source_ledger_unique_urls':len(source_urls),'source_ledger_claim_entries':len(sources['sources']),'claude_rounds':2,'claude_final_packet_script_exact_match':True,'claude_response_adopted':'limited_agreement_with_rejected_unsupported_claims','files':[{'path':str(f),'sha256':sha(f),'bytes':f.stat().st_size}for f in paths],'checks':['report_urls_in_source_ledger','source_urls_deduplicated','claude_two_exit0_is_errorFalse','receipt_input_hash_matches','final_packet_script_equal','private_sheet_not_in_packets','ten_numbered_topic_headings'],'not_performed':['voice_generation','actual_audio_listening','video_render','continuous_playback','upload']}
(w/'delivery_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8');shutil.copy2(w/'delivery_manifest.json',out/'delivery_manifest.json')
handoff={'role':'writer','status':'research_report_and_script_draft_complete_pending_director_gate','inputs':['brief.json','research/korea_sources.json korea-research-v1','research/method_sources.json methods-v1','research/sheet_audit.json','research/illustrative_results.json illustrative-v1','qa/model-review/handoff.json passed_with_limits'],'outputs':[str(f)for f in paths]+[str(out)],'validation':manifest['checks'],'unresolved':['market equivalent housing rent calibration','actual historical rental/ETF monthly inputs','year-specific tax/loan feasibility','user script approval','media production and playback QA'],'affected_scene_ids':[f'S{i:03}'for i in range(1,26)],'next_role':'director: independent script QA, user script delivery/approval; no TTS/paid media/render/upload authorization','claude_consensus':'writer/consensus_record.md','manifest':'writer/delivery_manifest.json'}
(w/'handoff.json').write_text(json.dumps(handoff,ensure_ascii=False,indent=2),encoding='utf-8');shutil.copy2(w/'handoff.json',out/'handoff.json')
print(json.dumps({'report_unique_urls':len(report_urls),'ledger_unique_urls':len(source_urls),'narration_chars':len(body),'script_sha256':sha(w/'script_v1.md'),'report_sha256':sha(report),'claude_final_packet_script_exact_match':True},ensure_ascii=False))
