import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {createRequire} from 'node:module';
const require=createRequire(import.meta.url);
const {chromium}=require('C:/Users/백창현/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const D=path.dirname(fileURLToPath(import.meta.url));
const out=path.join(D,'main_v14/qa');fs.mkdirSync(out,{recursive:true});
const files=['01_ball_count.html'];
const browser=await chromium.launch({headless:true,executablePath:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'});
const checks=[],errors=[];
try {
 for(const width of [1280,390,360]){
  const page=await browser.newPage({viewport:{width,height:900},deviceScaleFactor:1});
  page.on('pageerror',e=>errors.push(String(e)));
  for(const file of files){
   await page.goto(pathToFileURL(path.join(D,file)).href);await page.evaluate(()=>document.fonts.ready);
   const result=await page.evaluate(()=>({
    overflow:document.documentElement.scrollWidth>innerWidth+1,
    unintendedStrikethrough:document.querySelectorAll('del').length,
    literalEmphasis:document.body.innerText.includes('**'),
    brokenImages:[...document.images].filter(i=>!i.complete||!i.naturalWidth).map(i=>i.src),
    links:[...document.querySelectorAll('a[href]')].map(a=>a.href),
    mobileCards:[...document.querySelectorAll('table.mobile-cards tbody tr')].every(r=>getComputedStyle(r).display==='block'),
    wideTables:document.querySelectorAll('table.mobile-cards').length
   }));
   const brokenLinks=[];
   for(const href of new Set(result.links)){
    const u=new URL(href);if(u.protocol!=='file:')continue;
    const target=fileURLToPath(u);
    if(!fs.existsSync(target)){brokenLinks.push(href);continue;}
    if(u.hash){
     const id=decodeURIComponent(u.hash.slice(1));
     const src=fs.readFileSync(target,'utf8');
     if(!src.includes(`id="${id}"`)&&!src.includes(`id='${id}'`))brokenLinks.push(href);
    }
   }
   const item={file,width,overflow:result.overflow,brokenImages:result.brokenImages,brokenLinks,wideTables:result.wideTables,mobileCards:width===390?result.mobileCards:null};
   item.unintendedStrikethrough=result.unintendedStrikethrough;
   item.literalEmphasis=result.literalEmphasis;
   item.pass=!item.overflow&&!item.unintendedStrikethrough&&!item.literalEmphasis&&!item.brokenImages.length&&!item.brokenLinks.length&&(width!==390||result.mobileCards);
   checks.push(item);
   if(true)await page.screenshot({path:path.join(out,file.replace('.html','')+'_'+width+'.png'),fullPage:false});
   for(const [label,selector] of [['results','.result-note'],['note','.interpretation-note']]){
    const loc=page.locator(selector).first();if(await loc.count()){await loc.scrollIntoViewIfNeeded();await page.screenshot({path:path.join(out,file.replace('.html','')+'_'+label+'_'+width+'.png')});}
   }
   if(file==='01_ball_count.html'){
    for (const cls of ['bcai-board','location-board']) {
      const board=page.locator('.'+cls);
      const state=await board.evaluate(b=>({cells:b.querySelectorAll('td').length,rows:b.querySelectorAll('tbody tr').length,overflow:[...b.querySelectorAll('td,th')].some(e=>e.scrollWidth>e.clientWidth+1),boardWidth:b.getBoundingClientRect().width}));
      checks.push({file,width,matrix:cls,...state,pass:state.cells===12&&state.rows===4&&!state.overflow});
      await board.screenshot({path:path.join(out,`${cls}_${width}.png`)});
    }
    await page.locator('.reference-note').first().screenshot({path:path.join(out,`reference_${width}.png`)});
    for(let t=0;t<await page.locator('.comparison-table').count();t++) await page.locator('.comparison-table').nth(t).screenshot({path:path.join(out,`table_${t}_${width}.png`)});

    for(let i=0;i<await page.locator('figure').count();i++)await page.locator('figure').nth(i).screenshot({path:path.join(out,`figure_${i+1}_${width}.png`)});
    if(width===390){
     for(let i=0;i<await page.locator('figure').count();i++){
      const fig=page.locator('figure').nth(i);await fig.locator('button').click();
      const zoom=await fig.evaluate(f=>({expanded:f.querySelector('button').getAttribute('aria-expanded')==='true',imageWidth:f.querySelector('img').getBoundingClientRect().width,documentOverflow:document.documentElement.scrollWidth>innerWidth+1}));
      checks.push({file,width,figure:i+1,zoom,pass:zoom.expanded&&zoom.imageWidth===900&&!zoom.documentOverflow});
      if(i===3)await fig.screenshot({path:path.join(out,'figure_4_390_expanded.png')});
      await fig.locator('button').click();
     }
    }
   }
   if(file==='03_bcap.html'&&width===390)await page.locator('tbody tr').first().screenshot({path:path.join(out,'comparison_card_390.png')});
  }
  await page.close();
 }
} finally {await browser.close();}
const report={checkedAt:new Date().toISOString(),pass:checks.every(c=>c.pass)&&!errors.length,pages:files.length,viewports:[1280,390,360],checks,errors,note:'실제 Edge 1280·390·360px 렌더링, 이미지·로컬 링크·앵커·4×3 표 및 셀 넘침 검사. 외부 웹 접근 및 수치 검증과는 별도.'};
fs.writeFileSync(path.join(D,'main_v14/visual_check.json'),JSON.stringify(report,null,2));
console.log(JSON.stringify(report));if(!report.pass)process.exitCode=1;
