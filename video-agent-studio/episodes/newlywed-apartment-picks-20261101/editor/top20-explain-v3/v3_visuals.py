"""기존 3개 구도에 특징→가격 지도 의미 전환을 연결합니다. 외부 호출은 없습니다."""
from decimal import Decimal
import html
from phase_timing import price_phase
from caption_tools import norm,translated_index,local_word_time


def exact_price(value):
    """만원 단위 원수치를 반올림 없이 표시합니다."""
    if value is None:
        return '가격 확정 대기'
    v = Decimal(str(value))
    if not v.is_finite() or v < 0:
        raise ValueError('가격은 유한한 양수여야 합니다.')
    eok = int(v // 10000)
    rem = v - eok * 10000
    fractional = max(0, -rem.normalize().as_tuple().exponent)
    tail = f'{rem:,.{fractional}f}'
    return f'{eok}억 {tail}만원' if eok else f'{tail}만원'


def install_v3(g, ctx, panels, map_assets, bindings):
    txt, box, img = [g[k] for k in ['txt', 'box', 'img']]
    ctx['phase_audit'] = []
    ctx['price_audit'] = []
    ctx['photo_audit'] = []
    def wrap(content, cls, sid, extra=''):
        return f'<div id="{sid}" class="{cls}" {extra}>{content}</div>'
    def textblock(text, x, y, w, h, size=31, cls='', id=None):
        attr=f' id="{id}"' if id else ''
        return f'<div{attr} class="text fit {cls}" data-min-font="24" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px;font-size:{size}px">{html.escape(str(text))}</div>'

    def feature(scene):
        rid = scene['region_id']; r = g['regions'][rid]; p = g['photos'][rid]
        rank = r['rank']; family = scene.get('layout_family') or ('top5' if rank <= 5 else 'hero' if rank in [20,18,17,14,11,9,7] else 'comparison')
        ctx['layout_families'][scene['scene_id']] = family
        bind = bindings.get(scene['scene_id'])
        if bind and bind.get('asset_id') and (bind['asset_id']!=p['asset_id'] or bind.get('sha256')!=p['sha256']):
            raise ValueError(scene['scene_id']+': 확정 사진 asset_id/SHA가 현재 명세와 다릅니다.')
        photo_ok = bind and bind.get('region_id') == rid and bind.get('status') in ['verified','provisional']
        x, y, w, h = (80,220,1100,520) if family == 'hero' else (80,300,1020,440) if family == 'comparison' else (80,220,1080,445)
        out = box(x,y,w,h,'#e7e9e4')
        if photo_ok:
            out += img(f'../assets/{rid}.jpg',x,y,w,h)
            out += txt(p['actual_place'],x,y+h+16,w,25,700)
            caption=f"실제 장소 자료사진 · 촬영 {p.get('photo_capture_year') or '연도 미상'}"
            if bind.get('show_license'):caption=f"지역 자료사진 · 촬영 {p.get('photo_capture_year') or '연도 미상'} · {p['license']['name']}"
            out += txt(caption,x,y+h+53,w,20,color='#536873')
        else:
            out += textblock('발화 장소와 일치하는 실제 사진 확정 대기',x+48,y+80,w-96,140,36)
        ctx['photo_audit'].append({'scene_id':scene['scene_id'],'region_id':rid,'binding_status':bind.get('status') if bind else 'pending','actual_place':p['actual_place'],'final_binding':bool(bind and bind.get('status')=='verified')})
        if family == 'comparison':
            out += txt('주거·생활권을 실제 장소와 함께 비교합니다',80,225,1030,31,700)
        if family == 'top5':
            out += txt('거주 수 상위 5개 구 · 현재 지역',1230,220,610,25,700)
            for i in range(5):
                q=next(v for v in g['regions'].values() if v['rank']==i+1); unseen=q['rank']<rank
                col='#286cda' if q['region_id']==rid else '#536873'
                out += txt(f"{i+1:02d}  {'소개 예정' if unseen else q['region'].split()[-1]}",1230,271+i*45,355,25,700,col)
                if not unseen:out += txt(f"{q['count2024']:,}쌍",1590,271+i*45,250,25,700,col)
            feature_y, feature_h = 540, 290
        else:
            out += txt('거주 신혼부부 · 2024년',1240,230,600,25,color='#536873')
            out += txt(f"{r['count2024']:,}쌍",1240,280,600,78,700,'#286cda')
            feature_y, feature_h = 450, 365
        # 문장별로 바꾸므로 긴 특징 설명을 한 카드에 눌러 넣지 않습니다.
        price_ids=set(scene['_phase']['price_sentence_ids'])
        statements=[s for s in scene['sentence_times'] if s['sentence_id'] not in price_ids][1:]
        anim=''
        for i,st in enumerate(statements):
            pid=f"{scene['scene_id']}-feature-{i}"
            content=txt('주거 특징·랜드마크',1240,feature_y-45,600,26,700,'#286cda')+textblock(st['text'],1240,feature_y,600,feature_h,34)
            out+=wrap(content,'statement',pid)
            end=statements[i+1]['start_s'] if i+1<len(statements) else scene['_phase']['switch_s']
            anim+=f'tl.set("#{pid}",{{opacity:0}},0);tl.set("#{pid}",{{opacity:1}},{st["start_s"]:.6f});tl.set("#{pid}",{{opacity:0}},{end:.6f});'
        if not statements:out+=textblock('특징 설명 확정 대기',1240,feature_y,600,feature_h,34)
        if family=='top5':out+=txt(f"거주 수 {rank}위 · {r['count2024']:,}쌍",80,825,1080,28,700,'#286cda')
        return out,anim

    def prices(scene):
        rid=scene['region_id'];data=panels.get(rid);m=map_assets.get(rid)
        # 완료 상태를 명시한 데이터만 사용합니다. 누락/잠정 수치는 시안에도 만들지 않습니다.
        ready=bool(data and data.get('status') in ['verified','final','ready'] and data.get('median_manwon') is not None)
        out=box(80,220,1000,615,'#e7e9e4')
        map_src=(m or {}).get('_staged_file')
        out+=img(map_src or f'../assets/{rid}_focus.svg',110,245,940,485)
        geo=(data or {}).get('price_geography_label') or (m or {}).get('geography_label')
        if ready and not geo:geo=('2024 옛 서구 범위 · 대응하는 현행 구역 합산' if rid=='R01' else g['regions'][rid]['province']+' '+g['regions'][rid]['region']+' · 실제 가격 집계구역')
        out+=textblock(geo or '2024 통계구역 경계 · 가격집계 구역 대조 대기',110,744,940,70,26)
        if m and m.get('marker_status')=='verified_coordinate_inside_region':out+=txt('파란 점: 단지 위치',110,826,940,22,color='#536873')
        out+=txt('지역 아파트 실거래 중위값',1150,220,690,31,700,'#286cda')
        out+=textblock(exact_price(data['median_manwon']) if ready else '지역 가격 확정 대기',1150,272,690,95,64,'price-value',scene['scene_id']+'-region-price')
        out+=txt(f"지역 거래 {data['n']:,}건" if ready else '지역 거래 건수 확정 대기',1150,375,690,27)
        rep=(data or {}).get('representative') or {};rep_ready=ready and rep.get('median_manwon') is not None and rep.get('n') is not None
        out+=box(1130,447,730,300,'#fff',12)
        out+=txt('단지 사례',1150,468,680,26,700,'#286cda')
        out+=textblock(rep.get('apt_name') if rep_ready else '대표 단지 확정 대기',1150,512,680,90,36,'complex-name')
        out+=textblock(exact_price(rep['median_manwon']) if rep_ready else '단지 가격 확정 대기',1150,612,680,72,48,'price-value',scene['scene_id']+'-complex-price')
        out+=txt(f"단지 거래 {rep['n']:,}건" if rep_ready else '단지 거래 건수 확정 대기',1150,701,680,25)
        window=(data or {}).get('contract_window') or {};area=(data or {}).get('area_range_m2')
        period=f"{window['start']} ~ {window['end']} 계약" if ready else '계약기간 확정 대기'
        area_text=f"전용 {area['minimum']}~{area['maximum']}㎡ · 아파트 매매 · 취소 제외" if ready else '전용면적·취소 제외 조건 확정 대기'
        # 기간·면적·각 n은 가격 phase 전체에 고정합니다.
        out+=textblock(period,1150,778,690,45,25)+textblock(area_text,1150,826,690,50,24)
        anim=''
        if ready and g['T'].get('timing_locked'):
            for kind,value,display in [('region',data['median_manwon'],data.get('display_price')),('complex',rep['median_manwon'],rep.get('display_price'))]:
                ids=scene['_phase']['price_sentence_ids'];sentence_id=ids[0 if kind=='region' else 1]
                st=next(t for t in scene['sentence_times'] if t['sentence_id']==sentence_id)
                reading=g['readings'].get(sentence_id) or st.get('reading_text') or st['text']
                aliases=[display,exact_price(value),exact_price(value).replace(' ',''),str(value)]
                found=None
                for alias in aliases:
                    if not alias:continue
                    k=st['text'].find(alias)
                    if k>=0:
                        idx=translated_index(st['text'],reading,len(norm(st['text'][:k])))
                        found=local_word_time(g['word_groups'].get(sentence_id,[]),idx,None);break
                if found is None:raise ValueError(f'{scene["scene_id"]}: {kind} 실제 가격 단어 앵커 누락')
                if found<scene['_phase']['switch_s']:raise ValueError('가격 숫자 강조가 지도 전환보다 빠릅니다.')
                anim+=g['tween']('#'+scene['scene_id']+'-'+kind+'-price',{'opacity':0},{'opacity':1},found,.2)
                ctx['anchor_audit'].append({'scene_id':scene['scene_id'],'key':kind+'_median','local_s':found,'basis':'original_price_sentence_word_boundary','sentence_id':sentence_id})
        ctx['price_audit'].append({'scene_id':scene['scene_id'],'region_id':rid,'price_status':'verified_input' if ready else 'pending','map_status':'v3_manifest_connected' if map_src else 'existing_geometry_only_pending_price_geography','pin_drawn':bool(map_src and m.get('marker_status')=='verified_coordinate_inside_region'),'pin_policy':'검증 좌표를 geometry와 교차 확인한 지도 에셋만 사용; 편집기가 좌표 핀을 추정하지 않습니다.','region_median_manwon':data.get('median_manwon') if ready else None,'complex_median_manwon':rep.get('median_manwon') if rep_ready else None,'region_n':data.get('n') if ready else None,'complex_n':rep.get('n') if rep_ready else None})
        return out,anim

    def region_scene(scene):
        phase=price_phase(scene,g['word_groups'],bool(g['T'].get('timing_locked')));scene['_phase']=phase;ctx['phase_audit'].append(phase)
        feature_body,anim=feature(scene);price_body,price_anim=prices(scene);anim+=price_anim;sid=scene['scene_id'];at=phase['switch_s']
        body=wrap(feature_body,'phase',sid+'-feature-phase')+wrap(price_body,'phase',sid+'-price-phase')
        # 하드 컷이므로 특징 종료 전 사진을 미리 흐리거나 가격을 겹치지 않습니다.
        anim+=f'tl.set("#{sid}-feature-phase",{{opacity:1}},0);tl.set("#{sid}-price-phase",{{opacity:0}},0);tl.set("#{sid}-feature-phase",{{opacity:0}},{at:.6f});tl.set("#{sid}-price-phase",{{opacity:1}},{at:.6f});'
        return body,anim

    old_open=g['opening']
    def opening(scene):
        if scene['scene_id']!='O002':return old_open(scene)
        out=txt('국가데이터처 「2024년 신혼부부통계」',80,230,1760,46,700,'#286cda')
        out+=textblock('2024년 11월 1일 · 당시 수도권 53개 구 · 초혼과 재혼 포함 · 단위: 쌍',80,330,1760,75,34)
        out+=box(80,450,1760,160,'#e2e7e7',12)+textblock('2024년의 거주 현황입니다. 이후 입주·이사·행정구역 개편을 반영한 현재 순위와는 시점이 다릅니다.',110,482,1700,100,37)
        out+=textblock('가격: 2026년 5~10월 계약 · 11월 3일 조회 기준입니다. 10월은 신고 진행 중으로 거래가 추가될 수 있습니다.',80,658,1760,108,33)
        out+=textblock('지역 중위값과 대표 단지 중위값을 구분하고 각각의 표본수를 표시합니다.',80,792,1760,75,31)
        return out,''
    g.update(region_scene=region_scene,opening=opening)
    return ctx


FIT_SCRIPT='''document.querySelectorAll('.fit').forEach(el=>{let size=parseFloat(getComputedStyle(el).fontSize);const floor=Number(el.dataset.minFont||24);while(size>floor&&(el.scrollWidth>el.clientWidth+1||el.scrollHeight>el.clientHeight+1)){size-=1;el.style.fontSize=size+'px';}el.dataset.overflow=(el.scrollWidth>el.clientWidth+1||el.scrollHeight>el.clientHeight+1)?'true':'false';});'''
