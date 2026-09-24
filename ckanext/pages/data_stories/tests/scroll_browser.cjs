// Real scrolling, including the wide/short viewport that broke percentage margins.
const {execFileSync} = require('node:child_process');
const path = require('node:path');
const cli = process.argv[2];
const root = path.resolve(__dirname, '../../public');
const assets = {viewer: path.join(root, 'js/data-stories-storymap.js'),
  visuals: path.join(root, 'js/data-stories-visuals.js'),
  css: ['data-stories-storymap.css', 'data-stories-visuals.css'].map(p => path.join(root, 'css', p))};
function run(...args) {return execFileSync('bash', [cli, '-s=storymap-scroll-tests', ...args], {encoding:'utf8',maxBuffer:1024*1024});}
async function check(page, assets) {
  await page.route('https://stories.test/**', route => route.fulfill({contentType:'text/html',body:
    route.request().url().includes('/map') ? `<script>window.applied=[];addEventListener('message',e=>{if(e.data.type==='applyScene'){applied.push(e.data.shareData.initSources[0].camera);parent.postMessage({type:'sceneApplied',phase:'complete',success:true,requestId:e.data.requestId},location.origin)}});parent.postMessage('ready',location.origin)</script>` : '<html><body></body></html>'}));
  await page.goto('https://stories.test/reader');
  await page.setViewportSize({width:1366,height:768});
  await page.setContent(`<div style="height:300px">Article</div><div id="storymap" class="storymap">
    <div class="storymap-media"><div class="storymap-map-pane"><iframe class="storymap-iframe"></iframe>
      <div class="storymap-media-image"><img><div class="storymap-media-image-caption"></div></div></div><nav class="storymap-progress"><button class="storymap-nav-btn storymap-nav-prev">Previous</button><button class="storymap-nav-btn storymap-nav-next">Next</button></nav></div>
    <div class="storymap-cards"><article class="storymap-card" data-scene-index="0"><div class="storymap-card-body">
      <header>Imported scenes</header><div class="storymap-narrative" style="height:500px">Introduction</div>
      <div class="storymap-scene-tabs"><button class="scene-tab-btn" data-source-index="0">Map A</button><button class="scene-tab-btn" data-source-index="1">Map B</button></div>
      ${['A0','A1','B0','B1'].map((name,i)=>`<section class="storymap-step" data-scene-index="0" data-source-index="${Math.floor(i/2)}" data-step-index="${i%2}"><h3>${name}</h3><p>Scene ${name}</p></section>`).join('')}
      <figure class="storymap-image-trigger" style="height:350px" data-image-url="https://stories.test/picture" data-image-caption="An image">Image</figure>
      <div class="storymap-narrative" style="height:600px">Continue reading after the image</div></div></article>
      <article class="storymap-card is-full-width" data-scene-index="1" data-layout="full"><div class="storymap-card-body"><div class="storymap-narrative" style="height:700px">Conclusion without a map</div></div></article>
    </div></div><div style="height:800px">Footer</div><script id="storymap-config" type="application/json"></script>`);
  for(const file of assets.css)await page.addStyleTag({path:file});
  await page.evaluate(()=>{
    const sources=['A','B'].map(name=>({sceneUrl:'https://stories.test/map',sourceId:name,steps:2,
      startData:{version:'8',initSources:[{camera:name+'base',stories:[0,1].map(i=>({shareData:{version:'8',initSources:[{camera:name+i}]}}))}]}}));
    document.querySelector('#storymap-config').textContent=JSON.stringify({displayMode:'storymap',embedBaseUrl:'https://stories.test/map',terriaOrigin:location.origin,scenes:[{layout:'split',sources},{layout:'full',sources:[]}]});
  });
  await page.addScriptTag({path:assets.visuals});await page.addScriptTag({path:assets.viewer});
  await page.waitForFunction(()=>document.querySelector('iframe').contentWindow.applied?.length);
  async function focus(selector,index=0){
    await page.locator(selector).nth(index).evaluate(e=>{
      const top=innerWidth<=768?innerHeight*.42:0;
      scrollTo(0,scrollY+e.getBoundingClientRect().top-top-(innerHeight-top)*.2);
    });
  }
  async function camera(value){await page.waitForFunction(v=>document.querySelector('iframe').contentWindow.applied.at(-1)===v,value);}
  for(const [index,value] of [[1,'A1'],[3,'B1'],[2,'B0'],[0,'A0']]){
    await focus('.storymap-step',index);await camera(value);
  }
  await page.locator('.scene-tab-btn').nth(1).evaluate(e=>e.click());await camera('Bbase');
  await focus('.storymap-step',1);await camera('A1');
  await focus('.storymap-image-trigger');
  await page.waitForFunction(()=>document.querySelector('.storymap-media-image').classList.contains('is-active'));
  await focus('.storymap-narrative',1);
  await page.waitForFunction(()=>!document.querySelector('.storymap-media-image').classList.contains('is-active'));
  await focus('.storymap-card',1);
  await page.waitForFunction(()=>document.querySelector('#storymap').classList.contains('is-full-section'));
  for(const viewport of [{width:1366,height:650},{width:390,height:844},{width:844,height:390}]){
    await page.setViewportSize(viewport);await focus('.storymap-step',3);await camera('B1');
    const metrics=await page.locator('.storymap-step').nth(3).evaluate(e=>({opacity:getComputedStyle(e).opacity,width:document.documentElement.scrollWidth,viewport:innerWidth}));
    if(metrics.opacity!=='1'||metrics.width>metrics.viewport+1)throw Error(JSON.stringify(metrics));
    await focus('.storymap-step',1);await camera('A1');
    await page.locator('.storymap-nav-next').click();await camera('B0');
    await page.waitForTimeout(350);
    await page.locator('.storymap-nav-prev').click();await camera('A1');
  }
  return 'PASS: real scroll forward/reverse, multiple sources, tab resume, image/text, full chapters, 1366 and mobile portrait/landscape';
}
try {
  run('open','about:blank');const out=run('run-code',`async page => (${check.toString()})(page,${JSON.stringify(assets)})`);
  if(!out.includes('PASS:'))throw Error(out);console.log(out.slice(0,out.indexOf('### Ran Playwright')));
} finally {run('close');}
