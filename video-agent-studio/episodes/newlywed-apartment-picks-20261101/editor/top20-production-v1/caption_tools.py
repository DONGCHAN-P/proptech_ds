"""Semantic display cues aligned to existing provider word boundaries.
Original text/numbers are preserved. Display/reading numeric differences are
mapped explicitly; no ASR/listening success is inferred from this metadata.
"""
import difflib,re
def norm(s):return re.sub(r'[^0-9a-z가-힣]','',s.lower())
def split_semantic(text,maxchars=43):
 tokens=re.findall(r'(?:\d{4}년\s+\d{1,2}월\s+\d{1,2}일|\d+만\s+[\d,]+쌍|(?:여섯|열세|열아홉|스무|열|다섯|두|한|세|네)\s+(?:곳|쌍|개|사람|지역|가지|구|해)[가-힣]*|\S+)',text)
 merged=[]
 for tok in tokens:
  if merged and re.fullmatch(r'[,?!.]+',tok):merged[-1]+=tok
  else:merged.append(tok)
 tokens=merged
 chunks=[];cur=''
 for tok in tokens:
  if cur and len(cur)+len(tok)+1>maxchars:chunks.append(cur);cur=tok
  else:cur=(cur+' '+tok).strip()
  if tok.endswith(',') and len(cur)>=16:chunks.append(cur);cur=''
 if cur:chunks.append(cur)
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
