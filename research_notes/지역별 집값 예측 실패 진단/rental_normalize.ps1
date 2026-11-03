param([string]$DataRoot = (Join-Path $PSScriptRoot 'rental_data'))
$ErrorActionPreference='Stop'
Add-Type -AssemblyName System.IO.Compression.FileSystem
$rentalRoot=$DataRoot
function Read-RentalXlsx([string]$file) {
 $zip=[System.IO.Compression.ZipFile]::OpenRead((Join-Path $rentalRoot $file))
 try {
  $reader=[System.IO.StreamReader]::new($zip.GetEntry('xl/sharedStrings.xml').Open())
  [xml]$ss=$reader.ReadToEnd();$reader.Dispose()
  $strings=@($ss.GetElementsByTagName('si') | ForEach-Object {$_.InnerText})
  $reader=[System.IO.StreamReader]::new($zip.GetEntry('xl/worksheets/sheet1.xml').Open())
  [xml]$sheet=$reader.ReadToEnd();$reader.Dispose()
  foreach($row in $sheet.GetElementsByTagName('row')) {
   $cells=[ordered]@{}
   foreach($c in $row.c){
    $val=[string]$c.v
    if($c.GetAttribute('t') -eq 's'){$val=$strings[[int]$val]}
    elseif($c.GetAttribute('t') -eq 'inlineStr'){$val=$c.is.InnerText}
    $cells[[string]$c.r]=$val
   }
   [pscustomobject]@{row=[int]$row.r;cells=$cells}
  }
 } finally {$zip.Dispose()}
}
$rentalRegions=[ordered]@{'서울'='11';'부산'='26';'대구'='27';'인천'='28';'광주'='29';'대전'='30';'울산'='31';'세종'='36';'경기'='41';'충북'='43';'충남'='44'}
$rentalSources=@(
 @{file='rental_reb_apt_jeonse_price.xlsx';variable='reb_apt_jeonse_price_index';depth=4;unit='2026-06=100'},
 @{file='rental_reb_apt_jeonse_supply_demand.xlsx';variable='reb_apt_jeonse_supply_demand_index';depth=3;unit='survey_supply_demand_index'}
)
$rentalNormalized=[System.Collections.Generic.List[object]]::new()
$rentalLineage=[System.Collections.Generic.List[object]]::new()
$rentalMissing=[System.Collections.Generic.List[object]]::new()
$rentalCoverage=[System.Collections.Generic.List[object]]::new()
foreach($source in $rentalSources) {
 $rows=@(Read-RentalXlsx $source.file)
 $dateRow=@($rows|Where-Object {$_.row -eq 4})[0]
 $dates=[ordered]@{}
 foreach($cell in $dateRow.cells.GetEnumerator()){
  if($cell.Value -match '^(\d{4})년\s*(\d{1,2})월$'){
   $dates[($cell.Key -replace '\d+$','')]=('{0}-{1:00}' -f $Matches[1],[int]$Matches[2])
  }
 }
 if($dates.Count -lt 100){throw 'Unexpected date headers'}
 foreach($name in $rentalRegions.Keys){
  $candidates=@($rows|Where-Object {
   $r=$_.row;$a=$_.cells["A$r"];$b=$_.cells["B$r"];$c=$_.cells["C$r"];$d=$_.cells["D$r"]
   ($r -gt 7) -and ($b -eq $name) -and ($c -eq $name) -and (($source.depth -eq 3) -or ($d -eq $name)) -and (($a -eq $name) -or (($name -eq '광주') -and ($a -eq '전남광주')))
  })
  if($candidates.Count -ne 1){throw "Expected one aggregate row: $($source.file) $name, got $($candidates.Count)"}
  $row=$candidates[0];$observed=@();$allObserved=@();$blanks=@()
  foreach($date in $dates.GetEnumerator()){
   $cell="$($date.Key)$($row.row)";$value=[string]$row.cells[$cell]
   $number=0.0;$isNumber=[double]::TryParse($value,[System.Globalization.NumberStyles]::Float,[System.Globalization.CultureInfo]::InvariantCulture,[ref]$number)
   if($isNumber){$allObserved+=$date.Value}
   if($date.Value -lt '2006-01'){continue}
   if(-not $isNumber){
    if($value -notin @('','-','..','...')){throw "Unexpected nonnumeric cell $cell : $value"}
    $blanks+=$date.Value
    $rentalMissing.Add([pscustomobject]@{region_code=$rentalRegions[$name];region_name=$name;month=$date.Value;variable=$source.variable;raw_value=$value;source_file=$source.file;source_cell=$cell})
    continue
   }
   $observed+=$date.Value
   $rentalNormalized.Add([pscustomobject]@{region_code=$rentalRegions[$name];month=$date.Value;variable=$source.variable;value=$value;available_date='';availability_basis='historical_release_unverified;current_vintage_retrieved_2026-10-27;not_point_in_time'})
   $rentalLineage.Add([pscustomobject]@{region_code=$rentalRegions[$name];region_name=$name;month=$date.Value;variable=$source.variable;value=$value;source_file=$source.file;source_sheet=1;source_row=$row.row;source_cell=$cell;source_hierarchy=(@('A','B','C','D')|Select-Object -First $source.depth|ForEach-Object {$row.cells["$_$($row.row)"]}) -join ' > ';unit=$source.unit})
  }
  if($observed.Count -eq 0){throw "No observations for $name"}
  $first=$observed[0];$last=$observed[-1]
  $internal=@($blanks|Where-Object {$_ -ge $first -and $_ -le $last})
  $rentalCoverage.Add([pscustomobject]@{region_code=$rentalRegions[$name];region_name=$name;variable=$source.variable;rows=$observed.Count;first_month=$first;last_month=$last;raw_first_month=$allObserved[0];raw_last_month=$allObserved[-1];internal_missing_months=$internal.Count;blank_cells_since_2006=$blanks.Count;target_expected_months=249;target_absent_months=(249-$observed.Count);source_file=$source.file;source_row=$row.row;unit=$source.unit})
 }
}
$rentalNormalized=@($rentalNormalized|Sort-Object region_code,month,variable)
$duplicate=@($rentalNormalized|Group-Object region_code,month,variable|Where-Object {$_.Count -gt 1})
if($duplicate.Count){throw 'Duplicate normalized keys'}
$rentalNormalized|Export-Csv -LiteralPath (Join-Path $rentalRoot 'rental_normalized.csv') -NoTypeInformation -Encoding UTF8
$rentalLineage|Export-Csv -LiteralPath (Join-Path $rentalRoot 'rental_lineage.csv') -NoTypeInformation -Encoding UTF8
$rentalCoverage|Export-Csv -LiteralPath (Join-Path $rentalRoot 'rental_coverage.csv') -NoTypeInformation -Encoding UTF8
$rentalMissing|Export-Csv -LiteralPath (Join-Path $rentalRoot 'rental_missing.csv') -NoTypeInformation -Encoding UTF8
$rentalSamples=@($rentalLineage|Where-Object {($_.region_code -in @('11','29','36','43')) -and ($_.month -in @('2006-01','2012-07','2012-12','2013-01','2026-06','2026-09'))})
$rentalSamples|Export-Csv -LiteralPath (Join-Path $rentalRoot 'rental_samples.csv') -NoTypeInformation -Encoding UTF8
$rentalValidation=[pscustomobject]@{normalized_rows=$rentalNormalized.Count;regions=@($rentalRegions.Values);variables=@($rentalSources.variable);duplicate_keys=$duplicate.Count;missing_cells=$rentalMissing.Count;historical_release_dates_filled=0;download_vintage='2026-10-27';price_june_2026_values=@($rentalNormalized|Where-Object {$_.variable -eq 'reb_apt_jeonse_price_index' -and $_.month -eq '2026-06'}|Select-Object region_code,value);coverage=$rentalCoverage;sample_numeric_cells=$rentalSamples}
$rentalValidation|ConvertTo-Json -Depth 8|Set-Content -LiteralPath (Join-Path $rentalRoot 'rental_validation.json') -Encoding UTF8
$rentalCoverage|Format-Table region_code,region_name,variable,rows,first_month,last_month,internal_missing_months,source_row -AutoSize
Write-Output "NORMALIZED_ROWS=$($rentalNormalized.Count); DUPLICATES=$($duplicate.Count); MISSING_CELLS=$($rentalMissing.Count)"
$rentalSamples|Select-Object -First 8|Format-Table region_code,month,variable,value,source_cell -AutoSize

