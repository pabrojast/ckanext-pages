/**
 * Data Stories — Story Map (scrollytelling) viewer
 *
 * One sticky Terria iframe + scrolling narrative cards. When a card (or a
 * story step inside it) becomes active, the map switches scene.
 *
 * Scene application, in order of preference:
 *
 * 1. postMessage bridge (auto-detected via the "ready" message Terria posts
 *    to its parent): the iframe loads a BARE Terria URL — no '#share=' — and
 *    scenes are applied by posting the share JSON (fetched from the Terria
 *    instance, CKAN proxy as fallback) with its embedded `stories` stripped.
 *    This keeps Terria's native story panel from ever opening inside the
 *    embed, and it enables walking through multi-scene stories ("steps") on
 *    scroll — including steps living on different map sources (tabs) of the
 *    same chapter. Only the 'applyScene' message (replaceStratum) is used,
 *    and only while the build acks it with 'sceneApplied': raw start data
 *    (updateFromStartData) proved unreliable for COG layers. A single missed
 *    ack degrades just that apply to hash navigation; only two consecutive
 *    misses latch the bridge data path off (a later "ready" — e.g. after a
 *    reboot — re-arms the probe).
 *
 * 2. Hash swap fallback (no "ready" within the timeout): the iframe loads
 *    '#share=...' directly and scene changes use a fragment navigation with
 *    '#clean&share=...' — no document reload. Steps show the base scene.
 *
 * Key bookkeeping: `appliedKey` is what the map is (believed to be) showing,
 * `inFlightKey` is a bridge apply awaiting its ack. Keys are only promoted
 * to `appliedKey` on ack (bridge) or fire-and-forget navigation (hash), so a
 * failed apply leaves the state retryable instead of wedged.
 */

