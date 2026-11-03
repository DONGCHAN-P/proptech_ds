import fs from 'node:fs/promises';
import {execFileSync} from 'node:child_process';
const dir='video/public/pilot-v6';await fs.mkdir(dir,{recursive:true});
const texts=[
['광교, 무엇이 달랐나','먼저 광교입니다. 자연앤힐스테이트의 국민평형 실거래를 보면, 처음부터 곧장 오른 것은 아닙니다. 상승과 조정을 거치면서 가격대가 달라졌습니다. 한 번의 최고가보다, 여러 해에 걸친 중위가격의 흐름을 보는 이유입니다.'],
['광교의 세 가지 조건','광교를 설명하는 조건은 크게 세 가지로 묶어 볼 수 있습니다. 수원과 용인의 일자리 접근성, 신분당선으로 연결되는 강남, 그리고 도시가 완성되기 전에 시작한 분양가입니다. 하나의 시설보다 이 조건들이 함께 갖춰진 점에 주목하겠습니다.'],
['생활의 중심이 모이다','여기에 도시 안에서 생활을 해결할 수 있는 중심이 생겼습니다. 광교중앙역과 경기도청, 상업시설이 모이고, 원천호수와 신대호수를 잇는 호수공원이 생활의 공간을 만들었습니다. 출퇴근뿐 아니라 주말을 보내는 방식까지 도시의 매력을 바꾼 셈입니다.'],
['동탄, 역에 모인 기능','동탄은 역 주변에 여러 기능이 겹쳐졌다는 점이 눈에 띕니다. 동탄역 롯데캐슬은 주거와 백화점, 철도가 가까이 모인 사례입니다. 에스알티에 이어 지티엑스 에이까지 연결되면서, 서울과의 거리보다 실제 이동 방식이 달라졌습니다.'],
['철도는 시간을 바꾼다','철도는 계획 발표와 개통을 나눠서 봐야 합니다. 광교는 이천십육년 신분당선 연장, 동탄은 같은 해 에스알티, 이천이십사년 수서와 동탄을 잇는 지티엑스 에이 개통이 중요한 이정표였습니다. 노선 이름보다, 내가 이용할 구간이 언제 열렸는지가 핵심입니다.'],
['지역 안에서도 가격은 다르다','그런데 역 주변 단지의 가격이 도시 전체를 설명하지는 않습니다. 이번 수집 표본에서 동탄 이 신도시의 삼십 평대 중위가격은 칠억 팔천만 원입니다. 동탄역 롯데캐슬의 팔십사 제곱미터 중위가격과는 차이가 큽니다. 도시 이름만 보고 판단하면 이 차이가 사라집니다.'],
['운정·김포·옥정도 따로 보자','비교 지역도 같은 방식으로 봐야 합니다. 운정 아이파크, 한강센트럴자이, 옥정 제일풍경채는 입주 시점부터 다릅니다. 광교와 동탄의 오래된 이력을 그대로 대입할 수는 없습니다. 최근 거래가격, 회복 과정, 생활권의 조건을 각각 나눠서 보겠습니다.'],
['선은 언제나 위로 가지 않는다','대표 단지 차트에는 이천이십일년 이후의 하락 구간도 보입니다. 좋은 도시라고 해서 모든 시점에 좋은 매수가 되는 것은 아닙니다. 금리와 대출 조건, 당시의 매입가격, 주변 공급까지 함께 영향을 줍니다. 오늘의 결과를 과거에도 확실했던 성공으로 읽어서는 안 됩니다.'],
['다음 신도시에 던질 다섯 질문','앞으로 신도시를 볼 때는 다섯 가지를 묻겠습니다. 일자리는 가까운가. 철도는 입주 시점에 실제로 이용할 수 있는가. 분양가는 주변 주택과 비교해 어떤가. 생활의 중심이 만들어지는가. 같은 생활권의 공급은 얼마나 겹치는가. 이 질문에 대한 근거를 하나씩 모아야 합니다.'],
['신도시 이름보다 생활권','광교와 동탄을 통해 확인한 것은, 신도시라는 이름만으로 가격을 설명하기 어렵다는 점입니다. 일자리와 이동, 생활의 중심이 만나는 곳을 보고, 같은 면적의 실거래로 확인해야 합니다. 다음 작업에서는 이 기준으로 다른 신도시의 생활권을 하나씩 살펴보겠습니다.']
];
const env={};for(const l of (await fs.readFile('.env','utf8')).split(/\r?\n/)){const m=l.match(/^\s*([A-Z_0-9]+)\s*=\s*(.*?)\s*$/);if(m)env[m[1]]=m[2].replace(/^(['"])(.*)\1$/,'$2');}
const segments=[];for(let i=0;i<texts.length;i++){const [title,text]=texts[i],file=`voice-${i}.mp3`;try{await fs.access(`${dir}/${file}`);}catch{const r=await fetch(`https://api.elevenlabs.io/v1/text-to-speech/${env.ELEVENLABS_VOICE_ID}?output_format=mp3_44100_128`,{method:'POST',headers:{'xi-api-key':env.ELEVENLABS_API_KEY,'Content-Type':'application/json'},body:JSON.stringify({text,model_id:'eleven_v4'}),signal:AbortSignal.timeout(90000)});if(!r.ok)throw Error('TTS HTTP '+r.status);await fs.writeFile(`${dir}/${file}`,Buffer.from(await r.arrayBuffer()));}
const duration=Number(execFileSync('video/node_modules/@remotion/compositor-win32-x64-msvc/ffprobe.exe',['-v','error','-show_entries','format=duration','-of','default=noprint_wrappers=1:nokey=1',`${dir}/${file}`],{encoding:'utf8'}));segments.push({title,text,file,duration,frames:Math.ceil((duration+1.4)*30)});console.log(`${i+1}/${texts.length}: ${title} (${duration.toFixed(1)}s)`);await fs.writeFile(`${dir}/plan.json`,JSON.stringify({segments},null,2));}
