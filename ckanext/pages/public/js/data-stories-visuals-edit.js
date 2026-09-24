/* Visual authoring helpers shared by all section editors. No executable embeds. */
(function ($) {
  'use strict';
  const id = () => 'visual-' + crypto.randomUUID();
  const copy = value => JSON.parse(JSON.stringify(value));
  const api = async (action, data) => {
    const response = await fetch('/api/3/action/' + action + '?' + new URLSearchParams(data), {credentials: 'same-origin'});
    const result = await response.json();
    if (!response.ok || !result.success) throw Error('Unable to load this resource. Check your access and try again.');
    return result.result;
  };
  const field = (label, input) => $('<label class="ds-visual-field">').append($('<span>').text(label), input);
  const select = (items, value) => {
    const input = $('<select class="form-control">');
    items.forEach(item => input.append($('<option>').val(item[0]).text(item[1])));
    return input.val(value || '');
  };

  function stateEditor(metadata, state, changed) {
    const box = $('<div class="ds-state-editor">');
    const filters = $('<div>');
    const widget = select([['', 'All charts'], ...(metadata.widgets || []).map(w => [w.id, w.title || w.type])], state.widgetId);
    const rows = [];
    function read() {
      return {widgetId: widget.val() || null, filters: rows.filter(r => r.node.parent().length).map(r => {
        const key = r.key.val();
        const type = (metadata.fields || []).find(f => f.key === key)?.type;
        const convert = value => {
          if (type === 'number') {
            if (!value.trim() || !Number.isFinite(Number(value))) throw Error('Enter a valid numeric filter.');
            return Number(value);
          }
          if (type === 'boolean') {
            if (!['true', 'false'].includes(value.trim().toLowerCase())) throw Error('Use true or false for this filter.');
            return value.trim().toLowerCase() === 'true';
          }
          return value.trim();
        };
        const op = r.op.val();
        const value = ['in', 'between'].includes(op) ? r.value.val().split(',').map(convert) : convert(r.value.val());
        if (!key || (op === 'between' && value.length !== 2)) throw Error('Choose a field and complete the filter.');
        return {field: key, op, value};
      })};
    }
    function add(filter) {
      const node = $('<div class="ds-filter-row">');
      const fields = (metadata.fields || []).map(f => [f.key, f.label || f.key]);
      if (filter.field && !fields.some(f => f[0] === filter.field)) fields.push([filter.field, filter.field + ' (saved field)']);
      const key = select([['', 'Choose field'], ...fields], filter.field);
      const op = select([['eq', 'Equals'], ['in', 'One of'], ['gte', 'At least / after'], ['lte', 'At most / before'], ['between', 'Between']], filter.op || 'eq');
      const value = $('<input class="form-control" placeholder="Value; comma-separated for lists or ranges">').val(Array.isArray(filter.value) ? filter.value.join(', ') : (filter.value ?? ''));
      node.append(field('Field', key), field('Condition', op), field('Value', value),
        $('<button type="button" class="btn btn-default">Remove</button>').on('click', () => {node.remove(); changed();}));
      rows.push({node, key, op, value});
      filters.append(node);
    }
    (state.filters || []).forEach(add);
    box.append(field('Highlight chart', widget), filters,
      $('<button type="button" class="btn btn-default">Add filter</button>').on('click', () => add({})));
    box.on('change input', changed);
    return {box, read};
  }

  function section($section, changed) {
    if ($section.data('visuals-initialized')) return;
    $section.data('visuals-initialized', true);
    const layout = select([['auto', 'Automatic'], ['map', 'Text + map'], ['dashboard', 'Text + dashboard'],
      ['combined', 'Text + map and dashboard'], ['full', 'Full width']], 'auto').addClass('ds-presentation');
    $section.find('.section-content-blocks').before(field('Section template', layout));
    layout.on('change', changed);
    $section.find('.add-block-controls .btn-group').append('<button type="button" class="btn btn-primary btn-sm add-dashboard-block"><i class="fa fa-bar-chart"></i> Dashboard</button>');
  }

  function dashboard(data, changed) {
    data = Object.assign({type: 'dashboard', version: 1, id: id(), title: '', view_id: '', state: {filters: [], widgetId: null}}, copy(data || {}));
    const box = $('<div class="ds-dashboard-editor">').data('dashboard', data);
    const message = $('<p role="status" aria-live="polite">');
    const search = $('<input class="form-control" placeholder="Search datasets">');
    const datasets = select([['', 'Choose dataset']], '');
    const resources = select([['', 'Choose resource']], '');
    const views = select([['', 'Choose dashboard']], '');
    const frame = $('<iframe title="Dashboard preview" class="ds-dashboard-preview" allowfullscreen>');
    const controls = $('<div>');
    let stateForm, request = 0, timer;
    function synchronize() {
      try { if (stateForm) data.state = stateForm.read(); message.text(''); changed(); }
      catch (error) { message.text(error.message); }
    }
    function open() {
      if (!data.view_id) return;
      message.text('Loading dashboard fields…');
      frame.attr('src', '/dashboard/' + encodeURIComponent(data.view_id) + '/embed');
      controls.empty(); stateForm = null;
      clearTimeout(timer);
      timer = setTimeout(() => message.text('Dashboard unavailable or still loading. Check access, then retry.'), 20000);
    }
    const listener = event => {
      if (!box[0].isConnected) { window.removeEventListener('message', listener); clearTimeout(timer); return; }
      if (event.origin !== location.origin || event.source !== frame[0].contentWindow ||
          event.data?.type !== 'dashboard:ready' || event.data.version !== 1 || event.data.viewId !== data.view_id) return;
      clearTimeout(timer);
      box.data('metadata', event.data);
      stateForm = stateEditor(event.data, data.state, synchronize);
      controls.empty().append(stateForm.box);
      message.text('');
    };
    window.addEventListener('message', listener);
    frame.on('load', () => frame[0].contentWindow.postMessage({type: 'dashboard:hello', version: 1}, location.origin));
    const load = $('<button type="button" class="btn btn-default">Search</button>').on('click', async () => {
      const current = ++request;
      try {
        message.text('Searching…');
        const result = await api('package_search', {q: search.val(), rows: 30});
        if (current !== request) return;
        datasets.empty().append($('<option>').val('').text('Choose dataset'));
        result.results.forEach(d => datasets.append($('<option>').val(d.id).text(d.title || d.name)));
        message.text(result.results.length ? '' : 'No matching datasets.');
      } catch (error) {message.text(error.message);}
    });
    datasets.on('change', async () => {
      const current = ++request;
      resources.empty(); views.empty();
      if (!datasets.val()) return;
      try {
        const result = await api('package_show', {id: datasets.val()});
        if (current !== request) return;
        resources.append($('<option>').val('').text('Choose resource'));
        result.resources.forEach(r => resources.append($('<option>').val(r.id).text(r.name || r.description || r.id)));
      } catch (error) {message.text(error.message);}
    });
    resources.on('change', async () => {
      const current = ++request;
      views.empty();
      if (!resources.val()) return;
      try {
        const result = await api('resource_view_list', {id: resources.val()});
        if (current !== request) return;
        const dashboards = result.filter(v => v.view_type === 'dashboard_view');
        views.append($('<option>').val('').text('Choose dashboard'));
        dashboards.forEach(v => views.append($('<option>').val(v.id).text(v.title)));
        message.text(dashboards.length ? '' : 'This resource has no saved dashboard. Create one in Manage views first.');
      } catch (error) {message.text(error.message);}
    });
    views.on('change', () => {
      if (!views.val()) return;
      data.view_id = views.val(); data.title = views.find(':selected').text();
      data.state = {filters: [], widgetId: null};
      box.find('.ds-dashboard-current').text(data.title); open(); changed();
    });
    box.append($('<strong class="ds-dashboard-current">').text(data.title || 'Choose a saved dashboard'),
      field('Dataset search', search), load, field('Dataset', datasets), field('Resource', resources), field('Dashboard', views),
      $('<button type="button" class="btn btn-default">Reload preview</button>').on('click', open), message, controls, frame);
    box.data('read', () => { if (stateForm) data.state = stateForm.read(); return copy(data); });
    if (data.view_id) open();
    return box;
  }

  function text(block, quill, data, changed) {
    const saved = {id: data.id || id(), references: copy(data.references || [])};
    block.data('visual-text', saved);
    const button = $('<button type="button" class="btn btn-default ds-link-visual">Link visualization</button>');
    block.find('.content-block-body').prepend(button);
    button.on('mousedown', event => event.preventDefault());
    button.on('click', () => {
      const range = quill.getSelection();
      if (!range || !range.length) { alert('Select the narrative text to link first.'); return; }
      const existingLink = quill.getFormat(range).link || '';
      const previous = saved.references.find(r => existingLink === '#story-ref-' + r.id);
      const ref = copy(previous || {id: id(), version: 1, state: {filters: [], widgetId: null}});
      const section = block.closest('.content-section-editor');
      const sources = [['', 'Keep current map']];
      section.find('.terria-tab-panel').each(function () {
        const panel = $(this);
        const meta = panel.data('sequence-source') || {};
        if (!meta.source_id) { meta.source_id = id(); panel.data('sequence-source', meta); }
        sources.push([meta.source_id, panel.find('.terria-tab-title').val() || 'Map']);
      });
      const maps = select(sources, ref.source_id);
      const slides = select([['', 'Base map scene'], ...section.find('[data-block-type="terria_slide"]').toArray().map(el => {
        const slide = $(el).data('slide'); return [slide.slide_id, slide.title || 'Slide'];
      })], ref.slide_id);
      const dashboards = section.find('.ds-dashboard-editor').toArray();
      const dashboardSelect = select([['', 'Keep current dashboard'], ...dashboards.map(el => {
        const d = $(el).data('dashboard'); return [d.id, d.title || 'Dashboard'];
      })], ref.dashboard_id);
      const dialog = $('<dialog class="ds-reference-dialog">');
      const controls = $('<div>');
      const message = $('<p role="alert">');
      const enter = $('<input type="checkbox">').prop('checked', !!ref.on_enter);
      let stateForm;
      function update() {
        const target = dashboards.find(el => $(el).data('dashboard').id === dashboardSelect.val());
        controls.empty(); stateForm = null;
        if (target) {
          const metadata = $(target).data('metadata');
          if (!metadata) { message.text('Wait for the dashboard preview to load its fields.'); return; }
          stateForm = stateEditor(metadata, ref.state, () => {});
          controls.append(stateForm.box); message.text('');
        }
      }
      dashboardSelect.on('change', () => {ref.state = {filters: [], widgetId: null}; update();});
      dialog.append($('<h3>').text('Link visualization'), field('Map', maps), field('Saved Terria slide', slides),
        field('Dashboard', dashboardSelect), controls, field('Also activate when this paragraph is reached', enter), message,
        $('<button type="button" class="btn btn-primary">Apply</button>').on('click', () => {
          try {
            if (dashboardSelect.val() && !stateForm) throw Error('Wait for dashboard fields to load.');
            Object.assign(ref, {source_id: maps.val() || null, slide_id: slides.val() || null,
              dashboard_id: dashboardSelect.val() || null, on_enter: enter.prop('checked'),
              state: stateForm ? stateForm.read() : {filters: [], widgetId: null}});
            if (!ref.source_id && !ref.slide_id && !ref.dashboard_id) throw Error('Choose a map, slide or dashboard.');
            saved.references = saved.references.filter(r => r.id !== ref.id).concat(ref);
            quill.formatText(range.index, range.length, 'link', '#story-ref-' + ref.id, 'user');
            changed(); dialog[0].close();
          } catch (error) {message.text(error.message);}
        }),
        $('<button type="button" class="btn btn-default">Cancel</button>').on('click', () => dialog[0].close()));
      if (previous) dialog.append($('<button type="button" class="btn btn-default">Remove reference</button>').on('click', () => {
        saved.references = saved.references.filter(r => r.id !== previous.id);
        quill.formatText(range.index, range.length, 'link', false, 'user'); changed(); dialog[0].close();
      }));
      dialog.on('close', () => dialog.remove());
      $('body').append(dialog); update(); dialog[0].showModal();
    });
  }
  window.StoryVisualsEditor = {section, dashboard, text};
})(jQuery);
