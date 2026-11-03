import assert from 'node:assert/strict';
import {homography,project,cssMatrix,trackedQuad} from '../../../../video/src/data-insight-v2/homography.ts';
const quad=[[260,200],[1590,145],[1480,860],[340,820]];
const h=homography(1600,1000,quad);
[[0,0],[1600,0],[1600,1000],[0,1000]].forEach((p,i)=>{
 const actual=project(h,p);
 assert.ok(Math.hypot(actual[0]-quad[i][0],actual[1]-quad[i][1])<1e-7);
});
const values=cssMatrix(h).slice(9,-1).split(',').map(Number);
const [x,y]=[650,480];
const w=values[3]*x+values[7]*y+values[15];
const css=[(values[0]*x+values[4]*y+values[12])/w,(values[1]*x+values[5]*y+values[13])/w];
const expected=project(h,[x,y]);
assert.ok(Math.hypot(css[0]-expected[0],css[1]-expected[1])<1e-7);
const second=quad.map(([x,y])=>[x+8,y-4]);
const middle=trackedQuad([{time:0,quad},{time:2,quad:second}],1);
middle.forEach((p,i)=>assert.deepEqual(p,[quad[i][0]+4,quad[i][1]-2]));
assert.throws(()=>homography(1600,1000,[[0,0],[0,0],[0,0],[0,0]]));
console.log(JSON.stringify({status:'pass',corner_error_px:'<1e-7',css_matrix_mapping:'pass',track_interpolation:'pass',degenerate_rejected:true}));
