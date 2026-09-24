// Real-browser regression checks for authoring and the narrative/iframe contract.
const {execFileSync} = require('node:child_process');
const path = require('node:path');
const cli = process.argv[2];
const root = path.resolve(__dirname, '../..');
const read = name => path.join(root, name);
const assets = {
  editor: read('public/js/data-stories-edit.js'),
  visualsEditor: read('public/js/data-stories-visuals-edit.js'),
  sequence: read('public/js/data-stories-sequence.js'),
  visuals: read('public/js/data-stories-visuals.js'),
  viewer: read('public/js/data-stories-storymap.js'),
  css: [read('public/css/data-stories-storymap.css'), read('public/css/data-stories-visuals.css')],
  jquery: path.resolve(process.argv[3]),
  quill: read('assets/vendor/quill/quill.min.js')
};
function run(...args) {return execFileSync('bash', [cli, '-s=stories-visuals-tests', ...args], {encoding:'utf8', maxBuffer: 4*1024*1024});}
async function check(page, assets) {
  const failures = [];
  page.on('pageerror', error => failures.push(error.message));
  const view = '70441d68-3fa1-4e54-b7be-f87b6b27f515';
  const dashboard = {type:'dashboard', version:1, id:'dashboard-1', view_id:view, title:'Observations', url:'/dashboard/'+view+'/embed', state:{filters:[],widgetId:null}};
  const ref = {id:'reference-1', dashboard_id:'dashboard-1', source_id:'map-1', slide_id:'native:map-1:1', on_enter:true, state:{filters:[{field:'country',op:'eq',value:'Chile'}],widgetId:'records'}};
  await page.route('https://stories.test/**', route => {
    const url = route.request().url();
    if (url.includes('/api/3/action/')) {
      const action = url.split('?')[0].split('/').pop();
      const result = action === 'package_search' ? {results:[{id:'dataset',title:'Observations'}]} :
        action === 'package_show' ? {resources:[{id:'resource',name:'Measurements'}]} :
        [{id:view,title:'Observations dashboard',view_type:'dashboard_view'}];
      if (action === 'resource_view_list' && (route.request().method() !== 'POST' || route.request().postDataJSON().id !== 'resource'))
        return route.fulfill({status:400,body:'Use POST with resource id'});
      return route.fulfill({contentType:'application/json',body:JSON.stringify({success:true,result})});
    }
    if (url.includes('/terria/')) return route.fulfill({contentType:'text/html',body:`<script>
      window.applied=[];addEventListener('message',e=>{if(e.data.type==='applyScene'){applied.push(e.data.shareData);parent.postMessage({type:'sceneApplied',phase:'complete',requestId:e.data.requestId,success:true},location.origin)}});parent.postMessage('ready',location.origin);
      </script>`});
    if (url.includes('/dashboard/')) return route.fulfill({contentType:'text/html',body:`<html><body>Dashboard<script>
      window.received=[]; window.bootId=Math.random();
      function ready(){parent.postMessage({type:'dashboard:ready',version:1,viewId:'${view}',fields:[{key:'country',type:'text'}],widgets:[{id:'records',title:'Records'}]},location.origin)}
      addEventListener('message',e=>{if(e.data.type==='dashboard:hello')ready(); if(e.data.type==='dashboard:applyState'){received.push(e.data);parent.postMessage({type:'dashboard:stateApplied',version:1,viewId:'${view}',requestId:e.data.requestId,phase:'complete',success:true},location.origin)}});ready();
      </script></body></html>`});
    return route.fulfill({contentType:'text/html',body:'<html><body></body></html>'});
  });
  await page.goto('https://stories.test/viewer');
  await page.setViewportSize({width:1280,height:900});
  await page.setContent(`<div id="storymap" class="storymap">
    <nav class="storymap-slide-controls" hidden><button data-direction="-1">Previous</button><select></select><span role="status"></span><button data-direction="1">Next</button></nav>
    <div class="storymap-visual-status" hidden></div>
    <div class="storymap-media"><div class="storymap-map-pane"><iframe class="storymap-iframe"></iframe></div><div class="storymap-dashboard-pane" hidden></div></div>
    <div class="storymap-cards"><article class="storymap-card" data-scene-index="0"><div class="storymap-card-body"><header>Chapter</header>
    <div class="section-content storymap-narrative">Read <a href="#story-ref-reference-1">Chile</a></div>
    <div class="section-content storymap-narrative">Second paragraph</div></div></article>
    <article class="storymap-card is-full-width" data-scene-index="1" data-layout="full"><div class="storymap-card-body"><div class="section-content">Narrative only</div></div></article></div></div>
    <script id="storymap-config" type="application/json"></script>`);
  for (const css of assets.css) await page.addStyleTag({path:css});
  await page.evaluate(({dashboard,ref}) => {
    document.querySelector('#storymap-config').textContent = JSON.stringify({displayMode:'slides',embedBaseUrl:'https://stories.test/terria/',terriaOrigin:location.origin,scenes:[
      {layout:'split',presentation:'combined',sources:[{sourceId:'map-1',sceneUrl:'https://stories.test/terria/',steps:2,slideIds:['native:map-1:0','native:map-1:1'],startData:{version:'8',initSources:[{stories:[{shareData:{version:'8',initSources:[{camera:'first'}]}},{shareData:{version:'8',initSources:[{camera:'second'}]}}]}]}}],dashboards:[dashboard],references:[ref]},
      {layout:'full',sources:[],dashboards:[],references:[]} ]});
  }, {dashboard,ref});
  await page.addScriptTag({path:assets.visuals});
  await page.addScriptTag({path:assets.viewer});
  await page.waitForFunction(() => [...document.querySelectorAll('.storymap-dashboard-pane iframe')].some(f => f.contentWindow.received?.length));
  const frame = page.frames().find(f => f.url().includes('/dashboard/'));
  const boot = await frame.evaluate(() => window.bootId);
  await page.waitForFunction(() => document.querySelector('.storymap-iframe').contentWindow.applied?.some(s=>s.initSources.some(i=>i.camera==='second')));
  if (!(await page.locator('#storymap').getAttribute('class')).includes('has-combined-visuals')) throw Error('Combined template lost its visual panes');
  await page.waitForFunction(() => document.querySelector('.storymap-dashboard-pane iframe').contentWindow.received.at(-1).state.filters[0]?.value === 'Chile');
  await page.getByRole('link', {name:'Chile',exact:true}).click();
  await page.waitForFunction(() => document.querySelector('.storymap-dashboard-pane iframe').contentWindow.received.at(-1).state.filters[0]?.value === 'Chile');
  await page.getByRole('button', {name:'Next',exact:true}).click();
  await page.waitForFunction(() => document.querySelector('.storymap-dashboard-pane iframe').contentWindow.received.at(-1).state.filters.length === 0);
  if (await frame.evaluate(() => window.bootId) !== boot) throw Error('Dashboard reloaded between steps');
  await page.getByRole('button', {name:'Next',exact:true}).click();
  if (!(await page.locator('#storymap').getAttribute('class')).includes('is-full-section')) throw Error('Narrative-only slide retained media');
  await page.getByRole('button', {name:'Previous',exact:true}).click();
  await page.setViewportSize({width:390,height:844});
  await page.waitForFunction(() => document.querySelector('.has-mobile-slot'));
  const dimensions = await page.evaluate(() => ({width:document.documentElement.scrollWidth, viewport:innerWidth,
    inSlot:!!document.querySelector('.has-mobile-slot .storymap-media')}));
  if (dimensions.width > dimensions.viewport + 1 || !dimensions.inSlot) throw Error('Mobile visual layout overflow: '+JSON.stringify(dimensions));

  // Load the actual editor, serialize its blocks, then reconstruct it as after a save/reload.
  const metadata = [{type:'presentation',layout:'dashboard'},dashboard,
    {type:'text',id:'text-1',content:'<p>Read <a href="#story-ref-reference-1">Chile</a></p>',references:[ref]}];
  async function editor(blocks) {
    await page.goto('https://stories.test/editor');
    await page.setContent(`<form class="data-stories-form"><select id="display_mode"><option value="slides">Slides</option></select><div id="sections-container">
      <div class="content-section-editor" data-section-id="0"><div class="section-content-blocks" id="section-0-blocks"></div>
      <div class="add-block-controls"><div class="btn-group"></div></div><textarea class="section-content-field"></textarea>
      <input class="section-terria-link"><textarea class="section-blocks-metadata"></textarea></div></div></form>`);
    await page.locator('.section-blocks-metadata').fill(JSON.stringify(blocks));
    // CKAN defers jQuery; helpers must also survive loading before it.
    await page.addScriptTag({path:assets.visualsEditor});
    await page.addScriptTag({path:assets.jquery});
    await page.addScriptTag({path:assets.quill});
    await page.addScriptTag({path:assets.sequence});
    await page.addScriptTag({path:assets.editor});
    await page.waitForFunction(() => document.querySelector('.ql-editor') && document.querySelector('.ds-state-editor'));
    await page.locator('.ql-editor').press('End');
    await page.locator('.ql-editor').press('Space');
    await page.waitForFunction(() => JSON.parse(document.querySelector('.section-blocks-metadata').value).some(b => b.type==='text' && b.id==='text-1'));
    return JSON.parse(await page.locator('.section-blocks-metadata').inputValue());
  }
  const saved = await editor(metadata);
  const chooser = page.locator('.ds-dashboard-editor');
  await chooser.getByPlaceholder('Search datasets').fill('Observations');
  await chooser.getByRole('button',{name:'Search',exact:true}).click();
  await chooser.getByLabel('Dataset',{exact:true}).selectOption('dataset');
  await chooser.getByLabel('Resource',{exact:true}).selectOption('resource');
  await chooser.getByLabel('Dashboard',{exact:true}).selectOption(view);
  await chooser.locator('.ds-state-editor').waitFor();
  const reloaded = await editor(saved);
  if (reloaded.find(b=>b.type==='dashboard').view_id !== view || reloaded.find(b=>b.type==='text').references[0].id !== ref.id)
    throw Error('Visual metadata lost on reload');
  if (!reloaded.find(b=>b.type==='text').content.includes('#story-ref-reference-1')) throw Error('Quill removed the narrative link');
  if (failures.length) throw Error('Browser errors: '+failures.join('; '));
  return 'PASS: combined template, imported map slide and dashboard on-enter refs, slide navigation, filters and reset, iframe reuse, narrative-only slide, mobile layout, editor save/reload';
}
try {
  run('open');
  const result = run('run-code', `async page => (${check.toString()})(page, ${JSON.stringify(assets)})`);
  console.log(result.slice(0,result.indexOf('### Ran Playwright')));
  if (result.includes('### Error')) process.exitCode=1;
} catch (error) { console.error(error.stdout || error.message); process.exitCode = 1; }
finally {run('close');}
