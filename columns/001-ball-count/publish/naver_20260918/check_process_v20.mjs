import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {createRequire} from 'node:module';
const require=createRequire(import.meta.url);
const {chromium}=require('C:/Users/백창현/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const D=path.dirname(fileURLToPath(import.meta.url)),out=path.join(D,'process_v20/qa');fs.mkdirSync(out,{recursive:true});
const browser=await chromium.launch({headless:true,executablePath:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'}),checks=[];
try{for(const width of [1280,390,360]){
 const page=await browser.newPage({viewport:{width,height:950}});
 await page.goto(pathToFileURL(path.join(D,'05_data_validation.html')).href);await page.evaluate(()=>document.fonts.ready);
 const r=await page.evaluate(()=>({overflow:document.documentElement.scrollWidth>innerWidth+1,brokenImages:[...document.images].filter(i=>!i.complete||!i.naturalWidth).map(i=>i.src),literalEmphasis:document.body.innerText.includes('**'),links:[...document.querySelectorAll('a[href]')].map(a=>a.href)}));
 const brokenLinks=[];for(const h of new Set(r.links)){const u=new URL(h);if(u.protocol!=='file:')continue;const f=fileURLToPath(u);if(!fs.existsSync(f)){brokenLinks.push(h);continue;}if(u.hash&&!fs.readFileSync(f,'utf8').includes(`id="${decodeURIComponent(u.hash.slice(1))}"`))brokenLinks.push(h);}
 delete r.links;checks.push({width,...r,brokenLinks,pass:!r.overflow&&!r.brokenImages.length&&!r.literalEmphasis&&!brokenLinks.length});
 await page.screenshot({path:path.join(out,`opening_${width}.png`)});
 for(const n of [2,7,9]){await page.locator('h2').filter({hasText:new RegExp('^'+n+'\\.')}).scrollIntoViewIfNeeded();await page.screenshot({path:path.join(out,`chapter${n}_${width}.png`)});}
 await page.close();
}}finally{await browser.close();}
const report={pass:checks.every(r=>r.pass),checks};fs.writeFileSync(path.join(D,'process_v20/visual_check.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report));if(!report.pass)process.exitCode=1;
