from pathlib import Path
p=Path(__file__).parent/'template.html';s=p.read_text(encoding='utf8')
s=s.replace('let drag=null,moved=0;', 'function inside(x,y,rings){let c=false;for(const ring of rings)for(let j=0,k=ring.length-1;j<ring.length;k=j++){let [a,b]=ring[j],[u,v]=ring[k];if((b>y)!=(v>y)&&x<(u-a)*(y-b)/(v-b)+a)c=!c}return c}let drag=null,moved=0;')
s=s.replace("ctx.isPointInPath(paths[i],x,-y,'evenodd')",'inside(x,y,a.rings)')
s=s.replace('ns.every(Number.isFinite)',"keys.every(k=>ex.AM[k]!==undefined&&ex.AM[k]!=='')&&ns.every(Number.isFinite)")
p.write_text(s,encoding='utf8')
