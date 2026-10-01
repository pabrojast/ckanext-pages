/* Shared CKAN story uploads and image library picker. */
(function (root) {
  'use strict';
  const pending = new Set();
  const dataUploads = new Map();
  const endpoint = '/story-images/upload';

  async function settings() {
    const response = await fetch(endpoint, {credentials: 'same-origin', cache: 'no-store'});
    if (!response.ok) throw new Error('Sign in to IHP to upload images. Your draft has been kept.');
    return response.json();
  }

  function track(promise) {
    pending.add(promise);
    promise.then(() => pending.delete(promise), () => pending.delete(promise));
    return promise;
  }

  function upload(file, progress) {
    return track(settings().then(config => {
      if (file.size > config.max_bytes) throw new Error('Image exceeds the portal upload limit.');
      return new Promise((resolve, reject) => {
        const xhr = new XMLHttpRequest();
        xhr.open('POST', endpoint);
        xhr.timeout = 120000;
        xhr.setRequestHeader('X-CSRFToken', config.csrf_token);
        xhr.upload.onprogress = event => {
          if (progress && event.lengthComputable) progress(Math.round(event.loaded / event.total * 100));
        };
        xhr.onerror = xhr.ontimeout = () => reject(new Error('Upload interrupted. Your draft has been kept; please retry.'));
        xhr.onload = () => {
          try {
            const result = JSON.parse(xhr.responseText);
            if (xhr.status >= 400 || result.uploaded !== 1 || !result.url) {
              throw new Error(result.error?.message || 'Upload failed. Please sign in and retry.');
            }
            resolve(result);
          } catch (error) { reject(error); }
        };
        const form = new FormData();
        form.append('upload', file, file.name || 'story-image');
        form.append('_csrf_token', config.csrf_token);
        xhr.send(form);
      });
    }));
  }

  async function wait() {
    while (pending.size) await Promise.all(Array.from(pending));
  }

  function dataImage(uri) {
    if (!/^data:image\/(png|jpeg|gif|webp);base64,/i.test(uri)) {
      return Promise.reject(new Error('Unsupported inline image. Choose JPEG, PNG, WebP or GIF.'));
    }
    if (dataUploads.has(uri)) return dataUploads.get(uri);
    const promise = fetch(uri).then(response => response.blob()).then(blob => upload(blob));
    dataUploads.set(uri, promise);
    promise.catch(() => dataUploads.delete(uri));
    return promise;
  }

  async function normalizeQuill(quill) {
    const sources = new Set(quill.getContents().ops.map(op => op.insert?.image).filter(src => /^data:/i.test(src || '')));
    for (const source of sources) {
      const image = await dataImage(source);
      // Construct a change against the CURRENT document, so typing during an upload is retained.
      const Delta = root.Quill.import('delta');
      let change = new Delta();
      quill.getContents().ops.forEach(op => {
        if (op.insert?.image === source) {
          change = change.delete(1).insert({image: image.url}, op.attributes);
        } else {
          change = change.retain(typeof op.insert === 'string' ? op.insert.length : 1);
        }
      });
      quill.updateContents(change, 'user');
    }
  }

  async function normalizeForm(form) {
    // Covers legacy gallery/block JSON and nested Terria story text as well as HTML.
    for (const field of Array.from(form.elements)) {
      if (!field.name || field.type === 'file' || typeof field.value !== 'string') continue;
      const sources = new Set(field.value.match(/data:image\/[a-z0-9.+-]+;base64,[a-z0-9+/=\r\n]+/gi) || []);
      for (const source of sources) {
        const image = await dataImage(source);
        field.value = field.value.split(source).join(image.url);
      }
      if (/(data\s*:\s*image\/|blob\s*:)/i.test(field.value)) {
        throw new Error('Some images are still pending. Retry before saving.');
      }
    }
  }

  function choose() {
    return new Promise(resolve => {
      const dialog = document.createElement('dialog');
      dialog.className = 'story-image-dialog';
      dialog.setAttribute('aria-label', 'My images');
      const close = document.createElement('button');
      close.type = 'button'; close.textContent = 'Close'; close.className = 'btn btn-default';
      const iframe = document.createElement('iframe');
      iframe.src = '/story-images/library'; iframe.title = 'My images';
      dialog.append(close, iframe);
      const previousFocus = document.activeElement;
      function finish(image) {
        window.removeEventListener('message', selected);
        dialog.close(); dialog.remove(); previousFocus?.focus(); resolve(image);
      }
      function selected(event) {
        if (event.origin !== location.origin || event.source !== iframe.contentWindow ||
            event.data?.type !== 'ckan-story-image-selected') return;
        const image = event.data.image;
        try {
          const url = new URL(image.url, location.origin);
          if (url.origin !== location.origin || !url.pathname.startsWith('/story-images/')) return;
          finish(image);
        } catch (_) { /* Ignore unrelated messages. */ }
      }
      close.onclick = () => finish(null);
      dialog.addEventListener('cancel', event => { event.preventDefault(); finish(null); });
      window.addEventListener('message', selected);
      document.body.append(dialog); dialog.showModal();
    });
  }

  root.StoryImages = {settings, upload, wait, track, dataImage, normalizeQuill, normalizeForm, choose};
})(window);
