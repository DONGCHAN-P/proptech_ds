"""Read-only audit of frozen CSV; writes only notes/JSON receipts."""
from collect_official_inputs import *
from collections import Counter,defaultdict

EXPECTED='cbccdf22841a4d93c0233696e182c693fd05801929ba94522dc941e96646b576'
def main():
    import sys;sys.stdout.reconfigure(encoding='utf-8')
    p=OUT/'monthly_exogenous.csv';assert digest(p.read_bytes())==EXPECTED
    annual_source=OLD/'extracted/migration_annual_six_regions.csv'
    annual_raw=list(csv.DictReader(annual_source.open(encoding='utf-8-sig')))
    indexed={(r['region'],r['year'],r['measure']):float(r['persons']) for r in annual_raw}
    annual=[]
    for r in annual_raw:
        if r['measure']!='순이동':continue
        region,year=r['region'],int(r['year']);value=float(r['persons'])
        assert indexed[(region,str(year),'전입')]-indexed[(region,str(year),'전출')]==value
        annual.append(dict(region_code=REGIONS[region],month=f'{year}-12',variable='net_migration_annual_persons',value=value,available_date=f'{year+1}-03-31',availability_basis='assumed_next_year_march_31_not_verified_individual_annual_release',region_name=region,unit='persons_per_calendar_year',scope='annual_domestic_migration_do_not_distribute_across_months',source_id='existing_annual_migration_2025',source_locator='migration_2025_sheet03.csv;year='+str(year),vintage_date=ASOF,vintage_basis='verified_current_local_copy_not_historical_first_release',quality_flag='signed_flow_preserved;2005_baseline_included',frequency='annual',observation_year=year,period_start=f'{year}-01-01',period_end=f'{year}-12-31',suggested_max_observation_age_months=18))
    assert len(annual)==126
    write_csv('migration_annual_net_six_regions.csv',annual,FIELDS+['frequency','observation_year','period_start','period_end','suggested_max_observation_age_months'])
    rows=list(csv.DictReader(p.open(encoding='utf-8-sig')))
    assert len(rows)==16810
    assert len({(r['region_code'],r['month'],r['variable']) for r in rows})==len(rows)
    assert all(r['available_date']<=ASOF and r['month']<=ASOF[:7] and r['value']!='' for r in rows)
    groups=defaultdict(list)
    for r in rows:groups[(r['variable'],r['region_code'])].append(r)
    coverage=[dict(variable=v,region_code=c,first_month=min(r['month'] for r in rs),last_month=max(r['month'] for r in rs),rows=len(rs),negative_values=sum(float(r['value'])<0 for r in rs)) for (v,c),rs in sorted(groups.items())]
    write_json(OUT/'coverage_by_region.json',coverage)
    negative_supply=[r for r in rows if r['variable'].startswith('housing_') and float(r['value'])<0]
    geography=[x for x in coverage if x['region_code'] in ['12','29','46'] and x['variable'].startswith('resident_')]
    audit={'as_of_date':ASOF,'file':str(p.relative_to(ROOT)),'sha256':EXPECTED,'frozen':True,'no_further_csv_edits':True,'bytes':p.stat().st_size,'data_rows':len(rows),'variables':sorted({r['variable'] for r in rows}),'unique_keys':True,'all_available_dates_not_after_asof':True,'all_values_observed_or_definitionally_derived_not_imputed':True,'negative_supply_records':negative_supply,'administrative_geography_coverage':geography,'availability_counts':dict(Counter(r['availability_basis'] for r in rows)),'strict_point_in_time_backtest_ready':False,'reason':'Current/reused revised vintages; assumed publication lags do not recover historical first-release values. Treat available_date as an explicitly labelled release-lag proxy, not proof that this exact revised value was known then.'}
    write_json(OUT/'official_validation.json',audit)
    registry=[]
    for v in sorted({r['variable'] for r in rows}):
        rs=[r for r in rows if r['variable']==v]
        status='candidate_with_caveats';reason='Apply available_date, vintage and geography checks.'
        if v in ['employed_residents_thousand','employment_rate_15plus_pct','unemployment_rate_pct']:status='deferred_historical_training';reason='Only 2026-09 acquired; exclude from historical learning/feature selection.'
        if 'migration' in v:status='deferred_pre2024_selection';reason='Regional history begins 2024-08, or exact persons only 2026-08. Preserve signed net flows; do not select using a future holdout window. Longer monthly KOSIS extraction remains deferred.'
        if v.startswith('housing_'):reason='All housing, six regions, ends 2025-12. Mask stale values >6 months as parent specified; keep missing flags. Negative source values require review.'
        if v.startswith('resident_'):reason='Registered households are not census general households. Keep code12 separate. Code29/46 end 2026-06; do not splice combined geography. Historical district/province boundary changes not adjusted.'
        registry.append(dict(variable=v,status=status,reason=reason,first_month=min(r['month'] for r in rs),last_month=max(r['month'] for r in rs),unit=rs[0]['unit']))
    registry.append(dict(variable='net_migration_annual_persons',status='candidate_annual_supplement_separate_file',file='collected/migration_annual_net_six_regions.csv',frequency='annual',first_month='2005-12',last_month='2025-12',rows=126,reason='Six regions. December observation only; available following March31 by conservative assumption. Preserve signs; never backfill to January. Parent can use frequency-specific max observation age18 months. Latest revised vintage remains a limitation.'))
    write_json(ROOT/'official_feature_registry.json',{'as_of_date':ASOF,'frozen_input_sha256':EXPECTED,'parent_owns_pipeline_and_feature_selection':True,'features':registry})
    m=read_manifest();m['frozen_combined_csv']={k:audit[k] for k in ['file','sha256','frozen','no_further_csv_edits','bytes','data_rows']}
    m['normalization_schema']=FIELDS
    m['availability_warning']=audit['reason']
    m['credentials_accessed']=False;m['env_edited']=False;m['paid_calls']=False;m['raw_transaction_uploads']=False;m['transaction_parsing']=False
    m['geography_notes']={'00':'National common covariates; join to each modeled region, not a separate regional target.','12':'Jeonnam-Gwangju integrated region; NEVER map to historical Gwangju29.','29':'Gwangju old geography; acquired demographic series ends 2026-06.','42':'Stable project identifier for Gangwon; original MOIS code51 maps to42. Original source code retained in source_locator.','45':'Stable project identifier for Jeonbuk; original MOIS code52 maps to45. Original source code retained in source_locator.'}
    for src in m['sources']:
        local=ROOT/src['local_file'] if src.get('local_file') else None
        if local and local.suffix=='.json' and local.exists():
            try:j=json.loads(local.read_text(encoding='utf-8'))
            except ValueError:continue
            if j.get('RESULT',{}).get('CODE','').startswith('ERROR'):
                src['payload_status']='official_error_response_not_data';src['payload_error']=j['RESULT']
    # Provenance for previously collected annual migration, deliberately not repeated monthly.
    oldmanifest=json.loads((OLD/'collection_manifest.json').read_text(encoding='utf-8'))
    oldsource=next(x for x in oldmanifest if x['name']=='migration_2025.xlsx')
    m['reviewed_existing_annual_migration']={**oldsource,'local_original':str(OLD/'raw/migration_2025.xlsx'),'sha256':digest((OLD/'raw/migration_2025.xlsx').read_bytes()),'derived_local_file':str(OLD/'extracted/migration_annual_six_regions.csv'),'frequency':'annual','monthly_conversion_performed':False}
    for filename in ['migration_202608_tables.json','mois_geography_missing.json','coverage_summary.json','coverage_by_region.json','unsold_header_validation.json','official_validation.json']:
        local=OUT/filename;m['outputs']=[x for x in m['outputs'] if x.get('file')!=str(local.relative_to(ROOT))];m['outputs'].append(dict(file=str(local.relative_to(ROOT)),sha256=digest(local.read_bytes()),bytes=local.stat().st_size))
    write_json(MANIFEST,m)
    assert digest(p.read_bytes())==EXPECTED
    print(json.dumps({'rows':len(rows),'variables':len(audit['variables']),'negative_supply_records':len(negative_supply),'geography':geography,'sha256':EXPECTED},ensure_ascii=False,indent=2))

if __name__=='__main__':main()
