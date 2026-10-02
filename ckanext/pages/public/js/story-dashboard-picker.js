(function () {
  'use strict';
  function start() {
    if (!window.jQuery || !window.StoryVisualsEditor) { setTimeout(start, 50); return; }
    const box = window.StoryVisualsEditor.dashboard({}, () => {});
    document.getElementById('story-dashboard-picker-editor').append(box[0]);
    document.getElementById('story-dashboard-insert').addEventListener('click', () => {
      try {
        const dashboard = box.data('read')();
        if (!dashboard.view_id || !box.data('metadata')) throw Error('Choose an accessible dashboard and wait for its preview.');
        window.parent.postMessage({type: 'ckan-story-dashboard-selected', version: 1, dashboard}, location.origin);
      } catch (error) { document.getElementById('story-dashboard-picker-error').textContent = error.message; }
    });
  }
  start();
})();
