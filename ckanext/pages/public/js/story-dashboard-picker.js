(function () {
  'use strict';
  function start() {
    if (!window.jQuery || !window.StoryVisualsEditor) { setTimeout(start, 50); return; }
    const language = document.getElementById('story-dashboard-picker').dataset.language;
    const copy = window.StoryVisualsEditor.dashboardCopy(language);
    document.getElementById('story-dashboard-picker-heading').textContent = copy.heading;
    document.getElementById('story-dashboard-picker-intro').textContent = copy.intro;
    const insert = document.getElementById('story-dashboard-insert');
    insert.textContent = copy.insert;
    const box = window.StoryVisualsEditor.dashboard({}, () => {}, {language, picker: true});
    document.getElementById('story-dashboard-picker-editor').append(box[0]);
    box.data('insert-slot').append(insert);
    box.on('dashboard:selection-change', () => {
      insert.disabled = !box.data('can-insert')();
      document.getElementById('story-dashboard-picker-error').textContent = '';
    });
    insert.addEventListener('click', () => {
      try {
        const dashboard = box.data('read')({requireReady: true});
        window.parent.postMessage({type: 'ckan-story-dashboard-selected', version: 1, dashboard}, location.origin);
      } catch (error) { document.getElementById('story-dashboard-picker-error').textContent = error.message; }
    });
  }
  start();
})();
