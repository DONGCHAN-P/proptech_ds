import React from 'react';
import {C} from '../theme';
import {Page, useRise} from '../Cards';

/** 나란히 놓아야 뜻이 생기는 짝. 두 장에 나누면 앞 장을 기억해야 한다. */
export const Versus: React.FC<{sec?: string; left: any; right: any; mark?: string; dark?: boolean}> =
({sec, left, right, mark = '→', dark}) => {
  const a = useRise(0, 28);
  const b = useRise(6, 28);
  const h = useRise(0);
  const col = (c: any, st: React.CSSProperties) => (
    <div style={{...st, flex: 1, minWidth: 0, borderRadius: 20, padding: '34px 38px',
      border: `3px solid ${dark ? 'rgba(255,255,255,.16)' : C.line}`,
      background: dark ? 'rgba(255,255,255,.05)' : 'rgba(0,0,0,.025)'}}>
      <div style={{display: 'inline-block', fontSize: 24, fontWeight: 800,
        padding: '7px 16px', borderRadius: 9, color: '#fff', background: c.color}}>{c.tag}</div>
      <div style={{fontSize: 52, fontWeight: 800, letterSpacing: '-.03em', lineHeight: 1.22, marginTop: 20}}
        dangerouslySetInnerHTML={{__html: c.title}} />
      <div style={{fontSize: 29, lineHeight: 1.5, marginTop: 16, color: dark ? 'rgba(255,255,255,.66)' : C.sub}}
        dangerouslySetInnerHTML={{__html: c.sub}} />
    </div>
  );
  return (
    <Page dark={dark}>
      {sec ? <div style={{...h, fontSize: 34, fontWeight: 700, color: dark ? 'rgba(255,255,255,.55)' : C.sub, marginBottom: 30}}>{sec}</div> : null}
      <div style={{display: 'flex', alignItems: 'stretch'}}>
        {col(left, a)}
        <div style={{flex: 'none', width: 104, display: 'flex', alignItems: 'center',
          justifyContent: 'center', fontSize: 46, fontWeight: 800, color: C.sub, ...b}}>{mark}</div>
        {col(right, b)}
      </div>
    </Page>
  );
};
