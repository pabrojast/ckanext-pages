const {test} = require('node:test');
const assert = require('node:assert/strict');
const sequence = require('../../public/js/data-stories-sequence.js');
const share = stories => ({version: '8', initSources: [{stories}]});
const slide = (id, title = id) => ({id, title, text: title, shareData: {initSources: [{camera: id}]}});

test('refresh preserves CKAN inserts and reordered slides, retains removed snapshots', async () => {
  const saved = await sequence.importSlides(share([slide('a'), slide('b'), slide('c')]), 'map');
  const image = {type: 'image', url: '/photo.png', display: 'full'};
  const text = {type: 'text', content: 'Editorial'};
  const incoming = await sequence.importSlides(share([slide('a', 'Updated'), slide('b'), slide('d')]), 'map');
  const result = sequence.reconcile([saved[1], image, saved[0], text, saved[2]], 'map', incoming);
  assert.deepEqual(result.map(b => b.type), ['terria_slide', 'image', 'terria_slide', 'text', 'terria_slide', 'terria_slide']);
  assert.equal(result[0].slide_id, 'b:1');
  assert.equal(result[2].title, 'Updated');
  assert.equal(result[4].orphaned, true);
  assert.equal(result[4].share_data.initSources[0].camera, 'c');
  assert.equal(result[5].slide_id, 'd:1');
  assert.equal(result[1], image);
  assert.equal(result[3], text);
});

test('identity fallback and duplicate slides are stable without native IDs', async () => {
  const original = {title: 'No ID', text: 'Text', shareData: {initSources: []}};
  const first = await sequence.importSlides(share([original, original]), 'map');
  const second = await sequence.importSlides(share([original, original]), 'map');
  assert.deepEqual(first, second);
  assert.notEqual(first[0].slide_id, first[1].slide_id);
});

test('initial import follows its source and does not change another map', async () => {
  const source = {type: 'terria', tabs: [{source_id: 'map'}]};
  const other = {type: 'terria_slide', source_id: 'other', slide_id: 'z'};
  const incoming = await sequence.importSlides(share([slide('a')]), 'map');
  const result = sequence.reconcile([source, other], 'map', incoming);
  assert.deepEqual(result, [source, incoming[0], other]);
});

test('snapshot removes native story navigation without mutating the source', () => {
  const data = share([slide('a')]);
  assert.equal(sequence.baseSnapshot(data).initSources[0].stories, undefined);
  assert.equal(data.initSources[0].stories.length, 1);
});

test('initial import of multiple tabs follows tab order', async () => {
  let blocks = [{type:'terria',tabs:[{source_id:'first'},{source_id:'second'}]}];
  for (const id of ['first','second']) {
    blocks = sequence.reconcile(blocks,id,await sequence.importSlides(share([slide(id)]),id));
  }
  assert.deepEqual(blocks.slice(1).map(b=>b.source_id), ['first','second']);
});
