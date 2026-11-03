import React from 'react';
import {Composition, staticFile, continueRender, delayRender} from 'remotion';
import {Main} from './Video';
import type {Plan} from './theme';

export const Root: React.FC = () => {
  const [plan, setPlan] = React.useState<Plan | null>(null);
  const [handle] = React.useState(() => delayRender('plan.json 읽는 중'));
  React.useEffect(() => {
    fetch(staticFile('plan.json'))
      .then((r) => r.json())
      .then((p) => {
        setPlan(p);
        continueRender(handle);
      });
  }, [handle]);
  if (!plan) return null;
  const total = plan.beats.reduce((s, b) => s + b.dur, 0);
  return (
    <Composition
      id="newtown1"
      component={Main as any}
      durationInFrames={Math.round(total * plan.fps)}
      fps={plan.fps}
      width={plan.width}
      height={plan.height}
      defaultProps={{plan} as any}
    />
  );
};
