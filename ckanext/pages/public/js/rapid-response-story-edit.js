/* A structured emergency narrative; DOM position never defines identity. */
(function () {
  'use strict';
  const labels = {text: 'Text', image: 'Image', media: 'Video / iframe', terria: 'Terria maps',
    terria_slide: 'Map scene', legacy_html: 'Existing content'};
  let story, root, field, core;
  let ready = false;
  const instances = new Map();
  const pending = new Set();
  const failedImages = new Map();
  let datasetLabels = [];
  function el(tag, text, className) {
    const node = document.createElement(tag);
    if (text !== undefined) node.textContent = text;
    if (className) node.className = className;
    return node;
  }
  function button(label, action, className) {
    const node = el('button', label, 'btn btn-sm ' + (className || 'btn-default'));
    node.type = 'button'; node.addEventListener('click', action); return node;
  }
  function message(text, error) {
    const box = document.getElementById('rr-story-status');
    box.textContent = text || ''; box.hidden = !text;
    box.className = error ? 'alert alert-danger' : 'alert alert-info';
  }
  function saveState() {
    if (!ready) return;
    story.sections.forEach((section, index) => { section.order_index = index; });
    field.value = JSON.stringify(story);
  }
  function input(container, label, object, key, type) {
    const wrapper = el('label', label, 'rr-story-input');
    const node = el(type === 'textarea' ? 'textarea' : 'input');
    if (node.tagName === 'INPUT') node.type = type || 'text';
    node.className = 'form-control'; node.value = object[key] || '';
    node.dataset.field = key;
    node.addEventListener('input', () => { object[key] = node.value; saveState(); });
    wrapper.append(node); container.append(wrapper); return node;
  }
  function track(promise) {
    pending.add(promise);
    promise.then(() => pending.delete(promise), error => {
      pending.delete(promise); message(error.message, true);
    });
    return promise;
  }
  function destroyBlock(block) {
    failedImages.delete(block.id);
    const instance = instances.get(block.id);
    if (instance) {
      window.RapidResponseImages.detach(instance.quill);
      instance.destroy(); instances.delete(block.id);
    }
  }
  function move(array, item, direction, node) {
    const index = array.indexOf(item), next = index + direction;
    if (next < 0 || next >= array.length) return;
    const sibling = direction < 0 ? node.previousElementSibling : node.nextElementSibling;
    if (!sibling) return;
    if (direction < 0) sibling.before(node); else sibling.after(node);
    array.splice(index, 1); array.splice(next, 0, item); saveState();
  }
  function controls(array, item, node, remove) {
    const box = el('div', undefined, 'rr-story-controls');
    box.append(button('Move up', () => move(array, item, -1, node)),
      button('Move down', () => move(array, item, 1, node)),
      button('Remove', () => {
        if (!window.confirm('Remove this content?')) return;
        remove(); array.splice(array.indexOf(item), 1); node.remove(); saveState();
      }, 'btn-danger'));
    return box;
  }
  function newBlock(type) {
    const block = {id: core.id(), type};
    if (type === 'text') block.content = '';
    if (type === 'image') Object.assign(block, {url: '', alt: '', caption: '', display: 'full'});
    if (type === 'media') Object.assign(block, {url: '', title: '', width: '100%', height: '600'});
    if (type === 'terria') block.tabs = [{source_id: core.id(), title: 'Map 1', url: '', width: '100%', height: '600'}];
    return block;
  }
  function sourceEditor(body, block) {
    const details = el('details');
    details.append(el('summary', 'Edit original HTML'));
    details.append(el('p', 'This content is preserved exactly. Open the source only when you need to change it.'));
    input(details, 'HTML source', block, 'content', 'textarea'); body.append(details);
    const preview = el('iframe'); preview.title = 'Existing content preview';
    preview.setAttribute('sandbox', ''); preview.className = 'rr-legacy-preview';
    preview.srcdoc = block.content || ''; body.prepend(preview);
    details.addEventListener('input', () => { preview.srcdoc = block.content || ''; });
  }
  function renderBlock(section, block, container) {
    const node = el('article', undefined, 'rr-story-block'); node.dataset.blockId = block.id;
    const heading = el('header'); heading.append(el('h4', labels[block.type] || 'Existing block'));
    heading.append(controls(section.blocks_metadata, block, node, () => {
      destroyBlock(block);
      // Removed map sources retain their imported scenes as standalone snapshots.
    })); node.append(heading);
    const body = el('div', undefined, 'rr-story-block-body'); node.append(body); container.append(node);
    if (block.type === 'text') {
      const editor = el('div'); body.append(editor);
      const options = {theme: 'snow', modules: {toolbar: [
        [{header: [2, 3, false]}], ['bold', 'italic', 'underline'],
        [{list: 'ordered'}, {list: 'bullet'}], [{align: []}], ['link', 'image'], ['clean']
      ]}};
      const instance = core.createText(editor, block.content || '', options, html => {
        block.content = html; saveState();
      });
      instances.set(block.id, instance);
      window.RapidResponseImages.attach(instance.quill, () => {
        block.content = instance.getHtml(); saveState();
      });
    } else if (block.type === 'legacy_html' || !labels[block.type]) {
      sourceEditor(body, block);
    } else if (block.type === 'image') {
      const image = el('img'); image.className = 'rr-image-preview'; image.alt = block.alt || '';
      if (block.url) image.src = block.url;
      image.hidden = !block.url; body.append(image);
      const url = input(body, 'Image URL', block, 'url');
      url.addEventListener('input', () => { image.src = url.value; image.hidden = !url.value; });
      const upload = el('input'); upload.type = 'file'; upload.accept = 'image/*';
      const label = el('label', 'Upload image', 'rr-story-input'); label.append(upload); body.append(label);
      const retry = button('Retry image upload', () => sendImage(failedImages.get(block.id)));
      retry.hidden = true; body.append(retry);
      function sendImage(file) {
        if (!file) return;
        upload.disabled = true; retry.disabled = true;
        track(window.RapidResponseImages.uploadFile(file).then(value => {
          failedImages.delete(block.id); retry.hidden = true;
          if (!story.sections.includes(section) || !section.blocks_metadata.includes(block)) return;
          block.url = value; url.value = value; image.src = value; image.hidden = false; saveState();
        }).catch(error => {
          if (story.sections.includes(section) && section.blocks_metadata.includes(block)) {
            failedImages.set(block.id, file); retry.hidden = false;
          }
          throw error;
        }).finally(() => { upload.disabled = false; retry.disabled = false; }));
      }
      upload.addEventListener('change', () => sendImage(upload.files[0]));
      input(body, 'Alternative text', block, 'alt'); input(body, 'Caption', block, 'caption');
      const display = el('label', 'Image layout', 'rr-story-input');
      const select = el('select'); select.className = 'form-control';
      [['full', 'Full width'], ['map', 'Over the map']].forEach(([value, title]) => {
        const option = el('option', title); option.value = value; select.append(option);
      });
      select.value = block.display || 'map'; select.addEventListener('change', () => { block.display = select.value; saveState(); });
      display.append(select); body.append(display);
    } else if (block.type === 'media') {
      input(body, 'Title', block, 'title'); input(body, 'Video URL or iframe code', block, 'url', 'textarea');
      input(body, 'Width', block, 'width'); input(body, 'Height', block, 'height');
    } else if (block.type === 'terria') {
      const tabs = el('div', undefined, 'rr-map-tabs'); body.append(tabs);
      const renderTab = tab => {
        const panel = el('fieldset', undefined, 'rr-map-tab'); tabs.append(panel);
        input(panel, 'Map title', tab, 'title');
        const url = input(panel, 'Terria share link', tab, 'url');
        input(panel, 'Width', tab, 'width'); input(panel, 'Height', tab, 'height');
        panel.addEventListener('input', () => { delete block.legacy_embed; saveState(); });
        url.addEventListener('input', () => { tab.sequenced = false; delete tab.snapshot; saveState(); });
        panel.append(button('Import / refresh scenes', () => {
          track(importScenes(section, block, tab));
        }, 'btn-primary'), button('Remove map', () => {
          block.tabs.splice(block.tabs.indexOf(tab), 1); delete block.legacy_embed; panel.remove(); saveState();
        }, 'btn-danger'));
      };
      block.tabs.forEach(renderTab);
      body.append(button('Add map', () => {
        const tab = {source_id: core.id(), title: 'Map ' + (block.tabs.length + 1), url: '', width: '100%', height: '600'};
        block.tabs.push(tab); delete block.legacy_embed; renderTab(tab); saveState();
      }));
    } else if (block.type === 'terria_slide') {
      input(body, 'Scene title', block, 'title'); sourceEditor(body, block);
      if (block.orphaned) body.append(el('p', 'This scene is no longer in the source map. Its saved snapshot is preserved.'));
    }
    const insert = el('div', undefined, 'rr-story-add');
    Object.entries(labels).filter(([type]) => ['text', 'image', 'media', 'terria'].includes(type)).forEach(([type, title]) => {
      insert.append(button('+ ' + title, () => {
        const added = newBlock(type);
        section.blocks_metadata.splice(section.blocks_metadata.indexOf(block) + 1, 0, added);
        const next = renderBlock(section, added, container); node.after(next); saveState();
      }));
    }); node.append(insert); return node;
  }
  async function importScenes(section, block, tab) {
    message('Loading map scenes…');
    const originalUrl = tab.url;
    const url = new URL(originalUrl, location.origin);
    const params = new URLSearchParams(url.hash.slice(1));
    let data;
    if (params.has('start')) data = JSON.parse(params.get('start'));
    else {
      const share = params.get('share');
      if (!share || !/^[A-Za-z0-9_-]+$/.test(share)) throw new Error('Paste a Terria share or start link first.');
      const base = new URL(url.pathname.replace(/\/$/, '') + '/api/v1/share/', url.origin);
      try {
        const response = await fetch(new URL(share, base));
        if (!response.ok) throw new Error('Map source not available');
        data = await response.json();
      } catch (error) {
        const configured = new URL(root.dataset.terriaBase, location.origin);
        if (configured.origin !== url.origin || configured.pathname.replace(/\/$/, '') !== url.pathname.replace(/\/$/, '')) throw error;
        const response = await fetch(root.dataset.sceneEndpoint.replace('__ID__', encodeURIComponent(share)));
        if (!response.ok) throw new Error('Could not load map scenes. Your saved scenes are preserved.');
        data = await response.json();
      }
    }
    const slides = await window.DataStorySequence.importSlides(data, tab.source_id);
    if (tab.url !== originalUrl || !story.sections.includes(section) || !section.blocks_metadata.includes(block) || !block.tabs.includes(tab)) return;
    const existing = new Map(section.blocks_metadata.filter(b => b.type === 'terria_slide').map(b => [b.source_id + ':' + b.slide_id, b.id]));
    slides.forEach(slide => { slide.id = existing.get(slide.source_id + ':' + slide.slide_id) || core.id(); });
    section.blocks_metadata = window.DataStorySequence.reconcile(section.blocks_metadata, tab.source_id, slides);
    tab.snapshot = window.DataStorySequence.baseSnapshot(data); tab.sequenced = true;
    const node = document.getElementById('rr-chapter-' + section.id);
    instances.forEach((instance, id) => {
      if (node.contains(instance.quill.root)) { window.RapidResponseImages.detach(instance.quill); instance.destroy(); instances.delete(id); }
    });
    const replacement = renderSection(section); node.replaceWith(replacement); saveState();
    message(slides.length + ' map scenes imported. You can move text and images between them.');
  }
  function renderSection(section) {
    const node = el('section', undefined, 'rr-story-chapter'); node.id = 'rr-chapter-' + section.id;
    node.dataset.sectionId = section.id;
    const header = el('header'); node.append(header);
    const title = input(header, 'Chapter title', section, 'title'); title.required = true;
    header.append(controls(story.sections, section, node, () => section.blocks_metadata.forEach(destroyBlock)));
    const blocks = el('div', undefined, 'rr-story-blocks'); node.append(blocks);
    // Quill needs connected nodes; callers append before hydrating text blocks.
    root.append(node);
    section.blocks_metadata.forEach(block => renderBlock(section, block, blocks));
    const add = el('div', undefined, 'rr-story-add'); node.append(add);
    ['text', 'image', 'media', 'terria'].forEach(type => add.append(button('+ ' + labels[type], () => {
      const block = newBlock(type); section.blocks_metadata.push(block); renderBlock(section, block, blocks); saveState();
    }, 'btn-primary')));
    return node;
  }
  function renderDatasets() {
    const list = document.getElementById('rr-story-datasets'); list.replaceChildren();
    story.datasets.forEach(reference => {
      const label = datasetLabels.find(d => d.id === reference.id);
      const row = el('li'); row.append(el('span', label ? label.title : 'Unavailable dataset'));
      row.append(button('Remove', () => {
        story.datasets.splice(story.datasets.indexOf(reference), 1); saveState(); renderDatasets();
      })); list.append(row);
    });
  }
  function bindDatasets() {
    const search = document.getElementById('rr-dataset-search');
    const results = document.getElementById('rr-dataset-results');
    let sequence = 0, timer;
    const add = dataset => {
      if (story.datasets.some(d => d.id === dataset.id)) { message('This dataset is already linked.', true); return; }
      story.datasets.push({id: dataset.id}); datasetLabels.push(dataset);
      search.value = ''; results.replaceChildren(); saveState(); renderDatasets(); message('Dataset linked.');
    };
    search.addEventListener('input', () => {
      clearTimeout(timer); const current = ++sequence; results.replaceChildren();
      if (search.value.trim().length < 2) return;
      timer = setTimeout(async () => {
        try {
          const response = await fetch('/api/3/action/package_search?' + new URLSearchParams({q: search.value.trim(), rows: '8'}));
          const data = await response.json(); if (current !== sequence) return;
          if (!response.ok || !data.success) throw new Error('Dataset search failed.');
          results.replaceChildren();
          data.result.results.forEach(dataset => results.append(button(dataset.title || dataset.name, () => add(dataset))));
        } catch (error) { if (current === sequence) message(error.message, true); }
      }, 250);
    });
    document.getElementById('rr-add-dataset').addEventListener('click', () => {
      track((async () => {
        let id = search.value.trim();
        if (!id) return;
        if (/^https?:/.test(id)) {
          const match = new URL(id).pathname.match(/\/dataset\/([^/]+)/);
          if (!match) throw new Error('Paste a dataset page URL, name or ID.');
          id = decodeURIComponent(match[1]);
        }
        const response = await fetch('/api/3/action/package_show?' + new URLSearchParams({id}));
        const data = await response.json();
        if (!response.ok || !data.success) throw new Error('Dataset not found or not accessible.');
        add(data.result);
      })());
    });
    search.addEventListener('keydown', event => {
      if (event.key === 'Enter') { event.preventDefault(); document.getElementById('rr-add-dataset').click(); }
    }); renderDatasets();
  }
  async function prepare(form) {
    if (!ready) throw new Error('The story editor could not load. Reload or restore the original document before saving.');
    while (pending.size) await Promise.all(Array.from(pending));
    if (failedImages.size) throw new Error("Retry or remove the failed image upload before saving.");
    saveState();
    await window.RapidResponseImages.prepare(form);
    // prepare may replace inline URLs in preserved HTML and JSON fields.
    const uploaded = JSON.parse(field.value);
    function updateUrls(target, source) {
      Object.keys(source).forEach(key => {
        if (typeof source[key] === 'string') target[key] = source[key];
        else if (source[key] && target[key] && typeof source[key] === 'object') updateUrls(target[key], source[key]);
      });
    }
    updateUrls(story, uploaded);
    saveState();
  }
  function initialize() {
    root = document.getElementById('rr-story-editor'); field = document.getElementById('rr-story-json');
    if (!root || !field) return;
    window.RapidResponseStory = {prepare};
    const started = Date.now();
    function load() {
      if (!window.Quill || !window.StoryEditorCore || !window.RapidResponseImages || !window.DataStorySequence) {
        if (Date.now() - started > 10000) { message('The story editor could not load. Your original content is preserved. Reload to retry.', true); return; }
        setTimeout(load, 50); return;
      }
      try {
        core = window.StoryEditorCore; story = JSON.parse(field.value);
        if (story.version !== 1 || !Array.isArray(story.sections) || !Array.isArray(story.datasets)) throw new Error('Invalid story document.');
        const ids = new Set();
        story.sections.forEach(section => {
          [section].concat(section.blocks_metadata).forEach(item => {
            if (!item.id || ids.has(item.id)) throw new Error('Duplicate or missing chapter/block ID.');
            ids.add(item.id);
          });
          renderSection(section);
        });
        datasetLabels = JSON.parse(document.getElementById('rr-dataset-labels').textContent);
        bindDatasets();
        document.getElementById('rr-add-chapter').addEventListener('click', () => {
          const section = {id: core.id(), title: 'New chapter', origin: 'additional', section_type: 'additional', blocks_metadata: []};
          story.sections.push(section); renderSection(section); saveState();
        });
        ready = true; root.dataset.ready = 'true';
      } catch (error) { message(error.message + ' Your original document is preserved; saving is disabled until this is resolved.', true); }
    }
    load();
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', initialize);
  else initialize();
})();
