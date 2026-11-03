import React from 'react';
import {C} from '../theme';
import {Page} from '../Cards';
import {Bars} from './Bars';
import {Steps} from './Steps';
import {Versus} from './Versus';
import {Units} from './Units';
import {CounterMap, DirectionMap, Gen1Map, YeongtongMap} from './Maps';
import {Line, Mix} from './Charts';

/** 장면 이름 → 그리는 컴포넌트. 파이썬이 내보낸 `scene` 값이 여기로 온다. */
export const Scene: React.FC<{name: string; data: any; dur: number}> = ({name, data, dur}) => {
  const [head, key, mod] = name.split(':');
  if (head === 'bars')
    return <Bars rows={data.bars[key]} spec={data.barSpec[key]} still={mod === 'static'} />;
  if (head === 'steps') return <Steps {...data.props} />;
  if (head === 'versus') return <Versus {...data.props} />;
  if (head === 'units') return <Units {...data.props} />;
  if (head === 'gen1') return <Gen1Map data={data} dur={dur} />;
  if (head === 'yeongtong') return <YeongtongMap dur={dur} />;
  if (head === 'direction') return <DirectionMap data={data} dur={dur} still={key === 'static'} />;
  if (head === 'counter') return <CounterMap data={data} dur={dur} />;
  if (head === 'line') return <Line flags={data.flagsAll} dur={dur} />;
  if (head === 'mix') return <Mix m={data.mix} dur={dur} />;
  // 아직 옮기지 않은 장면은 비워 두지 않고 **눈에 띄게** 표시한다.
  return (
    <Page>
      <div style={{fontSize: 44, fontWeight: 800, color: C.lose}}>
        아직 안 옮긴 장면: {name}
      </div>
    </Page>
  );
};
