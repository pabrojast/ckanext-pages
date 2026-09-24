// Real Quill and browser DOM; CKAN package actions, uploads and Terria are fixtures.
const {execFileSync} = require('node:child_process');
const {mkdirSync, writeFileSync} = require('node:fs');
const path = require('node:path');
const cli = process.argv[2] || 'playwright-cli';
const outputDir = path.resolve(__dirname, '../../../output/playwright');
mkdirSync(outputDir, {recursive: true});
function run(...args) {
  try { return execFileSync(cli.endsWith('.sh') ? 'bash' : cli,
    [...(cli.endsWith('.sh') ? [cli] : []), '--session', 'rr-story-tests', ...args],
    {cwd: outputDir, encoding: 'utf8', maxBuffer: 3 * 1024 * 1024});
  } catch (error) { throw new Error(error.stdout || error.stderr || error.message); }
}
async function check(page, rootPath) {
  page.on('dialog', dialog => dialog.accept());
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.route('https://rr.test/**', route => route.fulfill({contentType: 'text/html', body: '<html><body></body></html>'}));
  await page.goto('https://rr.test/editor');
  await page.setContent(`<form id="rapid-response-form">
    <div id="rr-story-status" hidden></div><textarea id="rr-story-json" name="rapid_response_story" hidden></textarea>
    <div id="rr-story-editor" data-scene-endpoint="/rapid-response/api/terria-scene/__ID__" data-terria-base="https://rr.test/terria"></div>
    <button type="button" id="rr-add-chapter">Add chapter</button>
    <input id="rr-dataset-search"><button type="button" id="rr-add-dataset">Add dataset</button>
    <div id="rr-dataset-results"></div><ul id="rr-story-datasets"></ul>
    <script type="application/json" id="rr-dataset-labels">[]</script>
  </form>`);
  await page.addStyleTag({path: rootPath + '/assets/vendor/quill/quill.snow.css'});
  await page.addStyleTag({path: rootPath + '/public/css/rapid-response-story.css'});
  await page.evaluate(() => {
    window.originalStory = {version: 1, sections: [
      {id: 'chapter-1', origin: 'overview', title: 'Context', order_index: 0, blocks_metadata: [
        {id: 'block-1', type: 'text', content: '<p class="ql-align-center">First &amp; original</p>'},
        {id: 'block-3', type: 'text', content: '<p>Third</p>'},
        {id: 'legacy', type: 'legacy_html', content: '<div style="height:777px"><iframe src="https://rr.test/map" allow="geolocation; fullscreen"></iframe></div>'}
      ]},
      {id: 'chapter-2', origin: 'impact', title: 'Impact', order_index: 1, blocks_metadata: [
        {id: 'maps', type: 'terria', tabs: [{source_id: 'source-1', title: 'Flood', url: 'https://rr.test/terria/#share=g-test', width: '100%', height: '700'}]}
      ]}
    ], datasets: []};
    document.getElementById('rr-story-json').value = JSON.stringify(window.originalStory);
    window.confirm = () => true;
    window.failUploads = false;
    window.jQuery = {ajax(options) {
      const callbacks = {};
      const result = {done(fn) {callbacks.done = fn; return result;}, fail(fn) {callbacks.fail = fn; return result;}};
      setTimeout(() => {
        if (window.failUploads) callbacks.fail();
        else callbacks.done({uploaded: 1, url: 'https://rr.test/uploads/image.png'});
      }, 50);
      return result;
    }};
    window.fetch = async url => {
      if (String(url).includes('package_show')) return {ok: true, json: async () => ({success: true, result: {id: 'dataset-id', name: 'floods', title: 'Flood observations'}})};
      if (String(url).includes('package_search')) return {ok: true, json: async () => ({success: true, result: {results: [{id: 'dataset-id', name: 'floods', title: 'Flood observations'}]}})};
      return {ok: true, json: async () => ({version: '8', initSources: [{stories: [
        {id: 'one', title: 'Scene one', text: '<p>Flood extent</p>', shareData: {version: '8', initSources: []}},
        {id: 'two', title: 'Scene two', text: '<p>Response</p>', shareData: {version: '8', initSources: []}}
      ]}]})};
    };
  });
  for (const file of ['assets/vendor/quill/quill.min.js', 'public/js/story-editor-core.js',
    'public/js/data-stories-sequence.js', 'public/js/rapid-response-images.js', 'public/js/rapid-response-story-edit.js']) {
    await page.addScriptTag({path: rootPath + '/' + file});
  }
  await page.waitForFunction(() => document.getElementById('rr-story-editor').dataset.ready === 'true');
  const result = await page.evaluate(async () => {
    const assert = (condition, message) => { if (!condition) throw new Error(message); };
    const form = document.querySelector('form');
    const documentValue = () => JSON.parse(document.getElementById('rr-story-json').value);
    const click = (node, label) => Array.from(node.querySelectorAll('button')).find(b => b.textContent === label).click();
    const wait = () => new Promise(resolve => setTimeout(resolve, 150));
    await window.RapidResponseStory.prepare(form);
    assert(JSON.stringify(documentValue()) === JSON.stringify(window.originalStory), 'No-op save must preserve the document');
    const chapter = document.getElementById('rr-chapter-chapter-1');
    click(chapter.querySelector('[data-block-id="block-1"]'), '+ Text');
    let ids = documentValue().sections[0].blocks_metadata.map(b => b.id);
    assert(new Set(ids).size === ids.length && ids.includes('block-3'), 'Adding after re-edit must not collide with a gap in IDs');
    const added = chapter.querySelectorAll('.rr-story-block')[1];
    const editor = Quill.find(added.querySelector('.ql-container'));
    editor.setText('New content after reopening', 'user');
    click(added.querySelector('header'), 'Move down');
    assert(documentValue().sections[0].blocks_metadata[2].content.includes('New content'), 'Reorder must keep editor identity');
    click(chapter.querySelector('header'), 'Move down');
    editor.insertText(0, 'Still the same block. ', 'user');
    assert(documentValue().sections[1].blocks_metadata[2].content.includes('Still the same'), 'Editing after moving a chapter must affect its own block');
    const legacy = documentValue().sections[1].blocks_metadata.find(b => b.id === 'legacy');
    assert(legacy.content === window.originalStory.sections[0].blocks_metadata[2].content, 'Legacy HTML and iframe dimensions must survive');
    click(added.querySelector('header'), 'Remove');
    assert(!documentValue().sections[1].blocks_metadata.some(b => b.id === ids[1]), 'Deleted editor must not be serialized again');
    const impact = document.getElementById('rr-chapter-chapter-2');
    click(impact, 'Import / refresh scenes'); await wait();
    await window.RapidResponseStory.prepare(form);
    let slides = documentValue().sections[0].blocks_metadata.filter(b => b.type === 'terria_slide');
    assert(slides.length === 2 && slides[0].share_data, 'Terria scenes must keep snapshots: ' + document.getElementById('rr-story-status').textContent);
    const slideIds = slides.map(b => b.id);
    click(document.getElementById('rr-chapter-chapter-2'), 'Import / refresh scenes'); await wait();
    await window.RapidResponseStory.prepare(form);
    slides = documentValue().sections[0].blocks_metadata.filter(b => b.type === 'terria_slide');
    assert(JSON.stringify(slides.map(b => b.id)) === JSON.stringify(slideIds), 'Refreshing scenes preserves identity');
    document.getElementById('rr-dataset-search').value = 'https://rr.test/dataset/floods';
    document.getElementById('rr-add-dataset').click(); await wait();
    document.getElementById('rr-dataset-search').value = 'floods';
    document.getElementById('rr-add-dataset').click(); await wait();
    assert(documentValue().datasets.length === 1, 'Dataset aliases must deduplicate by canonical ID');
    click(document.getElementById('rr-story-datasets'), 'Remove');
    assert(documentValue().datasets.length === 0, 'Removing all datasets must persist []');
    click(document.getElementById('rr-chapter-chapter-1'), '+ Image');
    const upload = document.querySelector('input[type="file"]');
    const canvas = document.createElement('canvas'); canvas.width = 32; canvas.height = 32;
    const blob = await new Promise(resolve => canvas.toBlob(resolve, 'image/png'));
    const transfer = new DataTransfer(); transfer.items.add(new File([blob], 'test.png', {type: 'image/png'}));
    upload.files = transfer.files; window.failUploads = true; upload.dispatchEvent(new Event('change'));
    await wait();
    let rejected = false;
    try { await window.RapidResponseStory.prepare(form); } catch (_) { rejected = true; }
    assert(rejected, 'Failed image upload must block saving without discarding the file');
    window.failUploads = false; click(upload.closest('.rr-story-block'), 'Retry image upload');
    await window.RapidResponseStory.prepare(form);
    assert(documentValue().sections[1].blocks_metadata.some(b => b.type === 'image' && b.url.endsWith('/image.png')), 'Retry must save the uploaded URL');
    return 'PASS: no-op preservation, gap IDs, block/chapter reorder, deletion, legacy HTML, Terria import/refresh, datasets, pending upload, failure/retry';
  });
  for (const width of [320, 390, 768, 1366, 1920]) {
    await page.setViewportSize({width, height: 900});
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth > innerWidth);
    if (overflow) throw new Error('Editor has horizontal overflow at ' + width + 'px');
  }
  if (errors.length) throw new Error(errors.join('\n'));
  return result;
}
try {
  run('open', 'about:blank');
  const rootPath = path.resolve(__dirname, '..');
  const output = run('run-code', `async page => { return await (${check.toString()})(page, ${JSON.stringify(rootPath)}); }`);
  writeFileSync(path.join(outputDir, 'rr-story-browser.txt'), output);
  if (!/### Result\s+[\s\S]*PASS:/.test(output) || output.includes('### Error')) throw new Error(output.slice(0, 1500));
  console.log(output.slice(0, output.indexOf('### Ran Playwright')));
} finally { run('close'); }
