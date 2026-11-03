"""Transparent long-hold screening heuristics; no return prediction or listing prices."""
import numpy as np
import pandas as pd

# Reference employment districts represented by stations in the local station dataset.
# Distances are geographic, not promised travel times or measured employment counts.
HUBS = ['광화문', '여의도', '강남', '디지털미디어시티', '마곡나루', '판교',
        '가산디지털단지', '인천대입구', '수원']


def enrich(df, stations, today):
    from web.match import haversine_km, ramp
    df = df.copy()
    df['s_location'] = 50.0
    df['hub_distance_km'] = np.nan
    df['nearest_hub'] = None
    if stations is not None:
        hubs = stations.df.copy()
        hubs['hub'] = hubs['station_name'].str.replace(r'\(.*?\)', '', regex=True).str.strip()
        hubs = hubs[hubs['hub'].isin(HUBS)].groupby('hub')[['lat','lng']].mean()
        if len(hubs):
            dist = haversine_km(df['lat'].to_numpy()[:,None], df['lng'].to_numpy()[:,None],
                                hubs['lat'].to_numpy()[None,:], hubs['lng'].to_numpy()[None,:])
            nearest = np.argmin(dist, axis=1)
            df['hub_distance_km'] = dist.min(axis=1)
            df['nearest_hub'] = hubs.index.to_numpy()[nearest]
            # Nearest employment district (70%) plus access to a second one (30%).
            reach = np.sort(dist,axis=1)[:,:min(2,len(hubs))]
            km = reach[:,0] if reach.shape[1]==1 else reach[:,0]*.7+reach[:,1]*.3
            df['s_location'] = .75*ramp(km,35,3)+.25*ramp(df['walk_min'],25,5)

    # Compare similar age and station-access homes, rather than the cheapest in a district.
    # Reference population is formed BEFORE the user's budget/region filters.
    age = (today.year-df['build_year']).clip(lower=0)
    df['_age_band'] = np.floor(age/10)
    df['_walk_band'] = pd.cut(df['walk_min'],[-np.inf,10,20,np.inf],labels=False)
    keys = ['sigungu_code','pyeong_bucket','_age_band','_walk_band']
    ppy = df['ppy_1y'].fillna(df['last_ppy'])
    fresh = pd.to_datetime(df['last_date']) >= pd.Timestamp(today)-pd.Timedelta(days=365)
    df['_reference_ppy'] = ppy.where(fresh & (df['trade_1y'].fillna(0)>=3) & (ppy>0))
    df['peer_count'] = df.groupby(keys)['_reference_ppy'].transform('count')
    median = df.groupby(keys)['_reference_ppy'].transform('median')
    df['peer_price_ratio'] = (ppy/median).where(df['peer_count']>=5)
    # Discount benefit is deliberately capped: unexplained low prices are not free alpha.
    df['s_value'] = (50+(1-df['peer_price_ratio'])*100).clip(20,75).fillna(50)
    df['s_liquidity'] = (np.log1p(df['trade_1y'].fillna(0).clip(lower=0))/np.log(31)*100).clip(0,100)
    infra = df['infra_score'].fillna(50) if 'infra_score' in df else 50
    df['s_residential'] = .6*ramp(df['build_year'],today.year-40,today.year-5)+.4*infra
    return df.drop(columns=['_age_band','_walk_band','_reference_ppy'])
