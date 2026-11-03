"""Point-in-time primitives for regional price forecasting (no production writes)."""
import numpy as np
import pandas as pd
from scipy.stats import trim_mean

def join_released(origins, rows, max_age_months=None):
    """As-of join by RELEASE date; national code 00 broadcasts to every region.

    Inputs are single-snapshot observations, not a revision-vintage archive. No
    backfill is allowed. Missing releases remain missing. For a variable, a
    regional row takes precedence over the national observation if present.
    """
    out=origins.copy()
    data=rows.copy()
    data['region_code']=data.region_code.astype(str)
    data['available_date']=pd.to_datetime(data.available_date)
    if data.duplicated(['region_code','variable','available_date']).any():
        raise ValueError('Ambiguous duplicate release; resolve vintages explicitly')
    out['as_of']=pd.to_datetime(out.as_of)
    for variable, v in data.groupby('variable'):
        values=pd.Series(np.nan,index=out.index,dtype=float)
        for region, indices in out.groupby('region_code').groups.items():
            sub=v[v.region_code.eq(str(region))]
            if sub.empty:
                sub=v[v.region_code.eq('00')]
            if sub.empty:
                continue
            left=out.loc[indices,['as_of']].sort_values('as_of')
            sub=sub.copy()
            sub['source_month']=pd.to_datetime(sub.month)
            matched=pd.merge_asof(left,sub[['available_date','source_month','value']].sort_values('available_date'),
                                  left_on='as_of',right_on='available_date',direction='backward')
            if max_age_months is not None:
                age=(matched.as_of.dt.year-matched.source_month.dt.year)*12+matched.as_of.dt.month-matched.source_month.dt.month
                matched.loc[age>max_age_months,'value']=np.nan
            values.loc[left.index]=matched.value.to_numpy()
        out[variable]=values
    return out

def add_target(panel, horizon=6):
    """Exact calendar target. A missing intervening return invalidates the label."""
    out=panel.copy()
    if out.duplicated(['series_id','month']).any():
        raise ValueError('Duplicate series-month')
    lookup=out.set_index(['series_id','month']).log_change
    future=[]
    for step in range(1,horizon+1):
        dates=out.month+pd.DateOffset(months=step)
        idx=pd.MultiIndex.from_arrays([out.series_id,dates])
        future.append(lookup.reindex(idx).to_numpy())
    arr=np.column_stack(future)
    out['target_log_return']=arr.sum(axis=1)  # NaN deliberately propagates.
    out['target_month']=out.month+pd.DateOffset(months=horizon)
    # Assumed 60+ day reporting buffer: monthly data available on month t+3's 1st.
    out['label_available']=out.target_month+pd.DateOffset(months=3)
    return out

def training_rows(panel, as_of):
    return panel.loc[(panel.label_available<=pd.Timestamp(as_of)) & panel.target_log_return.notna()].copy()


def assert_selection_available(records, first_holdout):
    if pd.to_datetime(records.label_available).max()>pd.Timestamp(first_holdout):
        raise ValueError('Model selection used a label unpublished at first holdout')


def lagged_change(rows, lag, log_growth=True):
    """Exact-month difference whose information date includes BOTH operands."""
    g=rows.sort_values('month').reset_index(drop=True).copy()
    idx=g.set_index('month')
    dates=g.month-pd.DateOffset(months=lag)
    prior=idx.value.reindex(dates).to_numpy()
    prior_release=pd.to_datetime(idx.available_date.reindex(dates).to_numpy())
    if log_growth:
        g['value']=np.log1p(g.value.clip(lower=0).to_numpy())-np.log1p(np.maximum(prior,0))
    else:
        g['value']=g.value.to_numpy()-prior
    release=pd.DataFrame({'new':pd.to_datetime(g.available_date),'old':prior_release})
    g['available_date']=release.max(axis=1)
    return g


def evaluation_cohort(panel, as_of, min_training_months=60):
    """Choose forecastable rows without consulting future outcome availability."""
    train=training_rows(panel,as_of)
    train=train[train.eligible]
    n=train.groupby('series_id').month.nunique()
    enough=n[n>=min_training_months].index
    return panel.loc[panel.month.eq(pd.Timestamp(as_of).to_period('M').start_time)&panel.eligible&panel.series_id.isin(enough)].copy()

def policy_features(origins, events):
    """Recent announced measures; zero does not assert absence of all policies.

    The supplied registry is deliberately partial. direction is a manual policy
    tightening (+1) / easing (-1) code, NEVER an assumed price response.
    """
    out=origins.copy()
    out['policy_recent_6m']=0.
    out['policy_announcements_6m']=0.
    packages={}
    for e in events:
        key=(e.get('package_id') or e.get('package_announcement_date') or e['announcement_date'],float(e.get('direction',0.)))
        packages.setdefault(key,[]).append(e)
    for (_,direction),measures in packages.items():
        mask=pd.Series(False,index=out.index)
        for e in measures:
            announce=pd.Timestamp(e['announcement_date'])
            known=(pd.to_datetime(out.as_of)>=announce)&(pd.to_datetime(out.as_of)<announce+pd.DateOffset(months=6))
            affected=pd.Series(False,index=out.index)
            for prefix in e.get('affected_prefixes',['00']):
                affected |= True if prefix=='00' else out.district_code.astype(str).str.startswith(str(prefix))
            mask |= known&affected
        out.loc[mask,'policy_recent_6m']+=direction
        out.loc[mask,'policy_announcements_6m']+=1.
    return out

def matched_changes(groups, min_complexes=5):
    """Adjacent-month same-complex/exact-rounded-area changes, equal complex weight.

    This is a matched-cell estimator, not a repeat sale of the exact same dwelling.
    Median cell prices, within-complex mean log return, 10% trimmed complex mean.
    No future-fitted property coefficients, no gap bridging and no forward fill.
    """
    keys=['series_id','month','apt_id','area_key']
    g=groups.groupby(keys,as_index=False).ppm.median()
    prev=g.copy()
    prev['month']+=pd.DateOffset(months=1)
    m=g.merge(prev,on=keys,suffixes=('','_prev'),validate='one_to_one')
    m['lr']=np.log(m.ppm/m.ppm_prev)
    per=m.groupby(['series_id','month','apt_id']).lr.mean().reset_index()
    stats=per.groupby(['series_id','month']).lr.agg(
        log_change=lambda x:float(trim_mean(x,0.1)),matched_complexes='size').reset_index()
    all_months=g[['series_id','month']].drop_duplicates()
    out=all_months.merge(stats,on=['series_id','month'],how='left')
    out['matched_complexes']=out.matched_complexes.fillna(0).astype(int)
    out.loc[out.matched_complexes<min_complexes,'log_change']=np.nan
    return out.sort_values(['series_id','month']).reset_index(drop=True)
