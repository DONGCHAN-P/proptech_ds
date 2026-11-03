/* Verified recommendation facts only; no network inference or generated facts. */
window.EXPLAIN = (() => {
  const labels = {location:'업무지 접근',value:'유사 조건 대비 가격',liquidity:'거래 활발도',residential:'주거 여건',commute:'개인 통근',station:'역 접근',school:'학교 접근',new:'연식',green:'녹지',active:'거래 활발도',price:'가격 조건'};
  function build(item, info, py, data) {
    const contributions = Object.entries(item.breakdown || {})
      .map(([key, score]) => ({key, contribution: score * (data.weights?.[key] || 0)}))
      .sort((a,b) => b.contribution - a.contribution).slice(0,3);
    const factors = contributions.map(x=>labels[x.key]).filter(Boolean);
    const checks=[];
    if (info.household_count > 0 && info.household_count < 300)
      checks.push(`전체 ${Number(info.household_count).toLocaleString()}세대인 단지입니다. 대단지와 규모가 다르므로 관리비·주차·매도 시 비교 단지를 함께 확인하세요.`);
    else if (!info.household_count) checks.push('세대수가 확인되지 않았습니다. 관리비·주차·단지 규모는 별도 확인이 필요합니다.');
    if ((py.trade_1y ?? item.trade_1y ?? 0) < 5)
      checks.push(`같은 평형의 최근 1년 거래가 ${py.trade_1y ?? item.trade_1y ?? 0}건으로 적어 거래가격을 해석할 때 개별 거래 조건을 확인해야 합니다.`);
    if (info.build_year && data.today && Number(data.today.slice(0,4))-info.build_year >= 30)
      checks.push(`${info.build_year}년 준공 단지입니다. 수선·주차 여건을 확인해야 하며, 연식만으로 재건축 사업성을 평가하지 않았습니다.`);
    if (data.objective === 'long_term' && (item.peer_count == null || item.peer_count < 5))
      checks.push('유사 조건 비교 표본이 5개 미만이거나 저장 결과에 표본 정보가 없어 가격 비교의 근거가 부족합니다. 가격 점수만으로 투자 매력을 판단하지 않습니다.');
    checks.push('표시 가격은 개별 과거 실거래입니다. 현재 매도 호가와 동·층·향·상태를 계약 전 확인해야 합니다.');
    return {
      summary: factors.length ? `설정한 예산·면적·지역 조건을 통과한 후보 중 ${factors.join(' · ')} 항목의 점수 기여가 컸습니다.` : '선택한 조건을 충족한 후보입니다.',
      reasons: (item.reasons || []).filter(x=>typeof x==='string'), checks,
      method: data.objective === 'long_term' ? '실거주·5년 이상 보유 기준의 비교입니다. 향후 공급·정비사업 사업성·미래 수익률은 평가에 포함하지 않았습니다.' : '저장 당시 선택한 조건과 점수 기준으로 작성한 설명입니다.'
    };
  }
  return {build};
})();
