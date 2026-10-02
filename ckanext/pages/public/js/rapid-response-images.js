/* Upload inline images before Rapid Response serializes any editor or block. */
(function () {
  'use strict';
  var editors = [];
  var uploads = new Map();
  var pending = new Set();
  var queue = Promise.resolve();
  var uriPattern = /data:image\/[a-zA-Z0-9.+-]+;base64,[a-zA-Z0-9+/=\r\n]+/gi;

  function message(text, failed) {
    var form = document.getElementById('rapid-response-form');
    if (!form) return;
    var box = document.getElementById('rr-image-status');
    if (!box) {
      box = document.createElement('div');
      box.id = 'rr-image-status';
      box.setAttribute('role', 'status');
      box.setAttribute('aria-live', 'polite');
      form.prepend(box);
    }
    box.className = 'alert ' + (failed ? 'alert-danger' : 'alert-info');
    box.textContent = text;
    box.hidden = !text;
    if (failed) box.scrollIntoView({block: 'nearest'});
  }

  function track(promise) {
    pending.add(promise);
    promise.then(function () {
      pending.delete(promise);
      if (!pending.size && !document.querySelector('.ql-editor img[src^="data:image/"]')) {
        message('', false);
      }
    }, function (error) {
      pending.delete(promise);
      message('Image upload failed. Your edits are preserved. Save again to retry. ' +
        (error.message || error), true);
    });
    return promise;
  }

  function readFile(file) {
    return new Promise(function (resolve, reject) {
      var reader = new FileReader();
      reader.onload = function () { resolve(reader.result); };
      reader.onerror = function () { reject(new Error('Could not read the image.')); };
      reader.readAsDataURL(file);
    });
  }

  function upload(uri) {
    if (uploads.has(uri)) return uploads.get(uri);
    var job = queue.then(function () {
      message('Uploading images…', false);
      return window.StoryImages.dataImage(uri).then(function (image) { return image.url; });
    });
    uploads.set(uri, job);
    queue = job.catch(function () {});
    job.catch(function () { uploads.delete(uri); });
    return job;
  }

  function replaceText(value) {
    var found = Array.from(new Set((value || '').match(uriPattern) || []));
    return found.reduce(function (chain, uri) {
      return chain.then(function (html) {
        return upload(uri).then(function (url) { return html.split(uri).join(url); });
      });
    }, Promise.resolve(value));
  }

  function processEditor(state) {
    if (!state.quill.root.isConnected) return Promise.resolve();
    var images = Array.from(state.quill.root.querySelectorAll('img'));
    return images.reduce(function (chain, img) {
      return chain.then(function () {
        var uri = img.getAttribute('src') || '';
        if (!/^data:image\//i.test(uri)) return;
        return upload(uri).then(function (url) {
          // Do not resurrect an image deleted/replaced while the request ran.
          if (img.isConnected && img.getAttribute('src') === uri) {
            img.setAttribute('src', url);
            state.quill.update('user');
            state.sync();
          }
        });
      });
    }, Promise.resolve());
  }

  function attach(quill, sync) {
    var state = {quill: quill, sync: sync || function () {}, scheduled: false};
    editors.push(state);
    function schedule() {
      if (state.scheduled) return;
      state.scheduled = true;
      track(Promise.resolve().then(function () { return processEditor(state); })
        .finally(function () { state.scheduled = false; }));
    }
    function insertFiles(files) {
      Array.from(files).filter(function (file) { return /^image\//.test(file.type); })
        .forEach(function (file) {
          track(readFile(file).then(function (uri) {
            var range = quill.getSelection(true);
            var index = range ? range.index : quill.getLength() - 1;
            quill.insertEmbed(index, 'image', uri, 'user');
            quill.setSelection(index + 1, 'silent');
            return processEditor(state);
          }));
        });
    }
    var toolbar = quill.getModule('toolbar');
    if (toolbar) toolbar.addHandler('image', function () {
      var input = document.createElement('input');
      input.type = 'file';
      input.accept = 'image/*';
      input.multiple = true;
      input.onchange = function () { insertFiles(input.files); };
      input.click();
    });
    ['paste', 'drop'].forEach(function (eventName) {
      quill.root.addEventListener(eventName, function (event) {
        var transfer = event.clipboardData || event.dataTransfer;
        var files = transfer && Array.from(transfer.files || []).filter(function (f) {
          return /^image\//.test(f.type);
        });
        if (files && files.length) {
          event.preventDefault();
          event.stopImmediatePropagation();
          insertFiles(files);
        }
      }, true);
    });
    quill.root.addEventListener('dragover', function (event) {
      if (event.dataTransfer && Array.from(event.dataTransfer.items || []).some(function (item) {
        return /^image\//.test(item.type);
      })) event.preventDefault();
    });
    quill.on('text-change', schedule);
  }

  async function prepare(form) {
    message('', false);
    let pendingFailure;
    while (pending.size) {
      // Drain all handlers of a failed paste before allowing the next retry.
      const settled = await Promise.allSettled(Array.from(pending));
      const failed = settled.find(result => result.status === 'rejected');
      if (failed) pendingFailure = failed.reason;
    }
    if (pendingFailure) throw pendingFailure;
    for (var state of editors) { if (state.quill.root.isConnected) await processEditor(state); }
    // Also covers source mode, JSON metadata and gallery/header URL fields.
    for (var field of form.querySelectorAll('textarea, input[type="hidden"], input[type="text"], input[type="url"]')) {
      var value = await replaceText(field.value);
      if (value !== field.value) {
        field.value = value;
        field.dispatchEvent(new Event('change', {bubbles: true}));
      }
    }
    message('', false);
  }

  function detach(quill) { editors = editors.filter(function (state) { return state.quill !== quill; }); }
  function uploadFile(file) { return track(readFile(file).then(upload)); }
  window.RapidResponseImages = {attach: attach, detach: detach, uploadFile: uploadFile, prepare: prepare, message: message};
})();
