// Local Chromium integration: real picker/template/editor, controlled CKAN API responses.
const {execFileSync} = require('node:child_process');
const path = require('node:path');
const fs = require('node:fs');
const cli = process.argv[2];
const root = path.resolve(__dirname, '../..');
const output = path.resolve(process.argv[4] || 'output/dashboard-picker-local');
fs.mkdirSync(output, {recursive:true});
const templates = path.join(root, 'theme/templates_main');
const assets = {editor:path.join(root,'public/js/data-stories-visuals-edit.js'),
  picker:path.join(root,'public/js/story-dashboard-picker.js'), css:path.join(root,'public/css/data-stories-visuals.css'),
  jquery:path.resolve(process.argv[3]), output, html:{}};
for (const language of ['en','es']) assets.html[language] = execFileSync('python3', ['-c', `
from jinja2 import Environment, ChoiceLoader, DictLoader, FileSystemLoader
import sys
base = '<!doctype html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><style>body{font:14px/1.5 Arial;margin:0;color:#183e58}button,input,select{font:inherit}.btn{padding:8px 12px;border:1px solid #a7bccb;border-radius:6px;background:white}.btn-primary{background:#006da8;color:white}.btn:disabled{opacity:.5}</style><script src="/jquery.js"></script></head><body>{% block primary %}{% endblock %}</body></html>'
env=Environment(loader=ChoiceLoader([DictLoader({'page.html':base}),FileSystemLoader(sys.argv[1])]),autoescape=True)
print(env.get_template('story_dashboards/picker.html').render(picker_language=sys.argv[2],picker_csrf='local-csrf'))
`, templates, language], {encoding:'utf8'});

