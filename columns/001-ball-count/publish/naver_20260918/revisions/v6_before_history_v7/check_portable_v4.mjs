import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import {spawnSync} from 'node:child_process';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {createRequire} from 'node:module';
const require=createRequire(import.meta.url);
const {chromium}=require('C:/Users/백창현/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const dir=path.dirname(fileURLToPath(import.meta.url));
const extracted=fs.mkdtempSync(path.join(os.tmpdir(),'Baseline-review-v4-'));
const unzip=spawnSync('C:/Users/백창현/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe',['-m','zipfile','-e',path.join(dir,'볼카운트_5편_검토본_20260927.zip'),extracted],{encoding:'utf8',windowsHide:true});
if(unzip.status!==0)throw new Error(unzip.stderr);
const browser=await chromium.launch({executablePath:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',headless:true});
const names=['index','01_ball_count','02_bcai','03_bcap','04_references_ko','05_data_validation'];
const checks=[];
try{
 for(const width of [390,1280]){
  const page=await browser.newPage({viewport:{width,height:900}});
  for(const name of names){
   await page.goto(pathToFileURL(path.join(extracted,name+'.html')).href);
   const check=await page.evaluate(()=>({width:document.documentElement.scrollWidth,viewport:innerWidth,images:[...document.images].every(x=>x.complete&&x.naturalWidth>0),nav:document.querySelectorAll('nav a').length,localPaths:[...document.querySelectorAll('a[href],img[src]')].map(x=>x.getAttribute('href')||x.getAttribute('src')).filter(x=>x.startsWith('../')||x.startsWith('file:'))}));
   checks.push({name,...check});
   if(name==='index'||name==='05_data_validation')await page.screenshot({path:path.join(dir,'../../figures/naver_20260918/qa',`portable_${name}_${width}.png`)});
  }
  // Exercise an inter-article link, a reference anchor, and a vocabulary anchor.
  await page.goto(pathToFileURL(path.join(extracted,'01_ball_count.html')).href);
  await page.locator('a[href="04_references_ko.html#ref-01"]').first().click();
  if(!page.url().endsWith('04_references_ko.html#ref-01'))throw new Error('문헌 이동 실패');
  await page.goto(pathToFileURL(path.join(extracted,'01_ball_count.html')).href);
  await page.locator('a[href="#term-01"]').first().click();
  if(!page.url().endsWith('#term-01'))throw new Error('용어 이동 실패');
  await page.locator('nav a[href="05_data_validation.html"]').click();
  if(!page.url().endsWith('05_data_validation.html'))throw new Error('다섯 번째 글 이동 실패');
  await page.close();
 }
}finally{await browser.close();}
const pass=checks.every(x=>x.width<=x.viewport&&x.images&&x.nav===5&&!x.localPaths.length);
fs.writeFileSync(path.join(dir,'portable_check_v4.json'),JSON.stringify({pass,extractedOutsideProject:true,pages:checks.length,clickedLinks:['문헌1','용어1','다섯 번째 글'],checks},null,2));
console.log(JSON.stringify({pass,pages:checks.length}));
if(!pass)process.exitCode=1;
