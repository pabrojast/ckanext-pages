/* Shared rich-text lifecycle for Data Stories and Rapid Response. */
(function (root) {
  'use strict';
  const editors = new WeakMap();
  let registered = false;
  function registerFormats() {
    if (registered) return;
    ['image', 'video'].forEach(function (name) {
      const Base = root.Quill.import('formats/' + name);
      const attributes = ['alt', 'height', 'width', 'style', 'class', 'allow', 'title'];
      class StyledMedia extends Base {
        static formats(node) {
          const formats = super.formats(node);
          attributes.forEach(attr => { if (node.hasAttribute(attr)) formats[attr] = node.getAttribute(attr); });
          return formats;
        }
        format(name, value) {
          if (!attributes.includes(name)) return super.format(name, value);
          if (value) this.domNode.setAttribute(name, value);
          else this.domNode.removeAttribute(name);
        }
      }
      root.Quill.register(StyledMedia, true);
    });
    registered = true;
  }
  function createText(element, html, options, onChange) {
    registerFormats();
    const quill = new root.Quill(element, options);
    const state = {original: html || '', dirty: false};
    if (html) quill.clipboard.dangerouslyPasteHTML(html, 'silent');
    editors.set(quill, state);
    const changed = function () {
      state.dirty = true;
      if (onChange) onChange(getHtml(quill));
    };
    quill.on('text-change', changed);
    return {quill, getHtml: () => getHtml(quill), destroy: () => quill.off('text-change', changed)};
  }
  function getHtml(quill) {
    const state = editors.get(quill);
    return state && !state.dirty ? state.original : quill.root.innerHTML;
  }
  function id() {
    if (root.crypto.randomUUID) return root.crypto.randomUUID();
    return Array.from(root.crypto.getRandomValues(new Uint8Array(16)), x => x.toString(16).padStart(2, '0')).join('');
  }
  root.StoryEditorCore = {registerFormats, createText, getHtml, id};
})(window);
