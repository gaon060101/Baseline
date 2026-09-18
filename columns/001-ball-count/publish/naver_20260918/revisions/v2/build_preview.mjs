import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {createRequire} from 'node:module';
const require=createRequire(import.meta.url);
const {marked}=require('C:/Users/백창현/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/marked/lib/marked.esm.js');
const dir=path.dirname(fileURLToPath(import.meta.url));
const names=['01_ball_count','02_bcai','03_bcap','04_references_ko'];
const short=['볼카운트 분석 칼럼','BCAI 설명 글','BCAP 설명 글','참고문헌 한국어 해설'];
const mainPath=path.join(dir,names[0]+'.md');
let main=fs.readFileSync(mainPath,'utf8');
const refLabels=['카운트별 타율 연구','한 공의 가치 분석','1887년 역사 연구','0-2 위치 분석','멀리 벗어난 공의 분석','BART 연구 원문','3-0·3-1 분석','경계 공 테이크 분석','Kovash·Levitt 원문','최적 투구 연구 원문','MONEYBaRL 원문','1-1 경로 분석'];
const refs={};
for(const m of main.matchAll(/^(\d+)\. [^\n]*?\[[^\]]+\]\((https:[^)]+)\)/gm)) refs[m[1]]=m[2];
main=main.replace(/\[(\d+)\](?!\()/g,(all,n)=>refs[n]?`[${n} · ${refLabels[Number(n)-1]}](${refs[n]})`:all);
fs.writeFileSync(mainPath,main,'utf8');
const esc=s=>s.replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;');
const css=`
:root{--ink:#19383d;--teal:#147c80;--muted:#637579;--line:#dae5e5}
*{box-sizing:border-box}body{margin:0;background:#f5f8f7;color:var(--ink);font-family:'Malgun Gothic','맑은 고딕',sans-serif}
a{color:#156c76;text-underline-offset:4px;overflow-wrap:anywhere}a:hover{color:#b04e28}
.topbar{max-width:980px;margin:auto;padding:26px 36px;display:flex;justify-content:space-between;gap:16px;font-size:13px;letter-spacing:.5px}
.brand{font-weight:800;letter-spacing:3px;text-decoration:none}.meta{color:var(--muted)}
nav{max-width:908px;margin:0 auto 22px;display:flex;gap:8px;flex-wrap:wrap}nav a{padding:10px 16px;border:1px solid var(--line);border-radius:22px;background:white;text-decoration:none;font-size:14px}nav a.current{background:var(--ink);color:white}
main{max-width:908px;margin:0 auto 60px;padding:58px 64px;background:#fff;border:1px solid var(--line);border-radius:8px;box-shadow:0 4px 24px #18393b06}
article{font-size:18px;line-height:1.95;word-break:keep-all;overflow-wrap:break-word}
h1{font-size:38px;letter-spacing:-1.7px;line-height:1.45;margin:0 0 28px}h2{font-size:27px;line-height:1.5;letter-spacing:-.8px;margin:78px 0 25px;padding-top:24px;border-top:2px solid #cee1df;scroll-margin-top:24px}h3{font-size:21px;line-height:1.6;margin:40px 0 20px}
p{margin:0 0 25px}strong{font-weight:750;color:#102f36}em{font-style:normal;color:var(--muted)}p:has(>em:only-child){font-size:13px;line-height:1.8;margin-top:-10px;margin-bottom:32px}
blockquote{margin:28px 0;padding:25px 29px;border-left:4px solid var(--teal);background:#f2f7f6;font-size:17px}blockquote p:last-child{margin-bottom:0}
.interpretation-note{margin:30px 0;padding:23px 26px;border-left:5px solid #ae773a;background:#fbf3e6;color:#644928;font-family:'Batang','바탕',serif;font-size:16px;line-height:1.95}.interpretation-note strong{font-family:'Malgun Gothic',sans-serif;color:#79521f;font-size:15px}.interpretation-note p:last-child,.citation-note p:last-child{margin-bottom:0}.citation-note{margin:28px 0;padding:23px 26px;border-left:5px solid #34845d;background:#eef7ee;font-size:17px}.citation-note strong{color:#236342}a[id^='ref-']{display:block;scroll-margin-top:25px}
figure{margin:35px -14px 20px}img{display:block;max-width:100%;height:auto;border:1px solid #e7eeee;margin:auto}.image-link{cursor:zoom-in}
.table-wrap{overflow:auto;margin:26px 0 22px;border:1px solid var(--line);border-radius:5px}table{border-collapse:collapse;width:100%;font-size:14px;line-height:1.7}th,td{padding:13px 13px;border-bottom:1px solid #e4ebea;vertical-align:top;text-align:left}th{background:#edf4f2;color:#244b50;font-weight:700}tr:last-child td{border-bottom:0}td:first-child{font-weight:650}tbody tr:nth-child(even){background:#fafcfc}
li{margin:10px 0}ul,ol{padding-left:25px}hr{border:0;border-top:1px solid var(--line);margin:58px 0}
.toc{margin:40px 0;padding:18px 23px;border:1px solid var(--line);border-radius:5px;font-size:14px;background:#f8fbfa}.toc summary{cursor:pointer;font-weight:bold}.toc ul{margin:12px 0 3px}.toc a{text-decoration:none}
.endnav{margin:46px 0 0;border-top:1px solid var(--line);padding-top:24px;display:flex;gap:15px;flex-wrap:wrap;font-size:14px}
.lead{font-size:20px;line-height:1.9;color:#36555a}.cards{display:grid;gap:18px;margin:38px 0}.card{display:block;text-decoration:none;background:#f4f8f6;border:1px solid var(--line);border-radius:8px;padding:26px 28px}.card small{display:block;color:var(--teal);letter-spacing:2px;margin-bottom:9px}.card b{font-size:24px;line-height:1.6}.card p{margin:12px 0 0;font-size:15px;line-height:1.8;color:var(--muted)}.note{font-size:14px;line-height:1.8;color:var(--muted);padding:20px;background:#f7f3e9;border-radius:5px}
@media(max-width:650px){.topbar{padding:20px;display:block}.meta{display:block;margin-top:8px}nav{margin:0 16px 16px;gap:6px}nav a{font-size:12px;padding:9px 12px}main{margin:0 8px 25px;padding:32px 18px;border-radius:5px}article{font-size:17px;line-height:1.95}h1{font-size:29px;letter-spacing:-1px}h2{font-size:24px;margin-top:55px}h3{font-size:20px}p{margin-bottom:24px}.table-wrap{margin:24px -6px}table{font-size:12px;min-width:480px}th,td{padding:10px}figure{margin:28px -8px 20px}p:has(>em:only-child){font-size:12px}blockquote{padding:20px}.card{padding:23px}.card b{font-size:21px}.lead{font-size:18px}}
@media print{body{background:white}.topbar,nav,.toc,.endnav{display:none}main{max-width:none;border:0;padding:0;box-shadow:none}article{font-size:11pt;line-height:1.8}h1{font-size:23pt}h2{font-size:18pt;margin-top:28px}figure,table{break-inside:avoid}img{max-height:850px}a{color:inherit}}
`;
const nav=current=>`<nav aria-label="연재 글">${names.map((n,i)=>`<a class="${n===current?'current':''}" href="${n}.html">${i+1}. ${short[i]}</a>`).join('')}</nav>`;
const page=(title,content,current='')=>`<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>${esc(title)} | Baseline</title><style>${css}</style></head><body><header class="topbar"><a class="brand" href="index.html">BASELINE</a><span class="meta">볼카운트 연재 · 2026.09.18 · 사용자 검토본</span></header>${nav(current)}<main>${content}</main></body></html>`;
const report={articles:[],missing_links:[],figure_count:8};
for(let i=0;i<names.length;i++){
  const n=names[i];const src=fs.readFileSync(path.join(dir,n+'.md'),'utf8');
  let html=marked.parse(src);let h=0;const headings=[];
  html=html.replace(/<h2>(.*?)<\/h2>/g,(_,v)=>{const id='section-'+(++h);headings.push([id,v]);return `<h2 id="${id}">${v}</h2>`;});
  html=html.replace(/<table>/g,'<div class="table-wrap"><table>').replace(/<\/table>/g,'</table></div>');
  html=html.replace(/<p>(<img [^>]+>)<\/p>/g,(_,img)=>{const s=img.match(/src="([^"]+)"/)[1];return `<figure><a class="image-link" href="${s}" target="_blank" aria-label="그림 크게 보기">${img}</a></figure>`;});
  html=html.replace(/<blockquote>([\s\S]*?)<\/blockquote>/g,(all,body)=>body.includes('<strong>해석 메모 |')?`<aside class="interpretation-note" aria-label="해석 메모">${body}</aside>`:body.includes('<strong>칼럼에서 가져온 부분 |')?`<aside class="citation-note" aria-label="칼럼 인용 부분">${body}</aside>`:all);
  for(const name of names) {html=html.replaceAll(`href="${name}.md"`,`href="${name}.html"`);html=html.replaceAll(`href="${name}.md#`,`href="${name}.html#`);}
  for(const m of src.matchAll(/!?\[[^\]]*\]\(([^)]+)\)/g)){
    let url=m[1];if(url.startsWith('http')||url.startsWith('#'))continue;
    const target=path.resolve(dir,url.split('#')[0]);if(!fs.existsSync(target))report.missing_links.push({file:n,link:url});
  }
  const toc=`<details class="toc"><summary>이 글의 목차</summary><ul>${headings.map(([id,v])=>`<li><a href="#${id}">${v}</a></li>`).join('')}</ul></details>`;
  html=html.replace(/(<h1>.*?<\/h1>)/s,`$1${toc}`);
  const endnav=`<div class="endnav"><a href="index.html">연재와 문헌 읽기 안내</a>${names.filter(k=>k!==n).map(k=>`<a href="${k}.html">${short[names.indexOf(k)]}</a>`).join('')}</div>`;
  const title=src.split('\n')[0].replace(/^# /,'');
  fs.writeFileSync(path.join(dir,n+'.html'),page(title,`<article>${html}</article>${endnav}`,n),'utf8');
  report.articles.push({file:n+'.md',characters:src.length,images:(src.match(/!\[/g)||[]).length,tables:(src.match(/^\| ---/gm)||[]).length,headings:headings.length});
}
const descriptions=['“0-2에 볼을 하나 빼라”에서 출발합니다. 질문을 세우고 비교 기준과 그림을 읽으며 결과를 함께 알아갑니다.','결과에 점수를 붙이고 타석을 모은 뒤 100 기준 지수로 만드는 과정을 예시와 함께 설명합니다.','선수·상황 보정, 행동 선택 확률, 교차적합, 자료 부족을 단계별로 설명합니다.','본문에서 사용한 12건의 질문·방법·결과를 한국어로 읽습니다. 인용 부분은 초록 상자, 별도 개념 설명은 가상 예시와 함께 구분했습니다.'];
const index=`<h1>다음 공을 읽는<br>세 편과 문헌 해설</h1><p class="lead">분석 칼럼을 먼저 읽고, 계산이나 용어가 궁금해질 때 BCAI·BCAP 설명 글을 참고하세요. 외부 연구는 한국어 문헌 해설에서 이어 읽을 수 있습니다.</p><div class="cards">${names.map((n,i)=>`<a class="card" href="${n}.html"><small>0${i+1} / ${i===3?'읽기 자료':i?'방법 해설':'본문'}</small><b>${short[i]}</b><p>${descriptions[i]}</p></a>`).join('')}</div><p class="note">설명을 보강한 2차 사용자 검토본입니다. 갈색 상자는 해석 메모, 초록 상자는 문헌에서 인용한 부분입니다. 글의 표는 편집 가능한 형태이며, 차트·도식 8장은 PNG로 준비했습니다. 그림을 누르면 크게 볼 수 있습니다. 외부 게시와 드라이브 업로드는 하지 않았습니다.</p><p><a href="네이버_첨부그림_8장.zip">차트·도식 PNG 8장 받기</a> · <a href="README.md">원고와 그림 배치 안내</a></p>`;
fs.writeFileSync(path.join(dir,'index.html'),page('볼카운트 연재 세 글',index),'utf8');
fs.writeFileSync(path.join(dir,'render_check.json'),JSON.stringify(report,null,2),'utf8');
if(report.missing_links.length)throw new Error(JSON.stringify(report.missing_links));
console.log(JSON.stringify(report,null,2));
