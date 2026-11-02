const { chromium } = require('C:/Users/Rafael/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const { pathToFileURL } = require('node:url');
const path = require('node:path');
const fs = require('node:fs');
(async () => {
  const browser = await chromium.launch({executablePath:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',headless:true});
  const page = await browser.newPage({viewport:{width:1280,height:1000},deviceScaleFactor:1});
  const errors=[];
  page.on('pageerror', e=>errors.push(e.message));
  await page.goto(pathToFileURL(path.resolve('docs/gdd/index.html')).href);
  await page.evaluate(()=>Promise.all([...document.images].map(im=>im.decode())));
  await page.evaluate(()=>document.fonts.ready);
  const report=await page.evaluate(()=>({
    pages:document.querySelectorAll('.page').length,
    images:[...document.images].length,
    broken:[...document.images].filter(i=>!i.naturalWidth).length,
    overflow:[...document.querySelectorAll('.page')].flatMap((p,index)=>{
      const box=p.getBoundingClientRect();
      return [...p.querySelectorAll('.txt')].filter(t=>{
        const r=t.getBoundingClientRect();
        return r.right>box.right+1 || r.bottom>box.bottom+1 || r.left<box.left-1;
      }).map(t=>({page:index+1,text:t.textContent}));
    })
  }));
  await page.getByRole('button',{name:'Editar textos',exact:true}).click();
  report.editable=await page.locator('[contenteditable="true"]').count();
  await page.getByRole('button',{name:'Concluir edição',exact:true}).click();
  for(const n of [1,3,4,5,6,7,9,10,11,12,13,14,18,22,26,29,30,31,32,33,34]){
    await page.locator('.page').nth(n-1).screenshot({path:`docs/gdd/qa/html-${n}.png`});
  }
  report.errors=errors;
  fs.writeFileSync('docs/gdd/qa/html_check.json',JSON.stringify(report,null,2));
  console.log(JSON.stringify(report));
  await browser.close();
  if(report.pages!==34 || report.broken || report.overflow.length || errors.length || !report.editable) process.exitCode=1;
})().catch(e=>{console.error(e);process.exitCode=1});
