/* Visual authoring helpers shared by all section editors. No executable embeds. */
(function () {
  'use strict';
  // CKAN may defer its jQuery bundle. Resolve it only when the ready editor
  // calls these helpers, instead of requiring it while this script loads.
  const $ = (...args) => window.jQuery(...args);
  const id = () => 'visual-' + crypto.randomUUID();
  const copy = value => JSON.parse(JSON.stringify(value));
  const language = value => String(value || document.documentElement.lang || 'en').toLowerCase().split(/[-_]/)[0] === 'es' ? 'es' : 'en';
  const messages = {
    en: {
      heading: 'Add an IHP-WINS dashboard', intro: 'Choose a saved dashboard, tailor its appearance in your story, then add it to the chapter.',
      step1: '1. Find a dashboard', step2: '2. Choose story options (optional)', step3: '3. Add to the chapter',
      findHelp: 'A dataset groups related data. A file (resource) contains the data. A dashboard is a saved view of that file.',
      optionsHelp: 'Filters and the highlighted chart apply to this chapter only. They do not change the original dashboard.',
      addHelp: 'Check your selection, then add this dashboard to the chapter.', saveHelp: 'Save your story to keep this dashboard in the chapter.',
      helpTitle: 'No dashboard yet? How to create one', help: 'Open the selected file and choose Manage views → New view → Dashboard. Configure the charts, then Save. Return here and search again.',
      permissions: 'You need permission to edit the dataset to create or change its dashboards. Ask its owner if these controls are unavailable.',
      resourceLink: 'Open selected file', search: 'Search', searchLabel: 'Dataset search', searchPlaceholder: 'Search datasets',
      dataset: 'Dataset', resource: 'File (resource)', dashboard: 'Dashboard', chooseDataset: 'Choose dataset', chooseResource: 'Choose file', chooseDashboard: 'Choose dashboard',
      current: 'Choose a saved dashboard', searching: 'Searching datasets…', loadingFiles: 'Loading files…', loadingViews: 'Loading dashboards…',
      noDatasets: 'No matching datasets. Try another name or keyword.', noFiles: 'This dataset has no accessible files.',
      noDashboards: 'This file has no saved dashboards. Open the help below to create one if you have edit permission.',
      access: 'You do not have access to this selection. Sign in with an authorized account or choose another dataset.',
      failed: 'Unable to load this selection. Check your connection and try again.', loading: 'Loading dashboard fields…',
      slow: 'The dashboard is unavailable or still loading. Check your access, then reload the preview.',
      ready: 'Dashboard ready. You can choose filters and a chart for this chapter.', wait: 'Choose an accessible dashboard and wait for its fields to load.',
      reload: 'Reload preview', preview: 'Original dashboard preview', previewHelp: 'This preview shows the original dashboard. It does not yet reflect the story filters or highlighted chart chosen above.',
      insert: 'Add dashboard to chapter', allCharts: 'All charts', highlight: 'Highlight chart', field: 'Field', condition: 'Condition', value: 'Value',
      chooseField: 'Choose field', eq: 'Equals', in: 'One of', gte: 'At least / after', lte: 'At most / before', between: 'Between',
      numberExample: 'Example: 20', numberList: 'Example: 10, 20', dateExample: 'YYYY-MM-DD, for example 2026-10-12', dateList: 'YYYY-MM-DD, YYYY-MM-DD', booleanExample: 'true or false', textExample: 'Exact value from the column', textList: 'Exact values separated by commas',
      valuePlaceholder: 'Value; comma-separated for lists or ranges', remove: 'Remove', addFilter: 'Add filter', savedField: 'saved field', savedChart: 'saved chart',
      numeric: 'Enter a valid numeric filter.', boolean: 'Use true or false for this filter.', date: 'Use a valid ISO date, such as 2026-10-12.',
      incomplete: 'Choose a field and complete the filter.', unknownField: 'This saved field is unavailable. Choose an available field before adding the dashboard.',
      unknownChart: 'This saved chart is unavailable. Choose an available chart before adding the dashboard.',
      limit: 'Use at most 24 filters, 100 values per list and 2,000 characters per value.', range: 'Enter two values in ascending order for the range.'
    },
    es: {
      heading: 'Añadir un dashboard de IHP-WINS', intro: 'Elige un dashboard guardado, configura cómo aparecerá en tu historia y añádelo al capítulo.',
      step1: '1. Busca un dashboard', step2: '2. Elige las opciones de la historia (opcional)', step3: '3. Añádelo al capítulo',
      findHelp: 'Un conjunto de datos agrupa información relacionada. Un archivo (recurso) contiene los datos. Un dashboard es una vista guardada de ese archivo.',
      optionsHelp: 'Los filtros y el gráfico destacado se aplican solo a este capítulo. No modifican el dashboard original.',
      addHelp: 'Revisa tu selección y añade este dashboard al capítulo.', saveHelp: 'Guarda la historia para conservar este dashboard en el capítulo.',
      helpTitle: '¿Todavía no hay un dashboard? Cómo crearlo', help: 'Abre el archivo seleccionado y elige Administrar vistas (Manage views) → Nueva vista (New view) → Dashboard. Configura los gráficos y pulsa Guardar (Save). Vuelve aquí y busca de nuevo.',
      permissions: 'Necesitas permiso para editar el conjunto de datos para crear o modificar sus dashboards. Si no aparecen estos controles, consulta con su responsable.',
      resourceLink: 'Abrir el archivo seleccionado', search: 'Buscar', searchLabel: 'Buscar conjunto de datos', searchPlaceholder: 'Buscar conjuntos de datos',
      dataset: 'Conjunto de datos', resource: 'Archivo (recurso)', dashboard: 'Dashboard', chooseDataset: 'Elige un conjunto de datos', chooseResource: 'Elige un archivo', chooseDashboard: 'Elige un dashboard',
      current: 'Elige un dashboard guardado', searching: 'Buscando conjuntos de datos…', loadingFiles: 'Cargando archivos…', loadingViews: 'Cargando dashboards…',
      noDatasets: 'No hay conjuntos de datos que coincidan. Prueba otro nombre o palabra clave.', noFiles: 'Este conjunto de datos no tiene archivos accesibles.',
      noDashboards: 'Este archivo no tiene dashboards guardados. Abre la ayuda para crear uno si tienes permiso de edición.',
      access: 'No tienes acceso a esta selección. Inicia sesión con una cuenta autorizada o elige otro conjunto de datos.',
      failed: 'No se pudo cargar esta selección. Revisa tu conexión e inténtalo de nuevo.', loading: 'Cargando los campos del dashboard…',
      slow: 'El dashboard no está disponible o sigue cargando. Revisa tu acceso y vuelve a cargar la vista previa.',
      ready: 'Dashboard listo. Puedes elegir filtros y un gráfico para este capítulo.', wait: 'Elige un dashboard accesible y espera a que carguen sus campos.',
      reload: 'Volver a cargar la vista previa', preview: 'Vista previa del dashboard original', previewHelp: 'Esta vista previa muestra el dashboard original. Todavía no refleja los filtros de la historia ni el gráfico destacado elegidos arriba.',
      insert: 'Añadir dashboard al capítulo', allCharts: 'Todos los gráficos', highlight: 'Destacar gráfico', field: 'Campo', condition: 'Condición', value: 'Valor',
      chooseField: 'Elige un campo', eq: 'Es igual a', in: 'Uno de', gte: 'Como mínimo / después de', lte: 'Como máximo / antes de', between: 'Entre',
      numberExample: 'Ejemplo: 20', numberList: 'Ejemplo: 10, 20', dateExample: 'AAAA-MM-DD, por ejemplo 2026-10-12', dateList: 'AAAA-MM-DD, AAAA-MM-DD', booleanExample: 'true o false', textExample: 'Valor exacto de la columna', textList: 'Valores exactos separados por comas',
      valuePlaceholder: 'Valor; separa listas o intervalos con comas', remove: 'Quitar', addFilter: 'Añadir filtro', savedField: 'campo guardado', savedChart: 'gráfico guardado',
      numeric: 'Introduce un filtro numérico válido.', boolean: 'Usa true o false para este filtro.', date: 'Usa una fecha ISO válida, como 2026-10-12.',
      incomplete: 'Elige un campo y completa el filtro.', unknownField: 'Este campo guardado no está disponible. Elige otro antes de añadir el dashboard.',
      unknownChart: 'Este gráfico guardado no está disponible. Elige otro antes de añadir el dashboard.',
      limit: 'Usa como máximo 24 filtros, 100 valores por lista y 2.000 caracteres por valor.', range: 'Introduce dos valores en orden ascendente para el intervalo.'
    }
  };
  const dashboardCopy = locale => messages[language(locale)];
  const api = async (action, data) => {
    // CKAN exposes resource_view_list as POST even though it only reads views.
    const post = action === 'resource_view_list';
    const response = await fetch('/api/3/action/' + action + (post ? '' : '?' + new URLSearchParams(data)), {
      credentials: 'same-origin',
      ...(post ? {method: 'POST', headers: {'Content-Type': 'application/json',
        'X-CSRFToken': document.querySelector('[name="_csrf_token"]')?.value || ''}, body: JSON.stringify(data)} : {})
    });
    if ([401, 403].includes(response.status)) { const error = Error('Access denied'); error.access = true; throw error; }
    const result = await response.json();
    if (!response.ok || !result.success) { const error = Error('Dashboard request failed'); error.access = [401, 403].includes(response.status) || result.error?.__type === 'Authorization Error'; throw error; }
    return result.result;
  };
  const field = (label, input) => $('<label class="ds-visual-field">').append($('<span>').text(label), input.attr('aria-label', label));
  const select = (items, value) => {
    const input = $('<select class="form-control">');
    items.forEach(item => input.append($('<option>').val(item[0]).text(item[1])));
    return input.val(value || '');
  };

  function stateEditor(metadata, state, changed, t = dashboardCopy()) {
    const box = $('<div class="ds-state-editor">');
    const filters = $('<div>');
    const widgets = (metadata.widgets || []).map(w => [w.id, w.title || w.type]);
    if (state.widgetId && !widgets.some(w => w[0] === state.widgetId)) widgets.push([state.widgetId, state.widgetId + ' (' + t.savedChart + ')']);
    const widget = select([['', t.allCharts], ...widgets], state.widgetId);
    const rows = [];
    function read(strict = false) {
      const active = rows.filter(r => r.node.parent().length);
      if (active.length > 24) throw Error(t.limit);
      if (strict && widget.val() && !(metadata.widgets || []).some(w => w.id === widget.val())) throw Error(t.unknownChart);
      return {widgetId: widget.val() || null, filters: active.map(r => {
        const key = r.key.val();
        const descriptor = (metadata.fields || []).find(f => f.key === key);
        if (strict && !descriptor) throw Error(key ? t.unknownField : t.incomplete);
        const type = descriptor?.type;
        const convert = raw => {
          const value = raw.trim();
          // Existing text filters may intentionally match an empty cell.
          if (!value && (strict || ['number', 'boolean', 'date'].includes(type))) throw Error(t.incomplete);
          if (value.length > 2000) throw Error(t.limit);
          if (type === 'number') {
            if (!Number.isFinite(Number(value))) throw Error(t.numeric);
            return Number(value);
          }
          if (type === 'boolean') {
            if (!['true', 'false'].includes(value.toLowerCase())) throw Error(t.boolean);
            return value.toLowerCase() === 'true';
          }
          if (type === 'date') {
            const day = value.slice(0, 10), date = new Date(day + 'T00:00:00Z');
            if (!/^(?!0000)\d{4}-\d{2}-\d{2}(?:T(?:[01]\d|2[0-3]):[0-5]\d(?::[0-5]\d(?:\.\d{1,6})?)?(?:Z|[+-](?:[01]\d|2[0-3]):[0-5]\d)?)?$/.test(value) ||
                !Number.isFinite(Date.parse(value)) || !Number.isFinite(date.getTime()) || date.toISOString().slice(0, 10) !== day) throw Error(t.date);
          }
          return value;
        };
        const op = r.op.val();
        if (!key || !['eq', 'in', 'gte', 'lte', 'between'].includes(op)) throw Error(t.incomplete);
        const value = ['in', 'between'].includes(op) ? r.value.val().split(',').map(convert) : convert(r.value.val());
        if (Array.isArray(value) && value.length > 100) throw Error(t.limit);
        if (op === 'between' && (value.length !== 2 || (type === 'date' ? Date.parse(value[0]) > Date.parse(value[1]) : value[0] > value[1]))) throw Error(t.range);
        return {field: key, op, value};
      })};
    }
    function add(filter) {
      const node = $('<div class="ds-filter-row">');
      const fields = (metadata.fields || []).map(f => [f.key, f.label || f.key]);
      if (filter.field && !fields.some(f => f[0] === filter.field)) fields.push([filter.field, filter.field + ' (' + t.savedField + ')']);
      const key = select([['', t.chooseField], ...fields], filter.field);
      const op = select(['eq', 'in', 'gte', 'lte', 'between'].map(op => [op, t[op]]), filter.op || 'eq');
      const value = $('<input class="form-control">').attr('placeholder', t.valuePlaceholder).val(Array.isArray(filter.value) ? filter.value.join(', ') : (filter.value ?? ''));
      function hint() {
        const type = (metadata.fields || []).find(f => f.key === key.val())?.type;
        const list = ['in', 'between'].includes(op.val());
        value.attr('placeholder', type === 'number' ? (list ? t.numberList : t.numberExample) :
          type === 'date' ? (list ? t.dateList : t.dateExample) : type === 'boolean' ? t.booleanExample : (list ? t.textList : t.textExample));
      }
      key.add(op).on('change', hint); hint();
      node.append(field(t.field, key), field(t.condition, op), field(t.value, value),
        $('<button type="button" class="btn btn-default">').text(t.remove).on('click', () => {node.remove(); changed();}));
      rows.push({node, key, op, value});
      filters.append(node);
    }
    (state.filters || []).forEach(add);
    box.append(field(t.highlight, widget), filters,
      $('<button type="button" class="btn btn-default">').text(t.addFilter).on('click', () => {add({}); changed();}));
    box.on('change input', changed);
    return {box, read};
  }

  function section($section, changed) {
    if ($section.data('visuals-initialized')) return;
    $section.data('visuals-initialized', true);
    const layout = select([['auto', 'Automatic'], ['map', 'Text + map'], ['dashboard', 'Text + dashboard'],
      ['combined', 'Text + map and dashboard'], ['media', 'Text + image / multimedia'], ['full', 'Narrative (no side panel)']], 'auto').addClass('ds-presentation');
    $section.find('.section-content-blocks').before(field('Section template', layout));
    const side = select([['left', 'Text on the left'], ['right', 'Text on the right']], 'left');
    const ratio = select([['35', 'One third text'], ['50', 'Equal columns'], ['65', 'Two thirds text']], '35');
    const duration = $('<input type="number" min="1" max="600" step="1" class="form-control">').val(10);
    const preview = $('<div class="ds-template-preview" aria-label="Template preview">');
    const composition = $('<div class="ds-composition-controls">').append(field('Text position', side),
      field('Column proportions', ratio), field('Slide duration (seconds)', duration), preview);
    $section.find('.section-content-blocks').before(composition);
    function showPreview() {
      preview.empty().attr('data-side', side.val()).css('--story-text-width', ratio.val() + '%');
      preview.append($('<span>').text('Text'));
      if (layout.val() !== 'full') preview.append($('<span>').text({map: 'Map', dashboard: 'Dashboard', combined: 'Map + Dashboard', media: 'Image / Multimedia', auto: 'Visualizations'}[layout.val()]));
    }
    $section.data('presentation', {
      read: () => ({type: 'presentation', version: 1, layout: layout.val() || 'auto',
        text_side: side.val(), text_width: Number(ratio.val()), duration: Number(duration.val()) || 10,
        width: $section.data('section-width').read()}),
      load: data => {layout.val(data.layout || 'auto'); side.val(data.text_side || 'left');
        ratio.val(String(data.text_width || 35)); duration.val(data.duration || 10);
        $section.data('section-width').load(data.width); showPreview();}
    });
    composition.on('input change', () => {showPreview(); changed();});
    layout.on('change', () => {showPreview(); changed();});
    showPreview();
    const mode = select([['normal', 'Normal'], ['full', '100% of screen'], ['custom', 'Custom']], 'normal').addClass('ds-section-width-mode');
    const value = $('<input type="number" step="any" class="form-control ds-section-width-value">');
    const unit = select([['%', '%'], ['px', 'px']], '%').addClass('ds-section-width-unit');
    const custom = $('<div class="ds-section-width-custom">').append(field('Width value', value), field('Width unit', unit));
    const note = $('<p class="help-block ds-section-width-note">');
    const controls = $('<div class="ds-section-width-controls">').append(field('Section width', mode), custom, note);
    $section.find('.section-content-blocks').before(controls);

    function refresh() {
      const hasVisual = $section.find('.terria-tab-url').toArray().some(el => el.value.trim()) ||
        $section.find('.ds-dashboard-editor').toArray().some(el => !!$(el).data('dashboard')?.view_id);
      const sidePanel = ['storymap', 'slides'].includes($('#display_mode').val()) && layout.val() !== 'full' && hasVisual;
      const isCustom = mode.val() === 'custom';
      mode.prop('disabled', sidePanel);
      custom.prop('hidden', !isCustom);
      value.add(unit).prop('disabled', sidePanel || !isCustom);
      value.prop('required', isCustom && !sidePanel);
      value.attr('max', unit.val() === '%' ? '100' : null);
      const number = Number(value.val());
      const invalid = isCustom && (!value.val() || !Number.isFinite(number) || number <= 0 || (unit.val() === '%' && number > 100));
      value[0].setCustomValidity(!sidePanel && invalid ? 'Enter positive pixels or a percentage greater than 0 and at most 100.' : '');
      note.text(sidePanel ? 'Width applies to narrative sections without a side panel. The saved width is kept.' :
        'Applies to the section title and content. Custom widths are centered and adapt to mobile screens.');
    }
    function read() {
      refresh();
      return mode.val() === 'custom' ? {mode: 'custom', value: value.val() === '' ? null : Number(value.val()), unit: unit.val()} : {mode: mode.val()};
    }
    function load(width) {
      width = width || {mode: 'normal'};
      mode.val(['normal', 'full', 'custom'].includes(width.mode) ? width.mode : 'normal');
      value.val(width.value ?? '');
      unit.val(width.unit === 'px' ? 'px' : '%');
      refresh();
    }
    $section.data('section-width', {read, load, refresh});
    controls.on('input change', 'input, select', () => { refresh(); changed(); });
    layout.on('change', refresh);
    $('#display_mode').on('change', refresh);
    refresh();
    $section.find('.add-block-controls .btn-group').append('<button type="button" class="btn btn-primary btn-sm add-dashboard-block"><i class="fa fa-bar-chart"></i> Dashboard</button>');
  }

  function dashboard(data, changed, options = {}) {
    const t = dashboardCopy(options.language);
    data = Object.assign({type: 'dashboard', version: 1, id: id(), title: '', view_id: '', state: {filters: [], widgetId: null}}, copy(data || {}));
    const box = $('<div class="ds-dashboard-editor">').attr('lang', language(options.language)).data('dashboard', data);
    const message = $('<p class="ds-dashboard-status" role="status" aria-live="polite">');
    const search = $('<input class="form-control">').attr('placeholder', t.searchPlaceholder);
    const datasets = select([['', t.chooseDataset]], '');
    const resources = select([['', t.chooseResource]], '').prop('disabled', true);
    const views = select([['', t.chooseDashboard]], '').prop('disabled', true);
    const current = $('<strong class="ds-dashboard-current">').text(data.title || t.current);
    const controls = $('<div>');
    const preview = $('<div class="ds-dashboard-preview-area" hidden>').append($('<h4>').text(t.preview), $('<p>').text(t.previewHelp));
    const resourceLink = $('<a target="_blank" rel="noopener noreferrer" hidden>').text(t.resourceLink);
    let stateForm, frame, request = 0, timer;
    const notify = () => box.triggerHandler('dashboard:selection-change');
    function synchronize() {
      try { if (stateForm) data.state = stateForm.read(); message.text(t.ready); changed(); }
      catch (error) { message.text(error.message); }
      notify();
    }
    function reset(clearSelection = true) {
      clearTimeout(timer);
      box.removeData('metadata'); controls.empty(); stateForm = null;
      if (frame) frame.remove(); frame = null; preview.prop('hidden', true);
      if (clearSelection) { data.view_id = ''; data.title = ''; data.state = {filters: [], widgetId: null}; current.text(t.current); }
      message.text(''); notify();
    }
    function open() {
      reset(false);
      if (!data.view_id) return;
      message.text(t.loading); preview.prop('hidden', false);
      // A fresh browsing context also rejects a late ready from a previous
      // load of the same view ID; source + origin + viewId must all match.
      frame = $('<iframe class="ds-dashboard-preview" allowfullscreen>').attr('title', t.preview);
      const active = frame;
      active.on('load', () => {if (frame === active) active[0].contentWindow.postMessage({type: 'dashboard:hello', version: 1}, location.origin);});
      active.attr('src', '/dashboard/' + encodeURIComponent(data.view_id) + '/embed'); preview.append(active);
      timer = setTimeout(() => {if (frame === active && !box.data('metadata')) message.text(t.slow);}, 20000);
    }
    const listener = event => {
      if (!box[0].isConnected) { window.removeEventListener('message', listener); clearTimeout(timer); return; }
      if (!frame || event.origin !== location.origin || event.source !== frame[0].contentWindow ||
          event.data?.type !== 'dashboard:ready' || event.data.version !== 1 || event.data.viewId !== data.view_id ||
          !Array.isArray(event.data.fields) || !Array.isArray(event.data.widgets)) return;
      if (box.data('metadata')) return; // Repeated hello/ready must not reset edits.
      clearTimeout(timer);
      box.data('metadata', event.data);
      stateForm = stateEditor(event.data, data.state, synchronize, t);
      controls.empty().append(stateForm.box); message.text(t.ready); notify();
    };
    window.addEventListener('message', listener);
    const failure = (error, generation) => {if (generation === request) message.text(error.access ? t.access : t.failed);};
    const clearOptions = (input, placeholder) => input.empty().append($('<option>').val('').text(placeholder)).prop('disabled', true);
    const load = $('<button type="button" class="btn btn-default">').text(t.search).on('click', async () => {
      const generation = ++request;
      reset(false); clearOptions(datasets, t.chooseDataset); clearOptions(resources, t.chooseResource); clearOptions(views, t.chooseDashboard);
      resourceLink.removeAttr('href').prop('hidden', true); changed();
      try {
        message.text(t.searching);
        const result = await api('package_search', {q: search.val(), rows: 30});
        if (generation !== request) return;
        result.results.forEach(d => datasets.append($('<option>').val(d.id).text(d.title || d.name)));
        datasets.prop('disabled', !result.results.length); message.text(result.results.length ? '' : t.noDatasets);
      } catch (error) {failure(error, generation);}
    });
    search.on('keydown', event => {if (event.key === 'Enter') {event.preventDefault(); load.trigger('click');}});
    datasets.on('change', async () => {
      const generation = ++request;
      reset(); clearOptions(resources, t.chooseResource); clearOptions(views, t.chooseDashboard);
      resourceLink.removeAttr('href').prop('hidden', true); changed();
      if (!datasets.val()) return;
      try {
        message.text(t.loadingFiles);
        const result = await api('package_show', {id: datasets.val()});
        if (generation !== request) return;
        result.resources.forEach(r => resources.append($('<option>').val(r.id).text(r.name || r.description || r.id)));
        resources.prop('disabled', !result.resources.length); message.text(result.resources.length ? '' : t.noFiles);
      } catch (error) {failure(error, generation);}
    });
    resources.on('change', async () => {
      const generation = ++request;
      reset(); clearOptions(views, t.chooseDashboard); resourceLink.removeAttr('href').prop('hidden', true); changed();
      if (!resources.val()) return;
      // Construct a local CKAN resource route; never trust a returned external URL.
      resourceLink.attr('href', '/dataset/' + encodeURIComponent(datasets.val()) + '/resource/' + encodeURIComponent(resources.val())).prop('hidden', false);
      try {
        message.text(t.loadingViews);
        const result = await api('resource_view_list', {id: resources.val()});
        if (generation !== request) return;
        const dashboards = result.filter(v => v.view_type === 'dashboard_view');
        dashboards.forEach(v => views.append($('<option>').val(v.id).text(v.title)));
        views.prop('disabled', !dashboards.length); message.text(dashboards.length ? '' : t.noDashboards);
      } catch (error) {failure(error, generation);}
    });
    views.on('change', () => {
      ++request; reset();
      if (views.val()) {data.view_id = views.val(); data.title = views.find(':selected').text(); current.text(data.title); open();}
      changed(); notify();
    });
    const step = (heading, help) => $('<section class="ds-dashboard-step">').append($('<h3>').text(heading), $('<p>').text(help));
    const find = step(t.step1, t.findHelp).append(field(t.searchLabel, search), load,
      field(t.dataset, datasets), field(t.resource, resources), field(t.dashboard, views));
    find.append($('<details class="ds-dashboard-help">').append($('<summary>').text(t.helpTitle), $('<p>').text(t.help), $('<p>').text(t.permissions), resourceLink));
    const choose = step(t.step2, t.optionsHelp).append(controls);
    const add = step(t.step3, options.picker ? t.addHelp : t.saveHelp);
    box.append(current, find, choose, add, message,
      $('<button type="button" class="btn btn-default">').text(t.reload).on('click', open), preview);
    box.data('insert-slot', add);
    box.data('read', (settings = {}) => {
      if (settings.requireReady && (!data.view_id || !stateForm || box.data('metadata')?.viewId !== data.view_id)) throw Error(t.wait);
      if (stateForm) data.state = stateForm.read(!!settings.requireReady);
      // A saved dashboard survives loading/error states while editing a story.
      return copy(data);
    });
    box.data('can-insert', () => {try {box.data('read')({requireReady: true}); return true;} catch (_) {return false;}});
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
  window.StoryVisualsEditor = {section, dashboard, text, dashboardCopy};
})();
