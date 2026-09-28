import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {createRequire} from 'node:module';
const require=createRequire(import.meta.url);
const {chromium}=require('C:/Users/백창현/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const D=path.dirname(fileURLToPath(import.meta.url));
const out=path.join(D,'models_v17/qa');fs.mkdirSync(out,{recursive:true});
const browser=await chromium.launch({headless:true,executablePath:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'});
const checks=[];
try {
 for(const width of [1280,390,360]){
  const page=await browser.newPage({viewport:{width,height:950},deviceScaleFactor:1});
  for(const name of ['02_bcai']){
   await page.goto(pathToFileURL(path.join(D,name+'.html')).href);
   await page.evaluate(()=>document.fonts.ready);
   const result=await page.evaluate(()=>({
    overflow:document.documentElement.scrollWidth>innerWidth+1,
    brokenImages:[...document.images].filter(i=>!i.complete||!i.naturalWidth).map(i=>i.src),
    literalEmphasis:document.body.innerText.includes('**'),
    strikethrough:document.querySelectorAll('del').length,
    questionHeadings:[...document.querySelectorAll('h2,h3,h4')].filter(h=>h.innerText.includes('?')).map(h=>h.innerText),
    links:[...document.querySelectorAll('a[href]')].map(a=>a.href),
    matrixCells:document.querySelectorAll('.count-matrix td').length,
    cellOverflow:[...document.querySelectorAll('.count-matrix td,.count-matrix th')].some(c=>c.scrollWidth>c.clientWidth+1)
   }));
   const brokenLinks=[];
   for(const href of new Set(result.links)){
    const u=new URL(href);if(u.protocol!=='file:')continue;
    const f=fileURLToPath(u);
    if(!fs.existsSync(f)){brokenLinks.push(href);continue;}
    if(u.hash){const src=fs.readFileSync(f,'utf8'),id=decodeURIComponent(u.hash.slice(1));if(!src.includes(`id="${id}"`)&&!src.includes(`id='${id}'`))brokenLinks.push(href);}
   }
   delete result.links;
   const pass=!result.overflow&&!result.brokenImages.length&&!result.literalEmphasis&&!result.strikethrough&&!result.questionHeadings.length&&!result.cellOverflow&&result.matrixCells===12&&!brokenLinks.length;
   checks.push({name,width,...result,brokenLinks,pass});
   await page.screenshot({path:path.join(out,`${name}_${width}.png`)});
   await page.locator('.count-board').screenshot({path:path.join(out,`${name}_table_${width}.png`)});
   const heading=page.locator('h3').filter({hasText:name==='03_bcap'?'7단계':'Ridge로'}).first();
   await heading.scrollIntoViewIfNeeded();await page.screenshot({path:path.join(out,`${name}_method_${width}.png`)});
   if(name==='02_bcai'){
    for(let i=0;i<await page.locator('table.mobile-cards').count();i++)await page.locator('table.mobile-cards').nth(i).screenshot({path:path.join(out,`${name}_detail_${i}_${width}.png`)});
   }
  }
  await page.close();
 }
} finally {await browser.close();}
const report={pass:checks.every(c=>c.pass),checks};
fs.writeFileSync(path.join(D,'models_v17/visual_check.json'),JSON.stringify(report,null,2));
console.log(JSON.stringify(report));if(!report.pass)process.exitCode=1;

