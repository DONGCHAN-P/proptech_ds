from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from common import load_secrets
import requests
key=load_secrets().get('VWORLD_API_KEY','')
rows=[{'name':'스타필드 하남','address':'경기도 하남시 미사대로 750','type':'ROAD','source':'https://www.starfield.co.kr/hanam/main.do','status':'현재 운영시설'}, {'name':'캠프콜번 사업지 일원','address':'경기도 하남시 하산곡동 209-9','type':'PARCEL','source':'https://www.hanam.go.kr/cleanh/cleanhBbsNttWebView.do?key=8364&nttNo=3495','status':'개발 추진 / 주소 대표점이며 사업경계 아님'}]
for r in rows:
 try:
  x=requests.get('https://api.vworld.kr/req/address',params={'service':'address','request':'getcoord','version':'2.0','key':key,'address':r['address'],'type':r['type'],'simple':'false','format':'json','crs':'epsg:4326'},timeout=20).json().get('response',{})
  r['geocoder_status']=x.get('status');r['geocoder_result']=x.get('result');r['refined']=x.get('refined');r['geocoder']='VWorld Address API; EPSG:4326;2026-10-20'
 except Exception as e:r['geocoder_status']=type(e).__name__
out=Path(__file__).with_name('facilities_coordinates_v4.json');out.write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(rows,ensure_ascii=False))
