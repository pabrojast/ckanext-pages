// Ejecutar con: node storymap_browser.cjs /ruta/al/playwright_cli.sh
const {readFileSync} = require('node:fs');
const {execFileSync} = require('node:child_process');
const viewer = readFileSync(require('node:path').join(__dirname, '../../public/js/data-stories-storymap.js'), 'utf8');
const cli = process.argv[2] || 'playwright-cli';
function run(...args) {
  const command = cli.endsWith('.sh') ? 'bash' : cli;
  const prefix = cli.endsWith('.sh') ? [cli] : [];
  return execFileSync(command, [...prefix, '-s=storymap-state-tests', ...args], {encoding:'utf8', maxBuffer: 1024 * 1024});
}
async function check(page, source) {
  await page.setContent(`<div id="storymap"><div class="storymap-media">
    <iframe class="storymap-iframe"></iframe><div class="storymap-scene-error" hidden><button class="storymap-scene-retry">Retry</button></div></div>
    <article class="storymap-card" data-scene-index="0"><section class="storymap-step" data-scene-index="0" data-source-index="0" data-step-index="0"></section></article></div>
    <script id="storymap-config" type="application/json"></script>`);
  await page.evaluate(() => {
    const data = {version:'8',initSources:[{stories:[{shareData:{version:'8',initSources:[{camera:'A'}]}}]}]};
    document.querySelector('#storymap-config').textContent = JSON.stringify({
      embedBaseUrl:'about:blank',terriaOrigin:'https://map.test',scenes:[{sceneUrl:'about:blank',layout:'split',sources:[{sceneUrl:'about:blank',startData:data,steps:1}]}]
    });
    window.__timers = [];
    const original = window.setTimeout;
    window.setTimeout = (callback, ms) => {
      if (ms >= 1000) {window.__timers.push({callback,ms});return 10000 + window.__timers.length;}
      return original(callback,ms);
    };
    window.IntersectionObserver = class {observe() {} disconnect() {}};
    window.__messages = [];
    window.__ack = data => window.dispatchEvent(new MessageEvent('message', {
      data, origin:'https://map.test',source:document.querySelector('iframe').contentWindow
    }));
  });
  await page.evaluate(source => (0,eval)(source), source);
  await page.waitForFunction(() => document.querySelector('iframe').contentDocument?.readyState === 'complete');
  await page.evaluate(() => {
    document.querySelector('iframe').contentWindow.postMessage = data => window.__messages.push(data);
    window.__ack('ready');
  });
  await page.waitForFunction(() => window.__messages.some(m=>m.type==='applyScene'));
  const result = await page.evaluate(() => {
    const assert = (condition,message) => {if(!condition) throw new Error(message);};
    const applies = () => window.__messages.filter(m=>m.type==='applyScene');
    const id = applies().at(-1).requestId;
    const before = document.querySelector('iframe').src;
    window.__ack({type:'sceneApplied',requestId:id,phase:'received'});
    window.__timers.filter(t=>t.ms===2500).forEach(t=>t.callback());
    assert(document.querySelector('iframe').src===before,'Receipt must prevent premature hash fallback');
    window.__ack({type:'sceneApplied',requestId:id,phase:'complete',success:false});
    assert(!document.querySelector('.storymap-scene-error').hidden,'Failure must be visible');
    document.querySelector('.storymap-scene-retry').click();
    return {previous: id, count: applies().length};
  });
  await page.waitForFunction(id => window.__messages.filter(m=>m.type==='applyScene').at(-1).requestId !== id, result.previous);
  await page.evaluate(() => {
    const last = window.__messages.filter(m=>m.type==='applyScene').at(-1);
    window.__ack({type:'sceneApplied',requestId:last.requestId,phase:'complete',success:true});
    if(!document.querySelector('.storymap-scene-error').hidden) throw new Error('Successful retry must clear the error');
    if(document.querySelector('#storymap').classList.contains('is-switching')) throw new Error('Successful retry must end the transition');
  });
  return 'PASS: slow receipt, failure acknowledgement, same-scene retry, successful completion';
}
try {
  run('open', 'about:blank');
  const output = run('run-code', `async page => (${check.toString()})(page, ${JSON.stringify(viewer)})`);
  if (!output.includes('PASS:') || output.includes('### Error')) throw new Error(output);
  console.log(output.slice(0, output.indexOf('### Ran Playwright')));
} finally {run('close');}
