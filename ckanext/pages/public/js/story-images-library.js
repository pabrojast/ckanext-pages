(function () {
  'use strict';
  const root = document.getElementById('story-image-library');
  if (!root) return;
  const grid = document.getElementById('story-images-grid');
  const status = document.getElementById('story-images-status');
  const error = document.getElementById('story-images-error');
  const archived = document.getElementById('story-images-archived');
  const search = document.getElementById('story-images-search');
  const picker = root.dataset.picker === 'true';
  const previous = document.getElementById('story-images-previous');
  const next = document.getElementById('story-images-next');
  const modal = document.getElementById('story-image-metadata');
  let offset = 0;
  let currentImage;
  let generation = 0;
  const limit = 24;
  function showError(err) { error.textContent = err.message || String(err); }
  function node(tag, text, className) {
    const el = document.createElement(tag);
    if (text) el.textContent = text;
    if (className) el.className = className;
    return el;
  }
  function button(text, handler) {
    const el = node('button', text); el.type = 'button';
    el.onclick = async () => {
      el.disabled = true; error.textContent = '';
      try { await handler(); } catch (err) { showError(err); }
      finally { el.disabled = false; }
    };
    return el;
  }
  async function action(name, values) {
    const config = await StoryImages.settings();
    const response = await fetch('/api/3/action/' + name, {
      method: 'POST', credentials: 'same-origin',
      headers: {'Content-Type': 'application/json', 'X-CSRFToken': config.csrf_token},
      body: JSON.stringify(values)
    });
    const result = await response.json();
    if (!response.ok || !result.success) throw new Error('Could not save image details. Refresh and retry.');
    return result.result;
  }
  function renderImage(image) {
    const card = node('article', '', 'story-image-card');
    const photo = node('img'); photo.src = image.url; photo.alt = image.alt || ''; photo.loading = 'lazy';
    card.append(photo, node('h3', image.name), node('small', image.width + ' × ' + image.height + ' · ' + Math.ceil(image.size / 1024) + ' KB'));
    if (image.caption) card.append(node('p', image.caption));
    if (image.credit) card.append(node('small', image.credit));
    const actions = node('div', '', 'story-image-card-actions');
    if (picker && !image.archived) actions.append(button('Insert', () => {
      window.parent.postMessage({type: 'ckan-story-image-selected', image}, location.origin);
    }));
    actions.append(button('Copy link', async () => {
      await navigator.clipboard.writeText(image.url); status.textContent = 'Image link copied.';
    }));
    actions.append(button('Details', () => {
      currentImage = image;
      ['alt', 'caption', 'credit'].forEach(key => { modal.querySelector('[name="' + key + '"]').value = image[key] || ''; });
      modal.showModal();
    }));
    actions.append(button(image.archived ? 'Restore' : 'Archive', async () => {
      await action('story_image_update', {id: image.id, archived: !image.archived});
      await load();
    }));
    card.append(actions); return card;
  }
  async function load() {
    const requestId = ++generation;
    error.textContent = ''; status.textContent = 'Loading images…';
    const params = new URLSearchParams({owner_id: root.dataset.owner, q: search.elements.q.value,
      archived: String(archived.checked), offset: String(offset), limit: String(limit)});
    const response = await fetch('/api/3/action/story_image_list?' + params, {credentials: 'same-origin', cache: 'no-store'});
    const payload = await response.json();
    if (!response.ok || !payload.success) throw new Error('Sign in to view your image library.');
    if (requestId !== generation) return;
    const result = payload.result;
    if (!result.items.length && offset > 0) { offset = Math.max(0, offset - limit); return load(); }
    grid.replaceChildren(...result.items.map(renderImage));
    status.textContent = result.count ? '' : 'No images yet. Upload an image to get started.';
    document.getElementById('story-images-count').textContent = result.count ?
      (offset + 1) + '–' + (offset + result.items.length) + ' / ' + result.count : '0';
    previous.disabled = offset === 0; next.disabled = offset + limit >= result.count;
  }
  search.onsubmit = event => { event.preventDefault(); offset = 0; load().catch(showError); };
  archived.onchange = () => { offset = 0; load().catch(showError); };
  previous.onclick = () => { offset = Math.max(0, offset - limit); load().catch(showError); };
  next.onclick = () => { offset += limit; load().catch(showError); };
  document.getElementById('story-images-upload').onchange = async event => {
    const input = event.target; input.disabled = true; error.textContent = '';
    try {
      for (const file of input.files) {
        await StoryImages.upload(file, percent => { status.textContent = file.name + ': ' + percent + '%'; });
      }
      input.value = ''; offset = 0; archived.checked = false; await load();
    } catch (err) { showError(err); status.textContent = 'Select the file again to retry.'; }
    finally { input.disabled = false; }
  };
  document.getElementById('story-image-metadata-cancel').onclick = () => modal.close();
  modal.querySelector('form').onsubmit = async event => {
    event.preventDefault();
    const form = event.target;
    const save = form.querySelector('[type=submit]'); save.disabled = true;
    try {
      await action('story_image_update', {id: currentImage.id, alt: form.elements.alt.value,
        caption: form.elements.caption.value, credit: form.elements.credit.value});
      modal.close(); await load();
    } catch (err) { modal.close(); showError(err); }
    finally { save.disabled = false; }
  };
  load().catch(showError);
})();
