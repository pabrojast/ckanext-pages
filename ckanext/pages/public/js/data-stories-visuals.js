(function () {
  'use strict';
  window.StoryVisualsViewer = function (options) {
    const {root, config} = options;
    const cards = Array.from(root.querySelectorAll('.storymap-card'));
    cards.forEach((card, index) => {
      if (config.scenes[index].presentation !== 'media') return;
      const body = card.querySelector('.storymap-card-body');
      const visual = document.createElement('div'); visual.className = 'storymap-composition-media';
      Array.from(body.children).filter(el => el.matches('.storymap-card-media, .storymap-image-trigger')).forEach(el => visual.append(el));
      body.append(visual);
    });
    const pane = root.querySelector('.storymap-dashboard-pane');
    const mapPane = root.querySelector('.storymap-map-pane');
    const status = root.querySelector('.storymap-visual-status');
    const frames = new Map();
    const media = root.querySelector('.storymap-media');
    const mobile = window.matchMedia('(max-width: 768px)');
    const compact = window.matchMedia('(max-width: 1440px), (max-height: 850px)');
    const visualTabs = root.querySelector('.storymap-visual-tabs');
    let visualChoice = null;
    let playback;
    const visualState = (pending, error) => playback?.visual('dashboard', pending, error);
    const hasDashboards = config.scenes.some(scene => scene.dashboards?.length);
    const stackedMedia = hasDashboards || config.mobileStackedMedia;
    root.classList.toggle('has-story-dashboards', hasDashboards);
    root.classList.toggle('has-stacked-media', !!stackedMedia);
    const slots = cards.map((card, index) => {
      const scene = config.scenes[index];
      if (!stackedMedia || scene.layout === 'full') return null;
      const slot = document.createElement('div');
      slot.className = 'storymap-mobile-visual-slot';
      const combined = scene.sources.length && scene.dashboards?.length && !['map', 'dashboard'].includes(scene.presentation);
      slot.classList.toggle('is-combined', !!combined);
      card.append(slot); return slot;
    });
    let active = -1, currentFrame, serial = 0, slideIndex = 0;
    const slides = config.displayMode === 'slides';
    const say = message => {if (message) playback?.pause(); if (status) {status.textContent = message; status.hidden = !message;}};
    function chooseVisual(choice) {
      if (choice) visualChoice = choice;
      const combined = root.classList.contains('has-combined-visuals');
      const selected = visualChoice || (compact.matches ? 'map' : 'both');
      root.dataset.visualView = combined ? selected : '';
      if (visualTabs) {
        visualTabs.hidden = !combined;
        visualTabs.querySelectorAll('[data-visual-view]').forEach(button => {
          button.setAttribute('aria-pressed', String(button.dataset.visualView === selected));
        });
      }
      slots.forEach(slot => {if (slot) slot.classList.toggle('shows-both', selected === 'both');});
      requestAnimationFrame(placeMedia);
    }
    visualTabs?.querySelectorAll('[data-visual-view]').forEach(button => button.addEventListener('click', () => chooseVisual(button.dataset.visualView)));
    compact.addEventListener('change', () => chooseVisual());
    function placeMedia() {
      if (!media || !stackedMedia) return;
      const slot = mobile.matches && slots[active];
      root.classList.toggle('has-mobile-slot', !!slot);
      if (slot) {
        const bounds = slot.getBoundingClientRect(), parent = root.getBoundingClientRect();
        media.style.top = (bounds.top - parent.top) + 'px';
        media.style.left = (bounds.left - parent.left) + 'px';
        media.style.width = bounds.width + 'px';
        media.style.height = bounds.height + 'px';
      } else {
        ['top', 'left', 'width', 'height'].forEach(key => {media.style[key] = '';});
      }
    }
    mobile.addEventListener('change', placeMedia);
    window.addEventListener('resize', placeMedia);
    if ('ResizeObserver' in window) {
      const observer = new ResizeObserver(() => requestAnimationFrame(placeMedia));
      cards.forEach(card => observer.observe(card));
    }
    function send(record) {
      if (!record.ready || !record.state || currentFrame !== record) return;
      const requestId = 'story-' + (++serial);
      record.request = requestId; visualState(true);
      clearTimeout(record.timer);
      record.timer = setTimeout(() => {
        if (currentFrame === record && record.request === requestId) say('The dashboard is taking longer than expected. Retry or continue reading.');
      }, 30000);
      record.frame.contentWindow.postMessage({type: 'dashboard:applyState', version: 1,
        viewId: record.viewId, requestId, state: record.state}, location.origin);
    }
    window.addEventListener('message', event => {
      if (event.origin !== location.origin || event.data?.version !== 1) return;
      const record = Array.from(frames.values()).find(r => r.frame.contentWindow === event.source && r.viewId === event.data.viewId);
      if (!record) return;
      if (event.data.type === 'dashboard:ready') {
        record.ready = true; send(record);
      } else if (event.data.type === 'dashboard:stateApplied' && record === currentFrame &&
                 event.data.requestId === record.request && event.data.phase === 'complete') {
        clearTimeout(record.timer);
        if (!event.data.superseded) visualState(false, !event.data.success);
        if (!event.data.superseded) say(event.data.success ? '' : (event.data.error || 'The dashboard filters could not be applied.'));
      }
    });
    function dashboard(data, state) {
      if (!pane || !data) return;
      let record = frames.get(data.view_id);
      if (!record) {
        const frame = document.createElement('iframe');
        frame.title = data.title || 'Dashboard'; frame.allowFullscreen = true;
        record = {frame, viewId: data.view_id, ready: false};
        frames.set(data.view_id, record); pane.append(frame);
        frame.addEventListener('load', () => frame.contentWindow.postMessage({type: 'dashboard:hello', version: 1}, location.origin));
        frame.src = data.url;
      }
      currentFrame = record; visualState(true);
      frames.forEach(r => {r.frame.hidden = r !== record; if (r !== record) clearTimeout(r.timer);});
      record.state = state || data.state || {filters: [], widgetId: null};
      record.touched = Date.now();
      clearTimeout(record.timer);
      if (record.ready) send(record);
      else record.timer = setTimeout(() => {if (currentFrame === record) say('This dashboard is unavailable or still loading. Open it to check access.');}, 30000);
      // Keep adjacent dashboards warm without retaining an unbounded number of applications.
      if (frames.size > 3) {
        const oldest = Array.from(frames.values()).filter(r => r !== record).sort((a, b) => a.touched - b.touched)[0];
        oldest.frame.remove(); clearTimeout(oldest.timer); frames.delete(oldest.viewId);
      }
      const link = root.querySelector('.storymap-dashboard-link');
      if (link) link.href = data.url.replace(/\/embed$/, '');
    }
    function activate(index, force) {
      if (index === active && !force) return;
      if (index !== active) root.querySelectorAll('video, audio').forEach(element => element.pause());
      active = index;
      placeMedia();
      const scene = config.scenes[index];
      if (!scene) return;
      say('');
      const presentation = scene.presentation || 'auto';
      root.dataset.textSide = scene.composition?.text_side || 'left';
      root.style.setProperty('--story-text-width', (scene.composition?.text_width || 35) + '%');
      const hasMap = scene.sources.length > 0 && !['dashboard', 'full', 'media'].includes(presentation);
      const hasDashboard = scene.dashboards?.length > 0 && !['map', 'full', 'media'].includes(presentation);
      root.classList.toggle('has-dashboard', !!hasDashboard);
      root.classList.toggle('has-combined-visuals', !!(hasMap && hasDashboard));
      chooseVisual();
      if (mapPane) mapPane.hidden = !hasMap;
      if (pane) pane.hidden = !hasDashboard;
      root.classList.toggle('is-full-section', scene.layout === 'full');
      if (hasDashboard) dashboard(scene.dashboards[0]);
      else {if (currentFrame) clearTimeout(currentFrame.timer); currentFrame = null; visualState(false);}
      if ((presentation === 'combined' && (!hasMap || !hasDashboard)) ||
          (presentation === 'map' && !hasMap) || (presentation === 'dashboard' && !hasDashboard))
        say('Add the missing visualization to complete this section template.');
    }
    function reference(ref, index) {
      const scene = config.scenes[index];
      if (!scene) return;
      activate(index);
      let sourceIndex = scene.sources.findIndex(s => s.sourceId === ref.source_id);
      let stepIndex = null;
      if (ref.slide_id) {
        sourceIndex = scene.sources.findIndex(s => (!ref.source_id || s.sourceId === ref.source_id) && (s.slideIds || []).includes(ref.slide_id));
        if (sourceIndex >= 0) stepIndex = scene.sources[sourceIndex].slideIds.indexOf(ref.slide_id);
      }
      if (ref.source_id || ref.slide_id) {
        if (sourceIndex < 0) say('This map reference is no longer available.');
        else options.scheduleApply(index, sourceIndex, stepIndex);
      }
      if (ref.dashboard_id) {
        const target = (scene.dashboards || []).find(d => d.id === ref.dashboard_id);
        if (target) {
          dashboard(target, ref.state);
          if (compact.matches) chooseVisual('dashboard');
        }
        else say('This dashboard reference is no longer available.');
      }
    }
    root.addEventListener('click', event => {
      const link = event.target.closest('a[href^="#story-ref-"]');
      if (!link) return;
      event.preventDefault();
      const card = link.closest('.storymap-card');
      const index = Number(card.dataset.sceneIndex);
      const ref = (config.scenes[index].references || []).find(r => '#story-ref-' + r.id === link.getAttribute('href'));
      if (ref) {options.activateCard(card); reference(ref, index);}
      else say('This narrative reference is no longer available.');
    });
    function enter(element) {
      const card = element.closest('.storymap-card');
      if (!card) return;
      const index = Number(card.dataset.sceneIndex);
      if (!card.classList.contains('is-active')) options.activateCard(card);
      activate(index, true);
      if (!element.classList.contains('storymap-image-trigger')) options.deactivateImage();
      if (element.classList.contains('storymap-step')) options.activateStep(element);
      if (element.classList.contains('storymap-image-trigger')) options.activateImage(element);
      const refs = config.scenes[index].references || [];
      for (const link of element.querySelectorAll('a[href^="#story-ref-"]')) {
        const ref = refs.find(r => r.on_enter && '#story-ref-' + r.id === link.getAttribute('href'));
        if (ref) reference(ref, index);
      }
    }
    const stops = cards.flatMap(card => {
      if (config.scenes[Number(card.dataset.sceneIndex)].presentation === 'media' || config.scenes[Number(card.dataset.sceneIndex)].composedStep) return [card];
      const content = Array.from(card.querySelector('.storymap-card-body').children).filter(el =>
        el.matches('.section-content, .storymap-step, .storymap-card-media, .storymap-image-trigger'));
      return content.length ? content : [card];
    });
    const navigation = root.querySelector('.storymap-slide-controls');
    const indexSelect = navigation?.querySelector('select');
    function show(index, scroll, automatic) {
      if (!automatic) playback?.pause();
      if (!slides || !stops.length) return;
      slideIndex = Math.max(0, Math.min(stops.length - 1, index));
      const target = stops[slideIndex], card = target.closest('.storymap-card');
      cards.forEach(c => {c.hidden = c !== card;});
      stops.forEach(el => {if (!el.matches('.storymap-card')) el.hidden = el !== target;});
      const scene = config.scenes[Number(card.dataset.sceneIndex)];
      const waiting = [];
      if (options.mapPending?.() && scene.sources?.length && !['dashboard', 'full', 'media'].includes(scene.presentation)) waiting.push('map');
      if (scene.dashboards?.length && !['map', 'full', 'media'].includes(scene.presentation)) waiting.push('dashboard');
      playback?.step(Number(target.dataset.duration || scene.composition?.duration || 10), slideIndex === stops.length - 1, waiting);
      enter(target);
      if (indexSelect) indexSelect.value = String(slideIndex);
      navigation.querySelector('[data-direction="-1"]').disabled = slideIndex === 0;
      navigation.querySelector('[data-direction="1"]').disabled = slideIndex === stops.length - 1;
      navigation.querySelector('[role="status"]').textContent = (slideIndex + 1) + ' / ' + stops.length;
      if (scroll) root.scrollIntoView({block: 'start', behavior: 'auto'});
    }
    if (slides && navigation) {
      root.classList.add('is-slides'); navigation.hidden = false;
      stops.forEach((el, i) => {
        const option = document.createElement('option'); option.value = i;
        option.textContent = (i + 1) + '. ' + (el.querySelector('h2,h3')?.textContent || el.closest('.storymap-card')?.querySelector('h2')?.textContent || el.textContent).trim().slice(0, 80);
        indexSelect.append(option);
      });
      indexSelect.addEventListener('change', () => show(Number(indexSelect.value)));
      navigation.querySelectorAll('[data-direction]').forEach(button => button.addEventListener('click', () => show(slideIndex + Number(button.dataset.direction))));
      document.addEventListener('keydown', event => {
        if (!['ArrowLeft', 'ArrowRight'].includes(event.key) || event.altKey || event.ctrlKey || event.metaKey ||
            event.target.closest('input,textarea,select,[contenteditable=true]') || root.getBoundingClientRect().top > innerHeight) return;
        event.preventDefault(); show(slideIndex + (event.key === 'ArrowRight' ? 1 : -1));
      });
      const play = navigation.querySelector('[data-playback]') || document.createElement('button');
      if (!play.isConnected) {play.type = 'button'; play.dataset.playback = ''; play.textContent = 'Play'; navigation.append(play);}
      playback = new window.StoryPlayback({
        advance: () => show(slideIndex + 1, false, true),
        changed: playing => {play.textContent = playing ? 'Pause' : 'Play'; play.setAttribute('aria-pressed', String(playing));}
      });
      play.addEventListener('click', () => playback.toggle());
      root.addEventListener('story:map-state', event => {
        const scene = config.scenes[active];
        if (scene?.sources?.length && !['dashboard', 'full', 'media'].includes(scene.presentation)) playback.visual('map', event.detail.pending, event.detail.error);
      });
      root.addEventListener('click', event => {if (!event.target.closest('[data-playback]')) playback.pause();}, true);
      root.addEventListener('play', () => playback.pause(), true);
      document.addEventListener('visibilitychange', () => {if (document.hidden) playback.pause();});
      window.addEventListener('pagehide', () => playback.dispose(), {once: true});
      show(0);
    }
    root.querySelectorAll('.storymap-visual-fullscreen').forEach(button => button.addEventListener('click', () => {
      const target = button.closest('.storymap-map-pane, .storymap-dashboard-pane');
      if (document.fullscreenElement) document.exitFullscreen();
      else if (target.requestFullscreen) target.requestFullscreen().catch(() => target.classList.toggle('ds-visual-expanded'));
      else target.classList.toggle('ds-visual-expanded');
    }));
    root.querySelector('.storymap-dashboard-retry')?.addEventListener('click', () => {
      if (!currentFrame) return;
      if (currentFrame.ready) send(currentFrame);
      else currentFrame.frame.src = currentFrame.frame.src;
    });
    return {activate, enter, slides, jump: direction => show(slideIndex + direction),
      showElement: el => {const index = stops.findIndex(stop => stop === el || el.contains(stop)); if (index >= 0) show(index, true);}};
  };
})();