# Extra handoff outputs. These dates are ASSUMED MODEL AVAILABILITY, never official releases.
$rentalAssumed3m=@($rentalNormalized|ForEach-Object {
 $monthDate=[DateTime]::ParseExact($_.month+'-01','yyyy-MM-dd',[System.Globalization.CultureInfo]::InvariantCulture)
 [pscustomobject]@{region_code=$_.region_code;month=$_.month;variable=$_.variable;value=$_.value;available_date=$monthDate.AddMonths(4).AddDays(-1).ToString('yyyy-MM-dd');availability_basis='ASSUMED_month_end_of_reference_month_plus_3_months;NOT_official_release;latest_revised_vintage_2026-10-27;not_initial_vintage'}
})
$rentalAssumed3m|Export-Csv -LiteralPath (Join-Path $rentalRoot 'rental_normalized_assumed_3m.csv') -NoTypeInformation -Encoding UTF8
$rentalRevisionFlags=@($rentalLineage|ForEach-Object {
 [pscustomobject]@{region_code=$_.region_code;month=$_.month;variable=$_.variable;retrieved_vintage_date='2026-10-27';initial_release_observed='false';historical_release_date_verified='false';revision_flag='latest_vintage_history;initial_vintage_unavailable';rebase_flag=$(if($_.variable -eq 'reb_apt_jeonse_price_index'){'rebased_to_2026-06=100'}else{'survey_index_not_price_rebase'});geography_flag=$(if($_.region_code -eq '29'){'Gwangju_component_under_JeonnamGwangju;analyst_requested_code_29'}elseif($_.region_code -eq '28'){'Incheon_aggregate;2026-07_subdivision_change'}else{'source_named_aggregate;no_boundary_harmonization'});source_file=$_.source_file;source_cell=$_.source_cell}
})
$rentalRevisionFlags|Export-Csv -LiteralPath (Join-Path $rentalRoot 'rental_revision_flags.csv') -NoTypeInformation -Encoding UTF8
$rentalQuality=@(foreach($variable in $rentalSources.variable){
 $data=@($rentalNormalized|Where-Object {$_.variable -eq $variable})
 $numbers=@($data|ForEach-Object {[double]::Parse($_.value,[System.Globalization.CultureInfo]::InvariantCulture)})
 $cov=@($rentalCoverage|Where-Object {$_.variable -eq $variable})
 [pscustomobject]@{variable=$variable;rows=$data.Count;regions=@($data.region_code|Sort-Object -Unique);min=($numbers|Measure-Object -Minimum).Minimum;max=($numbers|Measure-Object -Maximum).Maximum;zero_values=@($numbers|Where-Object {$_ -eq 0}).Count;negative_values=@($numbers|Where-Object {$_ -lt 0}).Count;blank_normalized_values=@($data|Where-Object {$_.value -eq ''}).Count;nan_or_infinite=@($numbers|Where-Object {[double]::IsNaN($_) -or [double]::IsInfinity($_)}).Count;internal_missing_months=($cov|Measure-Object internal_missing_months -Sum).Sum;target_absent_months=($cov|Measure-Object target_absent_months -Sum).Sum;explicit_source_blank_cells=($cov|Measure-Object blank_cells_since_2006 -Sum).Sum;canonical_available_dates_blank=@($data|Where-Object {$_.available_date -eq ''}).Count}
})
$rentalQuality|ConvertTo-Json -Depth 5|Set-Content -LiteralPath (Join-Path $rentalRoot 'rental_quality_checks.json') -Encoding UTF8
$rentalQuality|ConvertTo-Json -Depth 5 -Compress
