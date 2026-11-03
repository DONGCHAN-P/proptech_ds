"""Comparable forecast metrics and information-date guarded selection helpers."""
import numpy as np
import pandas as pd
from scipy.stats import spearmanr


def direction(values,neutral=1.):
    a=np.asarray(values)
    return np.where(a>neutral,1,np.where(a < -neutral,-1,0))


def point_metrics(data):
    g=data[data.actual_pct.notna()&data.prediction_pct.notna()]
    result={'forecast_n':len(data),'scored_n':len(g),'unscored_n':len(data)-len(g),
            'scored_coverage':len(g)/len(data) if len(data) else np.nan}
    if g.empty: return result
    err=(g.prediction_pct-g.actual_pct).to_numpy()
    absolute=np.abs(err)
    truth=direction(g.actual_pct)
    pred=direction(g.prediction_pct)
    recalls=[float(np.mean(pred[truth==k]==k)) for k in np.unique(truth)]
    result.update(mae_pp=float(np.mean(absolute)),rmse_pp=float(np.sqrt(np.mean(err**2))),
                  median_ae_pp=float(np.median(absolute)),p90_ae_pp=float(np.quantile(absolute,.9)),
                  tail_mae_pp=float(np.mean(absolute[absolute>=np.quantile(absolute,.9)])),
                  max_ae_pp=float(np.max(absolute)),bias_pp=float(np.mean(err)),
                  direction_accuracy=float(np.mean(pred==truth)),balanced_direction_accuracy=float(np.mean(recalls)))
    if {'origin','region_code'}.issubset(g.columns): result['balanced_mae_pp']=balanced_mae(g)
    if 'origin' in g:
        ranks=[]
        for _,s in g.groupby('origin'):
            if len(s)>=5 and s.prediction_pct.nunique()>1 and s.actual_pct.nunique()>1:
                ranks.append(float(spearmanr(s.prediction_pct,s.actual_pct).statistic))
        result['rank_spearman']=float(np.mean(ranks)) if ranks else np.nan
    for coverage in [80,95]:
        lo,hi=f'lower_{coverage}',f'upper_{coverage}'
        if lo not in g or hi not in g: continue
        v=g[g[lo].notna()&g[hi].notna()]
        if v.empty: continue
        result[f'interval_n_{coverage}']=len(v)
        result[f'interval_coverage_{coverage}']=float(((v.actual_pct>=v[lo])&(v.actual_pct<=v[hi])).mean())
        result[f'interval_width_{coverage}_pp']=float((v[hi]-v[lo]).mean())
        result[f'interval_score_{coverage}']=float(np.mean(interval_score(v.actual_pct,v[lo],v[hi],1-coverage/100)))
    return result


def known_errors(data,as_of,lookback_months=None):
    cutoff=pd.Timestamp(as_of)
    mask=(pd.to_datetime(data.label_available)<=cutoff)&(pd.to_datetime(data.origin)<cutoff)
    mask &= data.actual_pct.notna()&data.prediction_pct.notna()
    if lookback_months:
        mask &= pd.to_datetime(data.origin)>=cutoff-pd.DateOffset(months=lookback_months)
    return data.loc[mask].copy()


def interval_score(actual,lower,upper,alpha):
    y=np.asarray(actual);lo=np.asarray(lower);hi=np.asarray(upper)
    if not 0<alpha<1 or np.any(lo>hi): raise ValueError('Invalid interval')
    return hi-lo+2/alpha*np.maximum(lo-y,0)+2/alpha*np.maximum(y-hi,0)


def loss_weights(losses):
    """At most three near-best candidates; no negative ensemble weights."""
    losses=losses.astype(float)
    if losses.empty or not np.isfinite(losses).all() or (losses<0).any():
        raise ValueError('Invalid historical losses')
    keep=losses.sort_values().head(3)
    keep=keep[keep<=max(keep.min()*1.35,keep.min()+.05)]
    inverse=1./np.maximum(keep,.1)**2
    out=pd.Series(0.,index=losses.index)
    out.loc[keep.index]=inverse/inverse.sum()
    return out


def balanced_mae(data):
    g=data[data.actual_pct.notna()&data.prediction_pct.notna()].copy()
    if g.empty: return np.nan
    g['ae']=(g.prediction_pct-g.actual_pct).abs()
    return float(g.groupby(['origin','region_code']).ae.mean().groupby('origin').mean().mean())


def regional_metrics(data):
    rows=[]
    for (model,level,sid),g in data.groupby(['model','level','series_id']):
        rows.append({'model':model,'level':level,'series_id':sid,'name':g['name'].iloc[0],
                     'region_code':g.region_code.iloc[0],**point_metrics(g)})
    return pd.DataFrame(rows)
