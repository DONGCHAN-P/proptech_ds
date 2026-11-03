"""Semantic display cues aligned to existing provider word boundaries.
Original text/numbers are preserved. Display/reading numeric differences are
mapped explicitly; no ASR/listening success is inferred from this metadata.
"""
import difflib,re
PROTECTED_PHRASES=[]
def set_protected_phrases(phrases):
 global PROTECTED_PHRASES
 PROTECTED_PHRASES=sorted({p for p in phrases if p},key=len,reverse=True)
def norm(s):return re.sub(r'[^0-9a-z가-힣]','',s.lower())
def split_semantic(text,maxchars=43):
 protected='|'.join(re.escape(p) for p in PROTECTED_PHRASES)
 number=r'\d[\d,]*(?:\.\d+)?'
 money=number+r'억(?:\s*'+number+r'만원)?'
 pattern='(?:'+(protected+'|' if protected else '')+money+r'|\d{4}년\s+\d{1,2}월\s+\d{1,2}일|\d+만\s+[\d,]+쌍|'+number+r'\s*(?:만원|억원|㎡|쌍|건)|(?:여섯|열세|열아홉|스무|열|다섯|두|한|세|네)\s+(?:곳|쌍|개|사람|지역|가지|구|해)[가-힣]*|\S+)'
 spans=[]
 for m in re.finditer(pattern,text):
  # 금액·단지명 뒤 조사/어미를 같은 단어로 묶어 원문에 없는 공백을 넣지 않습니다.
  if spans and spans[-1][1]==m.start():spans[-1]=(spans[-1][0],m.end())
  else:spans.append((m.start(),m.end()))
 chunks=[];start=None;end=None
 for a,b in spans:
  if start is not None and b-start>maxchars:
   chunks.append(text[start:end]);start=a
  elif start is None:start=a
  end=b
  if text[a:b].endswith(',') and end-start>=16:chunks.append(text[start:end]);start=None
 if start is not None:chunks.append(text[start:end])
 return chunks
def translated_index(display,reading,index):
 for tag,a,b,c,d in difflib.SequenceMatcher(None,norm(display),norm(reading),autojunk=False).get_opcodes():
  if a<=index<b or (a==b==index):
   return c+(index-a) if tag=='equal' else c+round((d-c)*(index-a)/max(1,b-a))
 return len(norm(reading))
def local_word_time(words,reading_index,fallback):
 for w in words:
  if w.get('sentence_normalized_char_end',0)>reading_index:
   return float(w.get('local_start_s',w.get('start_s',fallback)))
 return fallback
def make_cues(sentence,words,reading=None,maxchars=43):
 display=sentence['text'];reading=reading or sentence.get('reading_text') or display;chunks=split_semantic(display,maxchars)
 result=[];offset=0;start=float(sentence['start_s']);end=float(sentence['end_s']);ln=max(1,len(norm(display)))
 for chunk in chunks:
  idx=translated_index(display,reading,offset)
  b=local_word_time(words,idx,start) if words else start+(end-start)*offset/ln
  result.append({'sentence_id':sentence['sentence_id'],'text':chunk,'start_s':max(start,min(b,end)),'end_s':end,'display_normalized_range':[offset,offset+len(norm(chunk))],'reading_normalized_start':idx,'alignment_basis':'provider_word_boundaries_with_explicit_display_reading_map' if words else 'proportional_pending_word_metadata'})
  offset+=len(norm(chunk))
 for i in range(len(result)-1):result[i]['end_s']=result[i+1]['start_s']
 return [r for r in result if r['end_s']>r['start_s']]
def find_anchor(sentence,words,value,reading=None):
 aliases=[f'{value:,}',str(value)]
 if value>=10000:aliases += [f'{value//10000}만 {value%10000:,}',f'{value//10000}만{value%10000:,}']
 for v in aliases:
  k=sentence['text'].find(v)
  if k>=0:
   idx=translated_index(sentence['text'],reading or sentence.get('reading_text') or sentence['text'],len(norm(sentence['text'][:k])))
   return local_word_time(words,idx,sentence['start_s'])
 return None