(function () {
  'use strict';

  var configEl = document.getElementById('storymap-config');
  var root = document.getElementById('storymap');
  if (!configEl || !root) return;

  var config;
  try {
    config = JSON.parse(configEl.textContent);
  } catch (e) {
    return;
  }

  var iframe = root.querySelector('.storymap-iframe');
  var placeholder = root.querySelector('.storymap-placeholder');
  var cards = Array.prototype.slice.call(root.querySelectorAll('.storymap-card'));
  var steps = Array.prototype.slice.call(root.querySelectorAll('.storymap-step'));
  var dots = Array.prototype.slice.call(root.querySelectorAll('.storymap-dot'));
  var imageTriggers = Array.prototype.slice.call(
    root.querySelectorAll('.storymap-image-trigger'));
  var mediaImage = root.querySelector('.storymap-media-image');
  if (!cards.length) return;

  var scenes = config.scenes || [];
  var terriaOrigin = config.terriaOrigin || null;
  var resolveEndpoint = config.sceneResolveEndpoint || null;
  var firstSceneUrl = null;
  var hasBridgeSources = false;
  for (var i = 0; i < scenes.length; i++) {
    if (!Array.isArray(scenes[i].sources) || !scenes[i].sources.length) {
      scenes[i].sources = scenes[i].sceneUrl ? [{
        sceneUrl: scenes[i].sceneUrl,
        shareId: scenes[i].shareId || null,
        startData: scenes[i].startData || null
      }] : [];
    }
    scenes[i].sources.forEach(function (source) {
      if (!firstSceneUrl && source.sceneUrl) firstSceneUrl = source.sceneUrl;
      if (source.shareId || source.startData) hasBridgeSources = true;
    });
  }

  // 'idle' -> (load) -> 'pending' -> 'bridge' | 'hash'
  var mode = 'idle';
  var bridgeFallbackTimer = null;
  var desired = null;          // {sceneIndex, sourceIndex, stepIndex|null}
  var appliedKey = null;       // key the map is (believed to be) showing
  var inFlightKey = null;      // bridge apply awaiting its ack, else null
  var pendingTimer = null;     // debounce
  var manualSceneChapter = null;  // chapter index whose tab is pinned (null=none)
  var manualSourceIndex = null;
  var applySceneSupported = null;  // null=unknown, true/false after probe
  var pendingRequestId = null;
  var pendingKey = null;       // key owned by pendingRequestId
  var ackMisses = 0;           // consecutive missed acks (2 latch hash mode)
  var switchSeq = 0;           // invalidates stale veil-clearing timers
  var requestCounter = 0;
  var shareCache = {};         // shareId -> Promise<share JSON>

  // Cold Terria boots take ~10s before posting "ready"; a short timeout
  // here would lock the viewer into hash mode for the whole page life
  // (late "ready" upgrades to bridge, but the cheap path is waiting).
  var BRIDGE_TIMEOUT_MS = 12000;
  var ACK_TIMEOUT_MS = 2500;
  var PLACEHOLDER_TIMEOUT_MS = 20000;
  var SCENE_DEBOUNCE_MS = 250;

  /* ------------------------------------------------------------------ */
  /* Iframe lazy load + placeholder                                      */
  /* ------------------------------------------------------------------ */

  function loadIframe() {
    if (!iframe || mode !== 'idle') return;
    if (hasBridgeSources && config.embedBaseUrl) {
      // Bridge-first: bare Terria, scenes will arrive via postMessage.
      mode = 'pending';
      iframe.src = config.embedBaseUrl;
      bridgeFallbackTimer = setTimeout(function () {
        if (mode === 'pending') enterHashMode();
      }, BRIDGE_TIMEOUT_MS);
    } else if (firstSceneUrl) {
      mode = 'hash';
      appliedKey = keyFor(firstIndexWithScene(), 0, null);
      iframe.src = firstSceneUrl;
    } else {
      return;
    }
    setTimeout(hidePlaceholder, PLACEHOLDER_TIMEOUT_MS);
  }

  function enterHashMode() {
    mode = 'hash';
    if (firstSceneUrl) {
      var target = desired
        ? sourceFor(desired.sceneIndex, desired.sourceIndex)
        : null;
      appliedKey = target && target.sceneUrl
        ? keyFor(desired.sceneIndex, desired.sourceIndex, null)
        : keyFor(firstIndexWithScene(), 0, null);
      iframe.src = target && target.sceneUrl ? target.sceneUrl : firstSceneUrl;
    }
  }

  function firstIndexWithScene() {
    for (var j = 0; j < scenes.length; j++) {
      if (scenes[j].sceneUrl) return j;
    }
    return -1;
  }

  function hidePlaceholder() {
    if (placeholder && !placeholder.classList.contains('is-hidden')) {
      placeholder.classList.add('is-hidden');
    }
  }

  // Shows/hides the "Loading scene…" pill and the map veil. A failsafe
  // timer clears it even when no completion signal ever arrives; every
  // turn-on bumps switchSeq so a stale timer (an older hash swap, an old
  // failsafe) can never drop the veil of a newer in-flight apply.
  var switchingFailsafe = null;
  function setSwitching(on) {
    root.classList.toggle('is-switching', on);
    if (on) switchSeq++;
    var seq = switchSeq;
    if (switchingFailsafe) clearTimeout(switchingFailsafe);
    switchingFailsafe = null;
    if (on) {
      switchingFailsafe = setTimeout(function () {
        if (seq === switchSeq) root.classList.remove('is-switching');
      }, 8000);
    }
  }

  function clearSwitchingAfter(ms) {
    var seq = switchSeq;
    setTimeout(function () {
      if (seq === switchSeq) setSwitching(false);
    }, ms);
  }

  // The storymap IS the page's primary content and a cold Terria boot takes
  // ~10s: start it immediately so it loads while the reader is on the hero.
  loadIframe();

  /* ------------------------------------------------------------------ */
  /* postMessage bridge                                                  */
  /* ------------------------------------------------------------------ */

  // Warm the share-JSON cache for every scene so scrolling never waits on
  // a share fetch round-trip. Sequential, error-tolerant (failed fetches
  // self-evict from the cache and retry on real activation).
  var sharesWarmed = false;
  function warmShares() {
    if (sharesWarmed) return;
    sharesWarmed = true;
    setTimeout(function () {
      var chain = Promise.resolve();
      scenes.forEach(function (scene) {
        (scene.sources || []).forEach(function (source) {
          if (!source.shareId) return;
          chain = chain.then(function () {
            return fetchShare(source.shareId, source.sceneUrl)
              .catch(function () {});
          });
        });
      });
    }, 1500);
  }

  window.addEventListener('message', function (event) {
    if (!iframe) return;
    if (terriaOrigin && event.origin !== terriaOrigin) return;

    if (event.data === 'ready') {
      hidePlaceholder();
      // A "ready" means a (re)booted Terria: reset the ack bookkeeping and
      // re-arm the bridge probe even if a previous boot latched hash mode.
      ackMisses = 0;
      if (applySceneSupported === false) applySceneSupported = null;
      // 'pending': the bare embed booted in time. 'hash': Terria booted
      // slower than the fallback timer (or a src reset rebooted it) — a
      // late "ready" still proves the bridge works, so upgrade; steps and
      // clean scene applies only exist on the bridge. applyState() dedupes
      // by key, so an already-correct hash-loaded scene isn't re-applied.
      if (mode === 'pending' || (mode === 'hash' && hasBridgeSources)) {
        mode = 'bridge';
        if (bridgeFallbackTimer) clearTimeout(bridgeFallbackTimer);
        // Allow-origin handshake (harmless if already trusted as parent).
        try {
          iframe.contentWindow.postMessage(
            { allowOrigin: window.location.origin }, '*');
        } catch (e) { /* ignore */ }
        var target = desired || {
          sceneIndex: firstIndexWithScene(), sourceIndex: 0, stepIndex: null
        };
        if (target.sceneIndex >= 0) {
          applySource(target.sceneIndex, target.sourceIndex, target.stepIndex);
        }
        warmShares();
      }
    } else if (event.data && event.data.type === 'sceneApplied') {
      // Two-phase ack: 'received' arrives immediately (capability proof,
      // before the build awaits the heavy applyInitData calls), 'complete'
      // when the scene is fully applied. Builds predating the phases send a
      // single ack with no 'phase' — treated as completion.
      applySceneSupported = true;
      ackMisses = 0;
      if (event.data.phase === 'received') {
        // Keep the pill up and re-arm its failsafe for the apply itself.
        if (event.data.requestId === pendingRequestId) setSwitching(true);
        return;
      }
      if (event.data.requestId === pendingRequestId) {
        // Only a confirmed completion promotes the key: a failed or
        // superseded apply must stay retryable.
        appliedKey = pendingKey;
        inFlightKey = null;
        pendingRequestId = null;
        pendingKey = null;
        setSwitching(false);
      } else if (!pendingRequestId) {
        // Stale/unsolicited completion with nothing in flight: just make
        // sure the veil isn't stuck.
        setSwitching(false);
      }
    }
  });

  // Terria's share API base derived from the share URL itself, e.g.
  // 'https://host/terria/#share=g-x' -> 'https://host/terria/api/v1/share/'.
  // This works regardless of CKAN's configured Terria base URL.
  function apiBaseFromUrl(url) {
    var base = url.split('#')[0].split('?')[0];
    if (base.charAt(base.length - 1) !== '/') base += '/';
    return base + 'api/v1/share/';
  }

  function asJson(resp) {
    if (!resp.ok) throw new Error('share resolve failed: ' + resp.status);
    return resp.json();
  }

  function fetchShare(shareId, sceneUrl) {
    var cacheKey = shareId;
    if (!shareCache[cacheKey]) {
      // Direct fetch from the Terria instance (its share API sends open
      // CORS headers); the CKAN caching proxy is the fallback.
      var direct = sceneUrl
        ? fetch(apiBaseFromUrl(sceneUrl) + encodeURIComponent(shareId))
            .then(asJson)
        : Promise.reject(new Error('no scene url'));
      shareCache[cacheKey] = direct.catch(function () {
        if (!resolveEndpoint) throw new Error('share resolve failed');
        return fetch(
          resolveEndpoint.replace('__ID__', encodeURIComponent(shareId)),
          { credentials: 'same-origin' }
        ).then(asJson);
      });
      // Don't cache failures.
      shareCache[cacheKey].catch(function () { delete shareCache[cacheKey]; });
    }
    return shareCache[cacheKey];
  }

  function stripStories(share) {
    var out = { version: share.version || '8.0.0', initSources: [] };
    (share.initSources || []).forEach(function (src) {
      if (src && typeof src === 'object') {
        var copy = {};
        for (var k in src) {
          if (Object.prototype.hasOwnProperty.call(src, k) && k !== 'stories') {
            copy[k] = src[k];
          }
        }
        out.initSources.push(copy);
      } else if (typeof src === 'string') {
        out.initSources.push(src);
      }
    });
    return out;
  }

  function extractStories(share) {
    var sources = (share && share.initSources) || [];
    for (var j = 0; j < sources.length; j++) {
      if (sources[j] && typeof sources[j] === 'object' &&
          Array.isArray(sources[j].stories) && sources[j].stories.length) {
        return sources[j].stories;
      }
    }
    return [];
  }

  // 'fallback' is the caller-supplied degradation (a hash navigation with
  // the caller's key/superseded semantics); it runs when the build doesn't
  // ack 'applyScene'. Raw start data (updateFromStartData) is deliberately
  // NOT used — it fails to render COG layers on stock Terria builds.
  function postApply(shareData, key, fallback) {
    if (!iframe) return;
    setSwitching(true);
    if (applySceneSupported === false) {
      fallback();
      return;
    }
    var requestId = 'sm-' + (++requestCounter);
    pendingRequestId = requestId;
    pendingKey = key;
    try {
      iframe.contentWindow.postMessage({
        type: 'applyScene',
        shareData: shareData,
        requestId: requestId
      }, terriaOrigin || '*');
    } catch (e) {
      // contentWindow was inaccessible — not evidence the handler is
      // missing, so don't latch applySceneSupported here.
      if (pendingRequestId === requestId) {
        pendingRequestId = null;
        pendingKey = null;
      }
      fallback();
      return;
    }
    setTimeout(function () {
      if (pendingRequestId !== requestId) return; // acked or superseded
      pendingRequestId = null;
      pendingKey = null;
      ackMisses++;
      // One dropped message (heavy first scene, slow build) only degrades
      // THIS apply; two consecutive misses during the probe phase mean the
      // build has no applyScene handler — latch hash mode. A later "ready"
      // (fresh boot) re-arms the probe.
      if (applySceneSupported === null && ackMisses >= 2) {
        applySceneSupported = false;
      }
      fallback();
    }, ACK_TIMEOUT_MS);
  }

  /* ------------------------------------------------------------------ */
  /* Scene application                                                   */
  /* ------------------------------------------------------------------ */

  function sourceFor(sceneIndex, sourceIndex) {
    var scene = scenes[sceneIndex];
    if (!scene || !scene.sources) return null;
    return scene.sources[sourceIndex || 0] || null;
  }

  function keyFor(sceneIndex, sourceIndex, stepIndex) {
    return sceneIndex + ':' + (sourceIndex || 0) + ':' +
      (stepIndex === null || stepIndex === undefined ? 'base' : stepIndex);
  }

  function dataForSource(source) {
    if (source.startData) return Promise.resolve(source.startData);
    if (source.shareId) return fetchShare(source.shareId, source.sceneUrl);
    return Promise.reject(new Error('scene source has no bridge data'));
  }

  function applyState(sceneIndex, sourceIndex, stepIndex) {
    var scene = scenes[sceneIndex];
    if (!scene) return;

    // A manually selected tab pins its chapter: ignore scroll-driven applies.
    if (manualSceneChapter !== null && sceneIndex === manualSceneChapter) return;
    applySource(sceneIndex, sourceIndex, stepIndex);
  }

  function applySource(sceneIndex, sourceIndex, stepIndex) {
    var source = sourceFor(sceneIndex, sourceIndex);
    if (!source) return;
    var key = keyFor(sceneIndex, sourceIndex, stepIndex);
    if (key === appliedKey || key === inFlightKey) return;

    if (mode === 'bridge' && (source.shareId || source.startData) &&
        applySceneSupported !== false) {
      inFlightKey = key;
      setSwitching(true);
      // Hash degradation under the BASE key, even for steps — otherwise
      // every later step of the chapter re-fires the same navigation.
      var fallbackKey = keyFor(sceneIndex, sourceIndex, null);
      var fallback = function () {
        if (inFlightKey !== key) return; // superseded while probing
        inFlightKey = null;
        if (source.sceneUrl) {
          applyHash(source.sceneUrl, fallbackKey);
        } else {
          // Nothing to degrade to; appliedKey still names what is really
          // on screen, so re-entering this target retries cleanly.
          setSwitching(false);
        }
      };
      dataForSource(source).then(function (share) {
        if (inFlightKey !== key) return; // superseded while fetching
        var shareData;
        if (stepIndex !== null && stepIndex !== undefined) {
          var story = extractStories(share)[stepIndex];
          shareData = story && story.shareData
            ? stripStories(story.shareData)
            : stripStories(share);
        } else {
          shareData = stripStories(share);
        }
        postApply(shareData, key, fallback);
      }).catch(fallback);
      return;
    }

    if (mode === 'hash' || mode === 'bridge') {
      // No working bridge: hash swap. Steps cannot be addressed by URL, so
      // each source's base scene is what a step can show (source changes
      // still navigate: the base key differs per source).
      if (stepIndex !== null && stepIndex !== undefined) {
        var baseKey = keyFor(sceneIndex, sourceIndex, null);
        if (source.sceneUrl && appliedKey !== baseKey) {
          applyHash(source.sceneUrl, baseKey);
        }
        return;
      }
      if (source.sceneUrl) applyHash(source.sceneUrl, key);
      return;
    }

    // 'pending' or 'idle': remembered in `desired`, applied once ready.
  }

  function applyHash(url, key) {
    if (!iframe) return;
    // Fragment navigation into a cross-origin iframe has no observable
    // completion, so the key is claimed up front and the veil cleared on a
    // timer — that is the honest ceiling for this path.
    appliedKey = key;
    inFlightKey = null;
    // '#clean&' empties Terria's accumulated initSources before the new
    // share is applied; already-loaded catalog models stay in memory.
    var swapUrl = url.replace('#', '#clean&');
    setSwitching(true);
    try {
      // Cross-origin Location.replace is allowed and, unlike setting
      // iframe.src, does not push a browser history entry.
      iframe.contentWindow.location.replace(swapUrl);
    } catch (e) {
      iframe.src = swapUrl;
    }
    clearSwitchingAfter(2500);
  }

  function scheduleApply(sceneIndex, sourceIndex, stepIndex) {
    desired = {
      sceneIndex: sceneIndex,
      sourceIndex: sourceIndex || 0,
      stepIndex: stepIndex
    };
    if (pendingTimer) clearTimeout(pendingTimer);
    pendingTimer = setTimeout(function () {
      pendingTimer = null;
      applyState(sceneIndex, sourceIndex || 0, stepIndex);
    }, SCENE_DEBOUNCE_MS);
  }

  /* ------------------------------------------------------------------ */
  /* Active card / step detection                                        */
  /* ------------------------------------------------------------------ */

  // Image blocks: while a trigger is the active scroll stop the sticky
  // panel shows its image full-bleed over the map. The scene machinery
  // keeps running underneath — the overlay is purely visual.
  function activateImage(trigger) {
    var imageCard = trigger.closest('.storymap-card');
    if (imageCard && imageCard.getAttribute('data-layout') === 'full') {
      deactivateImage();
      return;
    }
    if (!mediaImage) return;
    var img = mediaImage.querySelector('img');
    var caption = mediaImage.querySelector('.storymap-media-image-caption');
    var url = trigger.getAttribute('data-image-url');
    if (img && img.getAttribute('src') !== url) img.src = url;
    if (img) img.alt = trigger.getAttribute('data-image-alt') || '';
    if (caption) {
      caption.textContent = trigger.getAttribute('data-image-caption') || '';
    }
    mediaImage.classList.add('is-active');
    mediaImage.setAttribute('aria-hidden', 'false');
    imageTriggers.forEach(function (t) {
      t.classList.toggle('is-active', t === trigger);
    });
  }

  function deactivateImage() {
    if (!mediaImage || !mediaImage.classList.contains('is-active')) return;
    // Keep the src so the fade-out still shows the image.
    mediaImage.classList.remove('is-active');
    mediaImage.setAttribute('aria-hidden', 'true');
    imageTriggers.forEach(function (t) { t.classList.remove('is-active'); });
  }

  // Keeps a chapter's tab row in sync with the source the scroll (or a
  // click) selected.
  function syncTabHighlight(sceneIndex, sourceIndex) {
    var card = root.querySelector(
      '.storymap-card[data-scene-index="' + sceneIndex + '"]');
    if (!card) return;
    var tabs = card.querySelectorAll('.scene-tab-btn');
    Array.prototype.forEach.call(tabs, function (b) {
      var si = parseInt(b.getAttribute('data-source-index'), 10);
      b.classList.toggle('is-active', si === sourceIndex);
    });
  }

  // First source of a chapter that has scroll steps (-1 when none do).
  function firstSourceWithSteps(scene) {
    var sources = scene.sources || [];
    for (var si = 0; si < sources.length; si++) {
      if ((sources[si].steps || 0) > 0) return si;
    }
    return -1;
  }

  function activateCard(card) {
    deactivateImage();
    cards.forEach(function (c) { c.classList.toggle('is-active', c === card); });
    var index = parseInt(card.getAttribute('data-scene-index'), 10);
    dots.forEach(function (dot, dotIndex) {
      dot.classList.toggle('is-active', dotIndex === index);
    });
    var scene = scenes[index];
    if (!scene) return;
    var isFull = scene.layout === 'full' || !scene.sources || !scene.sources.length;
    // Full chapters fade the media panel out but deliberately keep the last
    // scene loaded underneath: re-entering a split chapter re-applies by key.
    root.classList.toggle('is-full-section', isFull);
    // A pinned tab survives until the reader leaves its chapter.
    if (manualSceneChapter !== null) {
      if (index === manualSceneChapter) return;  // keep the pinned tab scene
      manualSceneChapter = null;                 // entered a different chapter
      manualSourceIndex = null;
    }
    if (isFull) return;
    var stepSource = firstSourceWithSteps(scene);
    // Entering a chapter fresh: sync the tab highlight to the source that
    // will drive the map (a previous pin may linger on another tab).
    syncTabHighlight(index, stepSource !== -1 ? stepSource : 0);
    if (stepSource !== -1) {
      // Jump to the chapter's first scroll step as soon as the card
      // activates (i.e. while reading its intro blocks); the step observer
      // takes over from there. keyFor() dedupes the re-apply when the step
      // centers.
      scheduleApply(index, stepSource, 0);
      return;
    }
    if (scene.sources && scene.sources.length) {
      scheduleApply(index, 0, null);
    }
  }

  function activateStep(stepEl) {
    deactivateImage();
    var sceneIndex = parseInt(stepEl.getAttribute('data-scene-index'), 10);
    var stepIndex = parseInt(stepEl.getAttribute('data-step-index'), 10);
    var sourceIndex = parseInt(stepEl.getAttribute('data-source-index'), 10);
    if (isNaN(sourceIndex)) sourceIndex = 0;
    // While a tab is pinned in this chapter, steps neither drive the map nor
    // highlight; a step in any other chapter releases the pin.
    if (manualSceneChapter !== null) {
      if (sceneIndex === manualSceneChapter) return;
      manualSceneChapter = null;
      manualSourceIndex = null;
    }
    steps.forEach(function (s) {
      if (parseInt(s.getAttribute('data-scene-index'), 10) === sceneIndex) {
        s.classList.toggle('is-active', s === stepEl);
      }
    });
    // The tab row follows the scroll through multi-map chapters.
    syncTabHighlight(sceneIndex, sourceIndex);
    scheduleApply(sceneIndex, sourceIndex, stepIndex);
  }

  if ('IntersectionObserver' in window) {
    var activeObserver = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        if (entry.target.classList.contains('storymap-image-trigger')) {
          activateImage(entry.target);
        } else if (entry.target.classList.contains('storymap-step')) {
          activateStep(entry.target);
        } else {
          activateCard(entry.target);
        }
      });
      // Asymmetric band [45%, 65%]: scrolling DOWN activates ~10vh earlier
      // (heavy layers get a head start) while scrolling up is unchanged.
    }, { rootMargin: '-45% 0px -35% 0px', threshold: 0 });
    cards.forEach(function (card) { activeObserver.observe(card); });
    steps.forEach(function (step) { activeObserver.observe(step); });
    imageTriggers.forEach(function (t) { activeObserver.observe(t); });
  } else {
    cards.forEach(function (card) { card.classList.add('is-active'); });
  }

  if (cards.length) activateCard(cards[0]);

  /* ------------------------------------------------------------------ */
  /* Prev/next block navigation (buttons + arrow keys)                   */
  /* ------------------------------------------------------------------ */

  // Scroll "stops" in DOM order: steps and image triggers; chapters with
  // neither contribute their card as the single stop.
  var stops = Array.prototype.slice.call(root.querySelectorAll(
    '.storymap-step, .storymap-image-trigger, .storymap-card'
  )).filter(function (el) {
    if (!el.classList.contains('storymap-card')) return true;
    return !el.querySelector('.storymap-step, .storymap-image-trigger');
  });

  function scrollToStop(el) {
    var reduceMotion = window.matchMedia &&
      window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    el.scrollIntoView({
      behavior: reduceMotion ? 'auto' : 'smooth',
      block: 'center'
    });
  }

  // Position is computed geometrically at jump time (nearest stop relative
  // to the viewport midline) — activation state can lag a smooth scroll.
  var lastJumpAt = 0;
  function jumpStop(direction) {
    if (!stops.length) return;
    var now = Date.now();
    if (now - lastJumpAt < 300) return; // held keys shouldn't skip stops
    lastJumpAt = now;
    var mid = window.innerHeight / 2;
    var EPS = 24;
    var i, rect, center;
    if (direction > 0) {
      for (i = 0; i < stops.length; i++) {
        rect = stops[i].getBoundingClientRect();
        center = rect.top + rect.height / 2;
        if (center > mid + EPS) return scrollToStop(stops[i]);
      }
    } else {
      for (i = stops.length - 1; i >= 0; i--) {
        rect = stops[i].getBoundingClientRect();
        center = rect.top + rect.height / 2;
        if (center < mid - EPS) return scrollToStop(stops[i]);
      }
    }
  }

  document.addEventListener('keydown', function (event) {
    if (event.key !== 'ArrowDown' && event.key !== 'ArrowUp') return;
    if (event.altKey || event.ctrlKey || event.metaKey || event.shiftKey) return;
    var active = document.activeElement;
    if (active && (/^(INPUT|TEXTAREA|SELECT)$/.test(active.tagName) ||
                   active.isContentEditable)) return;
    if (document.body.classList.contains('ds-lightbox-open')) return;
    // Only take over the arrows while the storymap spans the viewport
    // midline — everywhere else they keep their native scroll behavior.
    var rootRect = root.getBoundingClientRect();
    var midline = window.innerHeight / 2;
    if (rootRect.top > midline || rootRect.bottom < midline) return;
    event.preventDefault();
    jumpStop(event.key === 'ArrowDown' ? 1 : -1);
  });

  /* ------------------------------------------------------------------ */
  /* Sub-scene tabs + progress dots                                      */
  /* ------------------------------------------------------------------ */

  root.addEventListener('click', function (event) {
    var navBtn = event.target.closest('.storymap-nav-btn');
    if (navBtn) {
      jumpStop(navBtn.classList.contains('storymap-nav-next') ? 1 : -1);
      return;
    }

    var btn = event.target.closest('.scene-tab-btn');
    if (btn) {
      var group = btn.parentElement.querySelectorAll('.scene-tab-btn');
      Array.prototype.forEach.call(group, function (b) {
        b.classList.toggle('is-active', b === btn);
      });
      // Pin this tab's chapter so scroll-driven step applies don't revert it,
      // and cancel any step apply already queued from the last scroll.
      var tabCard = btn.closest('.storymap-card');
      if (tabCard) {
        var ci = parseInt(tabCard.getAttribute('data-scene-index'), 10);
        if (!isNaN(ci)) {
          manualSceneChapter = ci;
          manualSourceIndex = parseInt(btn.getAttribute('data-source-index'), 10);
          if (isNaN(manualSourceIndex)) manualSourceIndex = 0;
        }
      }
      if (pendingTimer) { clearTimeout(pendingTimer); pendingTimer = null; }
      desired = {
        sceneIndex: manualSceneChapter,
        sourceIndex: manualSourceIndex,
        stepIndex: null
      };
      applySource(manualSceneChapter, manualSourceIndex, null);
      return;
    }

    var dot = event.target.closest('.storymap-dot');
    if (dot) {
      var target = document.getElementById(dot.getAttribute('data-target'));
      if (target) {
        var reduceMotion = window.matchMedia &&
          window.matchMedia('(prefers-reduced-motion: reduce)').matches;
        target.scrollIntoView({
          behavior: reduceMotion ? 'auto' : 'smooth',
          block: 'center'
        });
      }
    }
  });
})();