function run(...args) {return execFileSync('bash',[cli,'--session','dashboard-picker-local',...args],{cwd:output,encoding:'utf8',maxBuffer:4*1024*1024});}
async function check(page, assets) {
  const errors=[]; page.on('pageerror', e=>errors.push(e.message));
  const deferred=[];
  const metadata = view => ({type:'dashboard:ready',version:1,viewId:view,
    fields:[{key:'country',type:'text'},{key:'value',type:'number'},{key:'date',type:'date'},{key:'valid',type:'boolean'}],
    widgets:[{id:'records',title:'Records'},{id:'trend',title:'Trend'}]});
  await page.route('https://picker.test/**', async route => {
    const url = new URL(route.request().url());
    if (url.pathname === '/jquery.js') return route.fulfill({path:assets.jquery,contentType:'application/javascript'});
    if (url.pathname.includes('/js/data-stories-visuals-edit.js')) return route.fulfill({path:assets.editor,contentType:'application/javascript'});
    if (url.pathname.includes('/js/story-dashboard-picker.js')) return route.fulfill({path:assets.picker,contentType:'application/javascript'});
    if (url.pathname.includes('/css/data-stories-visuals.css')) return route.fulfill({path:assets.css,contentType:'text/css'});
    if (url.pathname.includes('/api/3/action/')) {
      const action=url.pathname.split('/').pop(), id=url.searchParams.get('id') || route.request().postDataJSON()?.id;
      const q=url.searchParams.get('q');
      const response = result => route.fulfill({contentType:'application/json',body:JSON.stringify({success:true,result})});
      if (q==='slow' || q==='late-error' || id==='slow-dataset' || id==='slow-resource')
        await new Promise(resolve=>deferred.push({q,id,resolve}));
      if (q==='late-error' || q==='failure') return route.fulfill({status:500,body:'Unavailable'});
      if (id==='denied') return route.fulfill({status:403,body:'Forbidden'});
      if (action==='package_search') return response({results:q==='empty'?[]:[{id:q==='slow'?'obsolete':'dataset',title:'Observations'},{id:'second',title:'Second'},{id:'slow-dataset',title:'Slow dataset'}]});
      if (action==='package_show') return response({resources:[{id:id==='slow-dataset'?'obsolete-resource':'resource',name:'Measurements'},{id:'empty',name:'No dashboards'},{id:'denied',name:'Restricted'},{id:'slow-resource',name:'Slow resource'}]});
      if (action==='resource_view_list') {
        if (route.request().method()!=='POST') throw Error('resource_view_list must use POST');
        return response(id==='empty'?[]:[{id:id==='slow-resource'?'obsolete-view':'view-a',title:'Observations dashboard',view_type:'dashboard_view'},{id:'view-b',title:'Other dashboard',view_type:'dashboard_view'},{id:'view-wait',title:'Delayed dashboard',view_type:'dashboard_view'}]);
      }
    }
    if (url.pathname.startsWith('/dashboard/')) {
      const view=url.pathname.split('/')[2], ready=JSON.stringify(metadata(view));
      return route.fulfill({contentType:'text/html',body:`<html><body>Original dashboard<script>
        const data=${ready}; window.sendReady=()=>parent.postMessage(data,location.origin);
        addEventListener('message',e=>{if(e.data.type==='dashboard:hello'&&data.viewId!=='view-wait')sendReady()});
        </script></body></html>`});
    }
    if (url.pathname==='/story-dashboards/picker') return route.fulfill({contentType:'text/html',body:assets.html[url.searchParams.get('lang')==='es'?'es':'en']});
    return route.fulfill({contentType:'text/html',body:`<html><body><script>window.selections=[];addEventListener('message',e=>{if(e.data.type==='ckan-story-dashboard-selected')selections.push(e.data)})</script><iframe title="Picker" style="border:0;width:100%;height:95vh" src="/story-dashboards/picker?lang=${url.searchParams.get('lang')||'en'}"></iframe></body></html>`});
  });
  async function start(lang='en') {
    await page.goto('https://picker.test/host?lang='+lang);
    const f=page.frameLocator('iframe[title="Picker"]');
    await f.locator('.ds-dashboard-step').last().waitFor();return f;
  }
  let f=await start();
  const insert=()=>f.locator('#story-dashboard-insert');
  const assert= (condition,message)=>{if(!condition)throw Error(message);};
  async function search(q) {await f.locator('.ds-dashboard-editor input').first().fill(q);await f.getByRole('button',{name:'Search',exact:true}).click();}
  async function choose(view='view-a') {
    await search('Observations');await f.getByLabel('Dataset',{exact:true}).selectOption('dataset');
    await f.getByLabel('File (resource)',{exact:true}).selectOption('resource');
    await f.getByLabel('Dashboard',{exact:true}).selectOption(view);
    if(view!=='view-wait')await f.locator('.ds-state-editor').waitFor();
  }
  assert(await insert().isDisabled(),'Empty picker enabled insertion');
  assert(await f.locator('.ds-dashboard-step').count()===3,'Guide lost a step');
  await choose(); assert(await insert().isEnabled(),'No filters should be valid');
  await f.getByRole('button',{name:'Add filter',exact:true}).click();
  assert(await insert().isDisabled(),'Adding an incomplete filter must immediately disable insertion');
  const row=f.locator('.ds-filter-row');
  await row.getByLabel('Field',{exact:true}).selectOption('value');
  await row.getByLabel('Value',{exact:true}).fill('not-a-number');
  assert(await insert().isDisabled(),'Invalid number enabled insertion');
  await row.getByLabel('Value',{exact:true}).fill('20'); assert(await insert().isEnabled(),'Valid number rejected');
  assert((await row.getByLabel('Value',{exact:true}).getAttribute('placeholder')).includes('20'),'Numeric example absent');
  await row.getByLabel('Condition',{exact:true}).selectOption('between');
  await row.getByLabel('Value',{exact:true}).fill('20, 10'); assert(await insert().isDisabled(),'Reversed interval accepted');
  await row.getByLabel('Value',{exact:true}).fill('10, 20'); assert(await insert().isEnabled(),'Valid interval rejected');
  await row.getByLabel('Field',{exact:true}).selectOption('date');
  await row.getByLabel('Condition',{exact:true}).selectOption('eq');
  for(const value of ['2026-02-30','2026-10-12T24:00:00','0000-10-12']) {
    await row.getByLabel('Value',{exact:true}).fill(value);assert(await insert().isDisabled(),'Invalid ISO date accepted: '+value);
  }
  await row.getByLabel('Value',{exact:true}).fill('2026-10-12');assert(await insert().isEnabled(),'Valid date rejected');
  await row.getByLabel('Field',{exact:true}).selectOption('valid');
  await row.getByLabel('Value',{exact:true}).fill('yes');assert(await insert().isDisabled(),'Invalid boolean accepted');
  await row.getByLabel('Value',{exact:true}).fill('false');assert(await insert().isEnabled(),'False boolean rejected');
  await row.getByLabel('Field',{exact:true}).selectOption('country');await row.getByLabel('Value',{exact:true}).fill('Chile');
  await row.getByLabel('Condition',{exact:true}).selectOption('in');
  await row.getByLabel('Value',{exact:true}).fill(Array(101).fill('Chile').join(','));assert(await insert().isDisabled(),'101 values accepted');
  await row.getByLabel('Condition',{exact:true}).selectOption('eq');await row.getByLabel('Value',{exact:true}).fill('Chile');
  await insert().click();
  await page.waitForFunction(()=>selections.length>0);
  const sent=await page.evaluate(()=>selections.at(-1));
  assert(sent.type==='ckan-story-dashboard-selected'&&sent.version===1&&sent.dashboard.state.filters[0].value==='Chile','Selection contract or filter lost');
  await f.getByLabel('Dashboard',{exact:true}).selectOption('view-wait');
  assert(await insert().isDisabled(),'New view inherited old metadata');
  let picker=page.frames().find(frame=>frame.url().includes('/story-dashboards/picker'));
  await picker.evaluate(data=>{
    const iframe=document.querySelector('.ds-dashboard-preview');window.oldDashboard=iframe.contentWindow;
    window.dispatchEvent(new MessageEvent('message',{origin:'https://other.test',source:iframe.contentWindow,data}));
  },metadata('view-wait'));
  assert(await insert().isDisabled(),'Wrong origin accepted');
  await f.getByLabel('Dashboard',{exact:true}).selectOption('view-a');await f.locator('.ds-state-editor').waitFor();
  await f.getByLabel('Dashboard',{exact:true}).selectOption('view-wait');
  await picker.evaluate(data=>window.dispatchEvent(new MessageEvent('message',{origin:location.origin,source:oldDashboard,data})),metadata('view-wait'));
  assert(await insert().isDisabled(),'Old frame for the same view ID accepted');
  await page.frames().find(frame=>frame.url().includes('/dashboard/view-wait/')).evaluate(()=>sendReady());
  await f.locator('.ds-state-editor').waitFor();assert(await insert().isEnabled(),'Current frame ready rejected');
  await f.getByRole('button',{name:'Add filter',exact:true}).click();
  await page.frames().find(frame=>frame.url().includes('/dashboard/view-wait/')).evaluate(()=>sendReady());
  assert(await f.locator('.ds-filter-row').count()===1&&await insert().isDisabled(),'Duplicate ready erased pending filter');
  await f.getByLabel('Dataset',{exact:true}).selectOption('second');
  assert(await insert().isDisabled()&&await f.locator('.ds-state-editor').count()===0,'Dataset change kept metadata');
  await f.getByLabel('File (resource)',{exact:true}).selectOption('empty');await f.getByText('This file has no saved dashboards.',{exact:false}).waitFor();
  await f.getByLabel('File (resource)',{exact:true}).selectOption('denied');await f.getByText('You do not have access to this selection.',{exact:false}).waitFor();
  await f.getByLabel('Dataset',{exact:true}).selectOption('slow-dataset');
  await f.getByLabel('Dataset',{exact:true}).selectOption('dataset');
  await f.getByLabel('File (resource)',{exact:true}).selectOption('slow-resource');
  await f.getByLabel('File (resource)',{exact:true}).selectOption('empty');
  await f.getByText('This file has no saved dashboards.',{exact:false}).waitFor();
  deferred.find(x=>x.id==='slow-dataset').resolve();deferred.find(x=>x.id==='slow-resource').resolve();
  await picker.evaluate(()=>new Promise(resolve=>setTimeout(resolve,100)));
  assert(await f.locator('option[value="obsolete-resource"], option[value="obsolete-view"]').count()===0&&await insert().isDisabled(),'Stale dataset/resource response revived selection');
  await search('slow');await search('fast');
  deferred.find(x=>x.q==='slow').resolve();
  await f.getByLabel('Dataset',{exact:true}).selectOption('dataset');
  assert(await f.locator('option[value="obsolete"]').count()===0,'Stale search replaced current results');
  await search('late-error');await search('empty');
  await f.getByText('No matching datasets.',{exact:false}).waitFor();deferred.find(x=>x.q==='late-error').resolve();
  await picker.evaluate(()=>new Promise(resolve=>setTimeout(resolve,100)));
  assert((await f.locator('.ds-dashboard-status').innerText()).includes('No matching datasets'),'Late failure replaced current message');
  // Existing Data Stories / Rapid Response state must survive unavailable metadata and searches.
  const saved={type:'dashboard',version:1,id:'saved',view_id:'view-wait',title:'Saved chart',state:{filters:[{field:'country',op:'eq',value:'Chile'}],widgetId:'trend'}};
  await picker.evaluate(saved=>{document.querySelector('#story-dashboard-picker-editor').replaceChildren();window.savedBox=StoryVisualsEditor.dashboard(saved,()=>{});document.querySelector('#story-dashboard-picker-editor').append(savedBox[0]);},saved);
  for(const q of ['empty','failure']) {
    await search(q);await picker.evaluate(()=>new Promise(resolve=>setTimeout(resolve,100)));
    const result=await picker.evaluate(()=>({read:savedBox.data('read')(),ready:savedBox.data('can-insert')()}));
    assert(result.read.view_id===saved.view_id && JSON.stringify(result.read.state)===JSON.stringify(saved.state) && !result.ready,'Search destroyed an existing dashboard');
  }
  for(const filter of [{field:'country',op:'eq',value:''},{field:'country',op:'in',value:['','Chile']}]) {
    const preserved={...saved,view_id:'view-a',state:{filters:[filter],widgetId:'trend'}};
    await picker.evaluate(saved=>{document.querySelector('#story-dashboard-picker-editor').replaceChildren();window.savedBox=StoryVisualsEditor.dashboard(saved,()=>{});document.querySelector('#story-dashboard-picker-editor').append(savedBox[0]);},preserved);
    await f.locator('.ds-state-editor').waitFor();
    const result=await picker.evaluate(()=>({read:savedBox.data('read')(),ready:savedBox.data('can-insert')()}));
    assert(JSON.stringify(result.read.state.filters[0])===JSON.stringify(filter)&&!result.ready,'Existing empty text filter lost after metadata ready');
  }
  f=await start('es');
  await f.getByRole('heading',{name:'Añadir un dashboard de IHP-WINS',exact:true}).waitFor();
  await f.getByLabel('Buscar conjunto de datos',{exact:true}).fill('Observations');await f.getByRole('button',{name:'Buscar',exact:true}).click();
  await f.getByLabel('Conjunto de datos',{exact:true}).selectOption('dataset');
  await f.getByLabel('Archivo (recurso)',{exact:true}).selectOption('resource');await f.getByLabel('Dashboard',{exact:true}).selectOption('view-a');
  await f.locator('.ds-state-editor').waitFor();
  assert(await f.getByRole('button',{name:'Añadir dashboard al capítulo',exact:true}).isEnabled(),'Spanish picker not ready');
  assert(await f.getByRole('heading',{name:'Vista previa del dashboard original',exact:true}).count()===1,'Preview language leaked from host FR');
  await f.locator('summary').click();
  const resource=f.getByRole('link',{name:'Abrir el archivo seleccionado',exact:true});
  assert((await resource.getAttribute('href'))==='/dataset/dataset/resource/resource','Resource link not safely constructed');
  for(const [width,height] of [[1280,800],[390,844]]) {
    await page.setViewportSize({width,height});
    const frame=page.frames().find(frame=>frame.url().includes('/story-dashboards/picker'));
    const dimensions=await frame.evaluate(()=>({actual:document.documentElement.scrollWidth,viewport:innerWidth}));
    assert(dimensions.actual<=dimensions.viewport,'Picker overflow: '+JSON.stringify(dimensions));
    await frame.evaluate(()=>scrollTo(0,0));
    await page.screenshot({path:assets.output+'/picker-es-'+width+'.png',fullPage:true});
    await f.getByRole('button',{name:'Añadir dashboard al capítulo',exact:true}).scrollIntoViewIfNeeded();
    await page.screenshot({path:assets.output+'/picker-es-'+width+'-insert.png',fullPage:true});
  }
  assert(errors.length===0,'Browser errors: '+errors.join('; '));
  return 'PASS: EN/ES, optional valid/invalid typed filters and limits, actual selection message, stale dataset/resource/search responses and iframe metadata, duplicate ready, saved editor state including empty text, resource help, 1280/390 responsive layout';
}
try {run('open');const result=run('run-code',`async page => (${check.toString()})(page,${JSON.stringify(assets)})`);console.log(result.slice(0,result.indexOf('### Ran Playwright')));if(result.includes('### Error'))process.exitCode=1;}
catch(error){console.error(error.stdout||error.message);process.exitCode=1;}
finally{run('close');}
