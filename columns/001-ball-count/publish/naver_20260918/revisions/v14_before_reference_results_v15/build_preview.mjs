import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {createRequire} from 'node:module';
const require=createRequire(import.meta.url);
const {marked}=require('C:/Users/백창현/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/marked/lib/marked.esm.js');
const dir=path.dirname(fileURLToPath(import.meta.url));
const onlyMain=process.argv.includes('--only-main');
const onlyBcap=process.argv.includes('--only-bcap');
const names=['01_ball_count','02_bcai','03_bcap','04_references_ko','05_data_validation'];
const short=['볼카운트 분석 칼럼','BCAI 설명 글','BCAP 설명 글','참고문헌 한국어 해설','데이터·검증·개발 과정'];
const mainPath=path.join(dir,names[0]+'.md');
let main=fs.readFileSync(mainPath,'utf8');
const refLabels=['카운트별 타율 연구','한 공의 가치 분석','1887년 역사 연구','0-2 위치 분석','멀리 벗어난 공의 분석','BART 연구 원문','3-0·3-1 분석','경계 공 테이크 분석','Kovash·Levitt 원문','최적 투구 연구 원문','MONEYBaRL 원문','1-1 경로 분석'];
const refs={};
for(const m of main.matchAll(/^(\d+)\. [^\n]*?\[[^\]]+\]\((https:[^)]+)\)/gm)) refs[m[1]]=m[2];
main=main.replace(/\[(\d+)\](?!\()/g,(all,n)=>refs[n]?`[${n} · ${refLabels[Number(n)-1]}](${refs[n]})`:all);
// Markdown remains authoritative; rendering does not rewrite the manuscript.
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
.result-note{margin:26px 0 32px;padding:26px 28px;background:#e8f5f2;border:2px solid #167e78;border-radius:8px;font-size:19px;line-height:1.85}.result-note strong{display:block;color:#075b56;font-size:16px}.result-note p:last-child,.reference-note p:last-child{margin-bottom:0}.reference-note{margin:30px 0;padding:24px 27px;background:#f3f0fa;border:1px solid #d9cfeb;border-left:5px solid #8062ac;border-radius:0 8px 8px 0;font-size:16px;line-height:1.95}.reference-note strong{color:#64468c}.reference-note a{color:#62448e}h2{background:#edf3f2;padding:22px 20px;border-top:3px solid #577e7b;border-radius:3px}h3{padding-left:15px;border-left:3px solid #aac1bd}.sub-number{display:block;color:#6c8582;font-size:12px;letter-spacing:.7px;margin-bottom:4px}.section-summary{font-size:19px;color:#163f42}.toc li.subtopic{margin-left:18px;font-size:12px;border-left:2px solid #d8e5e2;padding-left:12px}.results-section>.table-wrap{border:2px solid #72a8a0}.results-section>h2{background:#dceee9;border-color:#147c80}h4{font-size:17px;margin:26px 0 14px}
figure{margin:35px -14px 20px}img{display:block;max-width:100%;height:auto;border:1px solid #e7eeee;margin:auto}.image-link{cursor:zoom-in}
.table-wrap{overflow:auto;margin:26px 0 22px;border:1px solid var(--line);border-radius:5px}table{border-collapse:collapse;width:100%;font-size:14px;line-height:1.7}th,td{padding:13px 13px;border-bottom:1px solid #e4ebea;vertical-align:top;text-align:left}th{background:#edf4f2;color:#244b50;font-weight:700}tr:last-child td{border-bottom:0}td:first-child{font-weight:650}tbody tr:nth-child(even){background:#fafcfc}
li{margin:10px 0}ul,ol{padding-left:25px}hr{border:0;border-top:1px solid var(--line);margin:58px 0}
.toc{margin:40px 0;padding:18px 23px;border:1px solid var(--line);border-radius:5px;font-size:14px;background:#f8fbfa}.toc summary{cursor:pointer;font-weight:bold}.toc ul{margin:12px 0 3px}.toc a{text-decoration:none}
.endnav{margin:46px 0 0;border-top:1px solid var(--line);padding-top:24px;display:flex;gap:15px;flex-wrap:wrap;font-size:14px}
.lead{font-size:20px;line-height:1.9;color:#36555a}.cards{display:grid;gap:18px;margin:38px 0}.card{display:block;text-decoration:none;background:#f4f8f6;border:1px solid var(--line);border-radius:8px;padding:26px 28px}.card small{display:block;color:var(--teal);letter-spacing:2px;margin-bottom:9px}.card b{font-size:24px;line-height:1.6}.card p{margin:12px 0 0;font-size:15px;line-height:1.8;color:var(--muted)}.note{font-size:14px;line-height:1.8;color:var(--muted);padding:20px;background:#f7f3e9;border-radius:5px}
@media(max-width:650px){.topbar{padding:20px;display:block}.meta{display:block;margin-top:8px}nav{margin:0 16px 16px;gap:6px}nav a{font-size:12px;padding:9px 12px}main{margin:0 8px 25px;padding:32px 18px;border-radius:5px}article{font-size:17px;line-height:1.95}h1{font-size:29px;letter-spacing:-1px}h2{font-size:24px;margin-top:55px}h3{font-size:20px}p{margin-bottom:24px}.table-wrap{margin:24px -6px}table{font-size:12px;min-width:480px}th,td{padding:10px}figure{margin:28px -8px 20px}p:has(>em:only-child){font-size:12px}blockquote{padding:20px}.card{padding:23px}.card b{font-size:21px}.lead{font-size:18px}}
@media(max-width:650px){.main-column table{min-width:0;table-layout:fixed}.main-column th,.main-column td{padding:10px 7px;overflow-wrap:anywhere}.main-column h4{padding:12px;background:#f6f8f7;border-bottom:1px solid #dae5e5}}
figure{max-width:100%}.figure-scroll{overflow-x:auto}.figure-scroll.zoomed a{display:block;width:900px}.figure-scroll.zoomed img{width:900px;max-width:none}.figure-toggle{font:inherit;font-size:14px;padding:8px 12px;color:#126d79;background:#eef6f3;border:1px solid #a7c7bf;border-radius:5px;cursor:pointer}
@media(max-width:650px){.table-wrap{overflow:visible;margin:22px 0}table.mobile-cards,table.mobile-cards tbody,table.mobile-cards tr,table.mobile-cards td{display:block;width:100%;min-width:0}table.mobile-cards thead{display:none}table.mobile-cards tr{margin-bottom:14px;border:1px solid #bcd1cd;border-radius:6px;padding:7px;background:#f8fbfa}table.mobile-cards td{border:0;border-bottom:1px solid #e0e8e6;font-size:15px;padding:8px;overflow-wrap:anywhere}table.mobile-cards td:before{content:attr(data-label);display:block;font-size:13px;font-weight:bold;color:#19615f}figure{margin-left:0;margin-right:0}}

/* Main manuscript: count matrices retain their 4 by 3 arrangement on phones. */
.main-column .count-board{margin:28px 0 20px;padding:18px 8px;background:#fff;border:1px solid #dbe6e4;border-radius:10px}
.main-column .board-subtitle{font-size:12px;color:#5b7376;margin:0 8px 12px}.main-column .board-title{font-size:18px;font-weight:750;margin:0 8px 12px;line-height:1.6}
.main-column table.count-matrix{width:100%;min-width:0;table-layout:fixed;border-collapse:separate;border-spacing:8px;font-size:14px}
.main-column .count-matrix th{background:none;border:0;text-align:center;padding:4px;font-size:16px;vertical-align:middle}
.main-column .count-matrix th:first-child{width:48px}
.main-column .count-matrix td{border:0;border-radius:12px;text-align:center;vertical-align:middle;padding:15px 5px;line-height:1.5}
.main-column .count-matrix tr{background:none}
.cell-count{display:block;font-size:15px;color:#546d71;margin-bottom:6px}
.cell-value{display:block;font-size:23px;white-space:nowrap;font-variant-numeric:tabular-nums;letter-spacing:-.6px}
.count-matrix small{display:block;font-size:12px;color:#50696c;margin-top:7px;letter-spacing:-.3px}
.count-matrix .pitcher{background:#deeeee}.count-matrix .pitcher strong{color:#147f83}.count-matrix .pitcher.strong-cell{background:#bfdddd}
.count-matrix .batter{background:#f8eae3}.count-matrix .batter strong{color:#b64f29}.count-matrix .batter.strong-cell{background:#e9bba7}
.count-matrix .neutral{background:#f0f3f3}.count-matrix .neutral strong{color:#365156}
.count-matrix .inside{background:#deeeeb}.count-matrix .inside strong{color:#1c6e62}.count-matrix .outside{background:#e8e1f3}.count-matrix .outside strong{color:#715095}
.board-legend{font-size:12px;display:flex;gap:14px;flex-wrap:wrap;padding:12px 10px 0}.pitcher-key{color:#147f83}.batter-key{color:#b64f29}
u.source-claim{text-decoration-color:#9577b9;text-decoration-thickness:2px;text-underline-offset:5px;text-decoration-skip-ink:auto}
.main-column .reference-note{font-size:14px;padding:15px 20px;margin:18px 0 28px;line-height:1.8}
.main-column .reference-note strong{font-size:14px}.main-column .reference-note p{margin-bottom:10px}
.main-column h3{margin-top:42px}.main-column h4{font-size:19px;line-height:1.7;margin:32px 0 18px}
.main-column .comparison-table{table-layout:fixed}.main-column .comparison-table td:first-child{width:35%}.main-column .comparison-table td strong{font-size:16px}
@media(max-width:650px){
 .main-column .count-board{padding:12px 2px;margin:24px -5px}.main-column .board-title{font-size:15px;margin:0 6px 8px}
 .main-column table.count-matrix{border-spacing:4px}.main-column .count-matrix th{font-size:12px;padding:3px 0;white-space:nowrap}.main-column .count-matrix th:first-child{width:28px}
 .main-column .count-matrix td{padding:12px 2px;border-radius:8px;overflow-wrap:normal}.cell-count{font-size:12px;margin-bottom:5px}
 .cell-value{font-size:18px;letter-spacing:-.3px;line-height:1.3}.range-end{display:block}.count-matrix small{font-size:10px;letter-spacing:-.5px;margin-top:6px}
 .main-column .location-board .cell-value{font-size:20px}.board-legend{font-size:11px;gap:3px 12px;padding:8px 6px 0}
 .main-column .comparison-table{width:100%;min-width:0;font-size:13px}.main-column .comparison-table th,.main-column .comparison-table td{padding:12px 8px}
 .main-column .comparison-table td strong{font-size:15px}.main-column h4{font-size:18px;padding:10px 0;background:none}
}


.main-column .question-group{margin:42px 0 22px;padding:14px 18px;border-top:2px solid #72918e;border-bottom:1px solid #cadbd8;background:#edf4f2;color:#285552;font-size:16px;font-weight:750}
.main-column .bcai-board .cell-value{font-size:34px;line-height:1.4}
@media(max-width:650px){.main-column .bcai-board .cell-value{font-size:27px}.main-column .question-group{font-size:15px;padding:12px}}

@media print{body{background:white}.topbar,nav,.toc,.endnav{display:none}main{max-width:none;border:0;padding:0;box-shadow:none}article{font-size:11pt;line-height:1.8}h1{font-size:23pt}h2{font-size:18pt;margin-top:28px}figure,table{break-inside:avoid}img{max-height:850px}a{color:inherit}}
`;
const nav=current=>`<nav aria-label="연재 글">${names.map((n,i)=>`<a class="${n===current?'current':''}" href="${n}.html">${i+1}. ${short[i]}</a>`).join('')}</nav>`;
const page=(title,content,current='')=>`<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>${esc(title)} | Baseline</title><style>${css}</style></head><body><header class="topbar"><a class="brand" href="index.html">BASELINE</a><span class="meta">볼카운트 연재 · 2026.09.28 · ${onlyMain?'본문 14차 검토본':'11시즌 반영 7차 검토본'}</span></header>${nav(current)}<main>${content}</main></body></html>`;
const report={articles:[],missing_links:[],figure_count:0};
for(const i of (onlyBcap?[2]:onlyMain?[0]:names.map((_,i)=>i))){
  const n=names[i];const src=fs.readFileSync(path.join(dir,n+'.md'),'utf8').replace(/^\uFEFF/,'');
  let html=marked.parse(src);
  // Korean particles immediately following punctuation can leave emphasis literal.
  html=html.replace(/\*\*([^*\n]+)\*\*/g,'<strong>$1</strong>');
  let h=0;const headings=[];
  let parentNumber='',sub=0;
  html=html.replace(/<h([23])>(.*?)<\/h\1>/g,(_,level,v)=>{
   if(level==='2'){const id='section-'+(++h);parentNumber=(v.match(/^(\d+)\./)||[])[1]||'';sub=0;headings.push([id,v,2]);return `<h2 id="${id}">${v}</h2>`;}
   const id=`section-${h}-sub-${++sub}`;headings.push([id,v,3]);return `<h3 id="${id}">${parentNumber&&n!=='01_ball_count'?`<span class="sub-number">${parentNumber}.${sub}</span>`:''}${v}</h3>`;
  });
  html=html.replace(/<table>([\s\S]*?)<\/table>/g,(_,body)=>{
 const labels=[...body.matchAll(/<th[^>]*>(.*?)<\/th>/gs)].map(m=>m[1].replace(/<[^>]+>/g,''));
 body=body.replace(/<tr>([\s\S]*?)<\/tr>/g,(_,r)=>{let j=0;return '<tr>'+r.replace(/<td([^>]*)>/g,(_,a)=>`<td${a} data-label="${esc(labels[j++]||'')}">`)+'</tr>';});
 return `<div class="table-wrap"><table class="${n==='01_ball_count'?'comparison-table':'mobile-cards'}">${body}</table></div>`;
 });
  html=html.replace(/<p>(<img [^>]+>)<\/p>/g,(_,img)=>{const s=img.match(/src="([^"]+)"/)[1];return `<figure><button class="figure-toggle" type="button" aria-expanded="false" onclick="const box=this.nextElementSibling;const expanded=box.classList.toggle('zoomed');this.setAttribute('aria-expanded',expanded);this.textContent=expanded?'그림 축소 · 좌우로 밀어 읽기':'그림 확대해서 읽기';">그림 확대해서 읽기</button><div class="figure-scroll"><a class="image-link" href="${s}" target="_blank" aria-label="그림 크게 보기">${img}</a></div></figure>`;});
  html=html.replace(/<blockquote>([\s\S]*?)<\/blockquote>/g,(all,body)=>{
   const styles=[['해석 메모 |','interpretation-note'],['연재에서 가져온 부분 |','citation-note'],['결과 요약 |','result-note'],['참고문헌 |','reference-note']];
   const style=styles.find(([label])=>body.includes('<strong>'+label));
   return style?`<aside class="${style[1]}" aria-label="${style[0].replace(' |','')}">${body}</aside>`:all;
  });
  html=html.replace(/(<h[23][^>]*>[\s\S]*?<\/h[23]>\s*)<p><strong>([^<]+)<\/strong>/g,'$1<p class="section-summary"><strong>$2</strong>');
  html=html.replace(/(<h2 id="([^"]+)">([^<]+)<\/h2>)([\s\S]*?)(?=<h2 |$)/g,(_,head,id,title,body)=>`<section class="content-section ${/^(먼저 보는 결과|1\. (주 )?결과|2\. 보조 결과)/.test(title)?'results-section':''}" aria-labelledby="${id}">${head}${body}</section>`);
  for(const name of names) {html=html.replaceAll(`href="${name}.md"`,`href="${name}.html"`);html=html.replaceAll(`href="${name}.md#`,`href="${name}.html#`);}
  for(const m of src.matchAll(/!?\[[^\]]*\]\(([^)]+)\)/g)){
    let url=m[1];if(url.startsWith('http')||url.startsWith('#'))continue;
    const target=path.resolve(dir,url.split('#')[0]);if(!fs.existsSync(target))report.missing_links.push({file:n,link:url});
  }
  const toc=`<details class="toc"><summary>이 글의 목차 — 결과·방법·해석</summary><ul>${headings.map(([id,v,level])=>`<li class="${level===3?'subtopic':''}"><a href="#${id}">${v}</a></li>`).join('')}</ul></details>`;
  if(n!=='01_ball_count') html=html.replace(/(<h1>.*?<\/h1>)/s,`$1${toc}`);
  const endnav=`<div class="endnav"><a href="index.html">연재와 문헌 읽기 안내</a>${names.filter(k=>k!==n).map(k=>`<a href="${k}.html">${short[names.indexOf(k)]}</a>`).join('')}</div>`;
  const title=src.split('\n')[0].replace(/^# /,'');
  let rendered=page(title,`<article>${html}</article>${endnav}`,n);
  if(n==='01_ball_count') rendered=rendered.replace('<body>','<body class="main-column">');
  fs.writeFileSync(path.join(dir,n+'.html'),rendered,'utf8');
  report.articles.push({file:n+'.md',characters:src.length,images:(src.match(/!\[/g)||[]).length,tables:(src.match(/^\| ---/gm)||[]).length,headings:headings.length});
}
const descriptions=['카운트·위치·스윙·구종의 결과를 경기 장면과 함께 읽습니다. 반복된 검증 설명을 덜고 용어 풀이를 붙였습니다.','열두 카운트의 결과표와 보조 결과를 먼저 제시합니다. 이후 타석·가중치·100 기준·불확실성을 설명합니다.','위치·타자 행동·구종 결과를 첫 절에 모았습니다. 결과의 의미, 계산 과정, 자료 부족과 한계를 이어 설명합니다.','12건의 연구를 한국어로 읽습니다. 본문 직접 인용과 확장 읽기를 나누고, 원문·활용 부분·해석을 구별했습니다.','무엇을 확인했는지 먼저 봅니다. 표본, 검증, 개발 과정과 시행착오, 모델의 한계와 남은 질문을 설명합니다.'];
const index=`<h1>결과부터 읽는<br>볼카운트 분석</h1><p class="lead">먼저 무엇을 알아냈는지, 다음으로 어떻게 구했고 무엇을 뜻하는지 읽습니다. 본문은 야구 이야기와 결과를 중심으로, 계산·문헌·검증은 별도 글로 읽을 수 있게 정리했습니다.</p><div class="cards">${names.map((n,i)=>`<a class="card" href="${n}.html"><small>0${i+1} / ${i>=3?'읽기 자료':i?'방법 해설':'본문'}</small><b>${short[i]}</b><p>${descriptions[i]}</p></a>`).join('')}</div><p class="note">4차 사용자 검토본입니다. 다섯 번째 글에 검증과 개발 과정을 모았습니다. 청록색은 자체 결과 요약, 보라색은 참고문헌, 갈색은 해석 메모, 초록색은 연재에서 활용한 문헌 내용입니다. 큰 제목은 주제, 작은 번호 제목은 그 아래 설명 단계입니다. 외부 게시·업로드는 하지 않았습니다.</p><p><a href="네이버_첨부그림_8장_v4.zip">차트·도식 PNG 8장 받기</a> · <a href="README.md">원고와 그림 배치 안내</a></p>`;
const legacyIndex=index.replace('4차 사용자 검토본입니다.','본문은 6차 질문형 설명본, 해설 02–05는 4차 검토본입니다. 본문은 각 장을 간단 설명 → 결과 한눈에 보기 → 상세 설명으로 구성했습니다.').replace('차트·도식 PNG 8장 받기','차트·도식 PNG 8장 받기 (배치 안내는 이전 4차)');
const currentIndex=index.replace('4차 사용자 검토본입니다.','2015~2025의 11시즌을 반영한 7차 사용자 검토본입니다. 본문은 질문 → 짧은 답·결과 → 예시·해석을 유지합니다.').replace('<a href="네이버_첨부그림_8장_v4.zip">차트·도식 PNG 8장 받기</a>','<a href="revision_v7.md">7차 수정·근거·그림 안내</a>');
report.figure_count=new Set((onlyBcap?[names[2]]:onlyMain?names.slice(0,1):names).flatMap(n=>[...fs.readFileSync(path.join(dir,n+'.md'),'utf8').matchAll(/!\[[^\]]*\]\(([^)]+)\)/g)].map(m=>m[1]))).size;
if(!onlyMain&&!onlyBcap) fs.writeFileSync(path.join(dir,'index.html'),page('볼카운트 연재 다섯 글',currentIndex).replace('4차 사용자 검토본','본문 6차 · 해설 4차 검토본'),'utf8');
fs.writeFileSync(path.join(dir,onlyMain?'main_v14/render_check.json':onlyBcap?'main_v14/bcap_render_check.json':'render_check.json'),JSON.stringify(report,null,2),'utf8');
if(report.missing_links.length)throw new Error(JSON.stringify(report.missing_links));
console.log(JSON.stringify(report,null,2));
