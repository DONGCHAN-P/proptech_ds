from bisect import bisect_right
import math

BANDS=[
    {'label':'5억 미만','min_manwon':0,'max_manwon':50000,'color':'#3E82BD'},
    {'label':'5~7억','min_manwon':50000,'max_manwon':70000,'color':'#299D92'},
    {'label':'7~10억','min_manwon':70000,'max_manwon':100000,'color':'#BEA52D'},
    {'label':'10~15억','min_manwon':100000,'max_manwon':150000,'color':'#E3913D'},
    {'label':'15~20억','min_manwon':150000,'max_manwon':200000,'color':'#D75B58'},
    {'label':'20억 이상','min_manwon':200000,'max_manwon':None,'color':'#954B87'}
]

def price_band(manwon):
    if not math.isfinite(manwon) or manwon<=0:raise ValueError('A price must be finite and positive')
    return bisect_right([50000,70000,100000,150000,200000],manwon)

def select_official(candidates,normalized_name):
    if len(candidates)!=1:return None
    row=candidates[0]
    return row if normalized_name in row['names_normalized'] else None
