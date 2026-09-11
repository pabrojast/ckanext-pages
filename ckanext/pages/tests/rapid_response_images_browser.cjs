// Real Quill + browser tests through playwright-cli; uploads are simulated here.
const {execFileSync} = require('node:child_process');
const path = require('node:path');
const {mkdirSync} = require('node:fs');
const cli = process.argv[2] || 'playwright-cli';
const outputDir = path.resolve(__dirname, '../../../output/playwright');
mkdirSync(outputDir, {recursive: true});
function run(...args) {
  try {return execFileSync(cli.endsWith('.sh') ? 'bash' : cli,
    [...(cli.endsWith('.sh') ? [cli] : []), '--session', 'rr-images-tests', ...args],
    {cwd: outputDir, encoding: 'utf8', maxBuffer: 2 * 1024 * 1024});
  } catch (error) {throw new Error(error.stdout || error.stderr || 'Browser command failed');}
}
async function check(page, quillPath, imagesPath) {
  await page.setContent('<form id="rapid-response-form"><div id="editor"></div><div id="block"></div>' +
    '<textarea id="content"></textarea><input type="hidden" id="metadata"><textarea id="source"></textarea></form>');
  await page.addScriptTag({path: quillPath});
  await page.addScriptTag({path: imagesPath});
  await page.evaluate(() => {
    window.uploads = [];
    window.failUploads = false;
    window.jQuery = {ajax(options) {
      const callbacks = {};
      const result = {done(fn) {callbacks.done = fn; return result;}, fail(fn) {callbacks.fail = fn; return result;}};
      setTimeout(async () => {
        if (window.failUploads) return callbacks.fail();
        const blob = options.data.get('upload');
        const bitmap = await createImageBitmap(blob);
        const canvas = document.createElement('canvas'); canvas.width = 1; canvas.height = 1;
        const context = canvas.getContext('2d'); context.drawImage(bitmap, 0, 0);
        window.uploads.push({width: bitmap.width, height: bitmap.height, bytes: blob.size,
          mime: blob.type, alpha: context.getImageData(0, 0, 1, 1).data[3]});
        callbacks.done({uploaded: 1, url: 'https://assets.invalid/image-' + window.uploads.length + '.png'});
      }, 25);
      return result;
    }};
    window.editor = new Quill('#editor', {modules: {toolbar: [['image']]}});
    window.block = new Quill('#block', {modules: {toolbar: [['image']]}});
    const sync = () => {
      document.getElementById('content').value = window.editor.root.innerHTML;
      document.getElementById('metadata').value = JSON.stringify([{id: 'block-1', type: 'text', content: window.block.root.innerHTML}]);
    };
    window.RapidResponseImages.attach(window.editor, sync);
    window.RapidResponseImages.attach(window.block, sync);
    window.makeFile = async (color) => {
      const canvas = document.createElement('canvas'); canvas.width = 2400; canvas.height = 1800;
      const context = canvas.getContext('2d'); context.fillStyle = color; context.fillRect(0, 0, 2400, 1800);
      const blob = await new Promise(resolve => canvas.toBlob(resolve, 'image/png'));
      return new File([blob], 'paste.png', {type: 'image/png'});
    };
  });
  const result = await page.evaluate(async () => {
    const assert = (condition, reason) => {if (!condition) throw new Error(reason);};
    const manager = window.RapidResponseImages;
    const form = document.querySelector('form');
    const file = await window.makeFile('rgba(0, 110, 180, 0.25)');
    const transfer = new DataTransfer(); transfer.items.add(file);
    window.editor.root.dispatchEvent(new ClipboardEvent('paste', {clipboardData: transfer, bubbles: true, cancelable: true}));
    // Calling prepare immediately must also await FileReader and the upload.
    await manager.prepare(form);
    assert(window.uploads.length === 1, 'Paste must upload exactly once');
    assert(window.uploads[0].width === 1600 && window.uploads[0].height === 1200, 'PNG must be resized');
    assert(window.uploads[0].alpha > 0 && window.uploads[0].alpha < 255, 'Transparency must survive');
    assert(!document.getElementById('content').value.includes('data:image'), 'Hidden content must contain URLs');
    assert(document.getElementById('rr-image-status').hidden, 'Finished uploads must clear progress');
    const drag = new DragEvent('dragover', {dataTransfer: transfer, bubbles: true, cancelable: true});
    window.block.root.dispatchEvent(drag);
    assert(drag.defaultPrevented, 'Dragover must allow dropping an image');
    window.block.root.dispatchEvent(new DragEvent('drop', {dataTransfer: transfer, bubbles: true, cancelable: true}));
    await manager.prepare(form);
    assert(window.uploads.length === 1, 'Repeated image in another block must reuse its upload');
    assert(JSON.parse(document.getElementById('metadata').value)[0].content.includes('https://assets.invalid/'), 'Block JSON must be synchronized');
    window.failUploads = true;
    const second = new DataTransfer(); second.items.add(await window.makeFile('red'));
    window.editor.root.dispatchEvent(new ClipboardEvent('paste', {clipboardData: second, bubbles: true, cancelable: true}));
    let failed = false;
    try {await manager.prepare(form);} catch (_) {failed = true;}
    assert(failed, 'Save must fail if upload fails');
    assert(window.editor.root.querySelector('img[src^="data:"]'), 'Failed image must remain editable');
    window.failUploads = false;
    await manager.prepare(form);
    assert(!window.editor.root.querySelector('img[src^="data:"]'), 'Retry must replace failed data URI');
    // Source-mode fields are processed even if they have no Quill instance.
    const raw = await new Promise(resolve => {const reader = new FileReader(); reader.onload = () => resolve(reader.result); reader.readAsDataURL(file);});
    document.getElementById('source').value = '<p class="ql-align-center"><img src="' + raw + '" width="500"></p>';
    await manager.prepare(form);
    assert(!document.getElementById('source').value.includes('data:image'), 'Source mode must be converted');
    assert(document.getElementById('source').value.includes('width="500"'), 'Source dimensions must be retained');
    return 'PASS: paste, resize, transparency, pending save, drag/drop, deduplication, block metadata, upload failure, retry, source mode';
  });
  return result;
}
try {
  run('open', 'about:blank');
  const args = [path.resolve(__dirname, '../assets/vendor/quill/quill.min.js'), path.resolve(__dirname, '../public/js/rapid-response-images.js')];
  const output = run('run-code', `async page => (${check.toString()})(page, ${args.map(JSON.stringify).join(',')})`);
  if (!output.includes('PASS:') || output.includes('### Error')) throw new Error(output);
  console.log(output.slice(0, output.indexOf('### Ran Playwright')));
} finally {run('close');}
