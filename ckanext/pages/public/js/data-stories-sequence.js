/* Datos de la secuencia editorial, compartidos por el editor y sus pruebas. */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else root.DataStorySequence = factory();
})(typeof window !== 'undefined' ? window : globalThis, function () {
  'use strict';
  function baseSnapshot(data) {
    var result = JSON.parse(JSON.stringify(data));
    (result.initSources || []).forEach(function (source) {
      if (source && typeof source === 'object') delete source.stories;
    });
    return result;
  }
  function canonical(value) {
    if (Array.isArray(value)) return '[' + value.map(canonical).join(',') + ']';
    if (value && typeof value === 'object') return '{' + Object.keys(value).sort().map(function (key) {
      return JSON.stringify(key) + ':' + canonical(value[key]);
    }).join(',') + '}';
    return JSON.stringify(value);
  }
  async function importSlides(data, sourceId) {
    if (!data || !Array.isArray(data.initSources)) throw new Error('Invalid Terria share');
    var owner = data.initSources.find(function (s) { return s && Array.isArray(s.stories) && s.stories.length; });
    var slides = owner ? owner.stories : [];
    var occurrences = {};
    var result = [];
    for (var index = 0; index < slides.length; index++) {
      var slide = slides[index];
      if (!slide || typeof slide !== 'object') continue;
      var identity = slide.id;
      if (!identity) {
        var digest = await globalThis.crypto.subtle.digest('SHA-256', new TextEncoder().encode(canonical(slide)));
        identity = Array.from(new Uint8Array(digest)).map(function (b) { return b.toString(16).padStart(2, '0'); }).join('');
      }
      identity = String(identity);
      occurrences[identity] = (occurrences[identity] || 0) + 1;
      result.push({
        type: 'terria_slide', source_id: sourceId,
        slide_id: identity + ':' + occurrences[identity],
        title: slide.title || 'Scene ' + (index + 1), content: slide.text || '',
        share_data: baseSnapshot(slide.shareData || data), orphaned: false
      });
    }
    return result;
  }
  function reconcile(blocks, sourceId, incoming) {
    var remaining = new Map(incoming.map(function (slide) { return [slide.slide_id, slide]; }));
    var result = blocks.map(function (block) {
      if (block.type !== 'terria_slide' || block.source_id !== sourceId) return block;
      var replacement = remaining.get(block.slide_id);
      remaining.delete(block.slide_id);
      return replacement || Object.assign({}, block, { orphaned: true });
    });
    var after = -1;
    result.forEach(function (block, index) {
      if (block.type === 'terria_slide' && block.source_id === sourceId) after = index;
    });
    if (after === -1) {
      var preceding = [];
      result.forEach(function (block, index) {
        if (block.type !== 'terria') return;
        var tabs = block.tabs || [];
        var tabIndex = tabs.findIndex(function (tab) { return tab.source_id === sourceId; });
        if (tabIndex !== -1) {
          after = index;
          preceding = tabs.slice(0, tabIndex).map(function (tab) { return tab.source_id; });
        }
      });
      result.forEach(function (block, index) {
        if (block.type === 'terria_slide' && preceding.includes(block.source_id)) after = Math.max(after, index);
      });
    }
    result.splice.apply(result, [after + 1, 0].concat(Array.from(remaining.values())));
    return result;
  }
  return { baseSnapshot: baseSnapshot, importSlides: importSlides, reconcile: reconcile };
});
