import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {createRequire} from 'node:module';
const require=createRequire(import.meta.url);
const {chromium}=require('C:/Users/백창현/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const dir=path.dirname(fileURLToPath(import.meta.url));
const out=path.resolve(dir,'../../figures/naver_20260918/qa');fs.mkdirSync(out,{recursive:true});
const browser=await chromium.launch({executablePath:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',headless:true});
const report=[];
try{
 for(const width of [1280,390]){
  const page=await browser.newPage({viewport:{width,height:900},deviceScaleFactor:1});
  for(const name of ['index','01_ball_count','02_bcai','03_bcap','04_references_ko']){
   await page.goto(pathToFileURL(path.join(dir,name+'.html')).href);
   await page.locator('body').waitFor();
   const status=await page.evaluate(()=>({title:document.title,viewport:innerWidth,width:document.documentElement.scrollWidth,images:[...document.images].map(x=>({src:x.getAttribute('src'),loaded:x.complete&&x.naturalWidth>0})),tables:document.querySelectorAll('table').length,headings:document.querySelectorAll('h1').length}));
   await page.screenshot({path:path.join(out,`${name}_${width}.png`)});
   if(name==='01_ball_count'){
    await page.locator('#section-3').scrollIntoViewIfNeeded();
    await page.screenshot({path:path.join(out,`main_batter_${width}.png`)});
   }
   if(name!=='index'){
    await page.locator('.interpretation-note').first().scrollIntoViewIfNeeded();
    await page.screenshot({path:path.join(out,`${name}_note_${width}.png`)});
    const labels=await page.evaluate(()=>({notes:document.querySelectorAll('.interpretation-note').length,cited:document.querySelectorAll('.citation-note').length,noteFont:getComputedStyle(document.querySelector('.interpretation-note')).fontFamily,bodyFont:getComputedStyle(document.querySelector('article')).fontFamily}));
    Object.assign(status,labels);
    if(name==='04_references_ko'){
     await page.locator('.citation-note').first().scrollIntoViewIfNeeded();
     await page.screenshot({path:path.join(out,`references_cited_${width}.png`)});
    }
   }
   report.push({name,...status});
  }
  await page.close();
 }
}finally{await browser.close();}
const anchorChecks=[];
for(const name of ['index','01_ball_count','02_bcai','03_bcap','04_references_ko']){
 const html=fs.readFileSync(path.join(dir,name+'.html'),'utf8');
 for(const m of html.matchAll(/href="([^"#]*\.html)?#([^"#]+)"/g)){
  const target=m[1]?path.resolve(dir,m[1]):path.join(dir,name+'.html');
  const text=fs.readFileSync(target,'utf8');
  anchorChecks.push({from:name,target:m[1]||name+'.html',anchor:m[2],exists:text.includes(`id="${m[2]}"`)});
 }
}
const pass=report.every(r=>r.width<=r.viewport&&r.images.every(i=>i.loaded)&&r.headings===1&&(r.name==='index'||(r.notes>0&&r.noteFont!==r.bodyFont))&&(r.name!=='04_references_ko'||r.cited===12))&&anchorChecks.every(x=>x.exists);
fs.writeFileSync(path.join(dir,'visual_check.json'),JSON.stringify({pass,checks:report,anchorChecks},null,2),'utf8');
console.log(JSON.stringify({pass,pages:report.length,unloaded:report.flatMap(r=>r.images.filter(i=>!i.loaded)),overflow:report.filter(r=>r.width>r.viewport)},null,2));
if(!pass)process.exitCode=1;
