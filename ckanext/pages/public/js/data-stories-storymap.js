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
 *    scenes are applied by posting the share JSON (resolved through the
 *    cached CKAN endpoint) with its embedded `stories` stripped. This keeps
 *    Terria's native story panel from ever opening inside the embed, and it
 *    enables walking through multi-scene stories ("steps") on scroll.
 *    The 'applyScene' message (replaceStratum) is tried first; if the build
 *    doesn't ack it, the raw share JSON is posted (updateFromStartData).
 *
 * 2. Hash swap fallback (no "ready" within the timeout): the iframe loads
 *    '#share=...' directly and scene changes use a fragment navigation with
 *    '#clean&share=...' — no document reload. Steps are unavailable here.
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
  if (!iframe || !cards.length) return;

  var scenes = config.scenes || [];
  var terriaOrigin = config.terriaOrigin || null;
  var resolveEndpoint = config.sceneResolveEndpoint || null;
  var firstSceneUrl = null;
  var hasShareIds = false;
  for (var i = 0; i < scenes.length; i++) {
    if (!firstSceneUrl && scenes[i].sceneUrl) firstSceneUrl = scenes[i].sceneUrl;
    if (scenes[i].shareId) hasShareIds = true;
  }

  // 'idle' -> (load) -> 'pending' -> 'bridge' | 'hash'
  var mode = 'idle';
  var bridgeFallbackTimer = null;
  var desired = null;          // {sceneIndex, stepIndex|null} last activation
  var currentKey = null;       // applied scene key, avoids redundant applies
  var pendingTimer = null;     // debounce
  var applySceneSupported = null;  // null=unknown, true/false after probe
  var pendingRequestId = null;
  var requestCounter = 0;
  var shareCache = {};         // shareId -> Promise<share JSON>

  var BRIDGE_TIMEOUT_MS = 6000;
  var ACK_TIMEOUT_MS = 2500;
  var PLACEHOLDER_TIMEOUT_MS = 20000;
  var SCENE_DEBOUNCE_MS = 250;

  /* ------------------------------------------------------------------ */
  /* Iframe lazy load + placeholder                                      */
  /* ------------------------------------------------------------------ */

  function loadIframe() {
    if (mode !== 'idle') return;
    if (resolveEndpoint && hasShareIds && config.embedBaseUrl) {
      // Bridge-first: bare Terria, scenes will arrive via postMessage.
      mode = 'pending';
      iframe.src = config.embedBaseUrl;
      bridgeFallbackTimer = setTimeout(function () {
        if (mode === 'pending') enterHashMode();
      }, BRIDGE_TIMEOUT_MS);
    } else if (firstSceneUrl) {
      mode = 'hash';
      currentKey = keyFor(firstIndexWithScene(), null);
      iframe.src = firstSceneUrl;
    } else {
      return;
    }
    setTimeout(hidePlaceholder, PLACEHOLDER_TIMEOUT_MS);
  }

  function enterHashMode() {
    mode = 'hash';
    if (firstSceneUrl) {
      var target = desired && scenes[desired.sceneIndex] &&
        scenes[desired.sceneIndex].sceneUrl
          ? scenes[desired.sceneIndex]
          : null;
      currentKey = target ? keyFor(desired.sceneIndex, null)
                          : keyFor(firstIndexWithScene(), null);
      iframe.src = target ? target.sceneUrl : firstSceneUrl;
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

  if ('IntersectionObserver' in window) {
    var lazyObserver = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          loadIframe();
          lazyObserver.disconnect();
        }
      });
    }, { rootMargin: '1200px 0px' });
    lazyObserver.observe(root);
  } else {
    loadIframe();
  }

  /* ------------------------------------------------------------------ */
  /* postMessage bridge                                                  */
  /* ------------------------------------------------------------------ */

  window.addEventListener('message', function (event) {
    if (terriaOrigin && event.origin !== terriaOrigin) return;

    if (event.data === 'ready') {
      hidePlaceholder();
      if (mode === 'pending') {
        mode = 'bridge';
        if (bridgeFallbackTimer) clearTimeout(bridgeFallbackTimer);
        // Allow-origin handshake (harmless if already trusted as parent).
        try {
          iframe.contentWindow.postMessage(
            { allowOrigin: window.location.origin }, '*');
        } catch (e) { /* ignore */ }
        var target = desired || { sceneIndex: firstIndexWithScene(), stepIndex: null };
        if (target.sceneIndex >= 0) applyState(target.sceneIndex, target.stepIndex);
      }
    } else if (event.data && event.data.type === 'sceneApplied') {
      applySceneSupported = true;
      if (event.data.requestId === pendingRequestId) pendingRequestId = null;
      root.classList.remove('is-switching');
    }
  });

  function fetchShare(shareId) {
    if (!shareCache[shareId]) {
      shareCache[shareId] = fetch(
        resolveEndpoint.replace('__ID__', encodeURIComponent(shareId)),
        { credentials: 'same-origin' }
      ).then(function (resp) {
        if (!resp.ok) throw new Error('share resolve failed: ' + resp.status);
        return resp.json();
      });
      // Don't cache failures.
      shareCache[shareId].catch(function () { delete shareCache[shareId]; });
    }
    return shareCache[shareId];
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

  function postApply(shareData) {
    root.classList.add('is-switching');
    if (applySceneSupported === false) {
      postRaw(shareData);
      return;
    }
    var requestId = 'sm-' + (++requestCounter);
    pendingRequestId = requestId;
    try {
      iframe.contentWindow.postMessage({
        type: 'applyScene',
        shareData: shareData,
        requestId: requestId
      }, terriaOrigin || '*');
    } catch (e) {
      postRaw(shareData);
      return;
    }
    setTimeout(function () {
      if (applySceneSupported === null && pendingRequestId === requestId) {
        // Build without the applyScene handler: fall back to the generic
        // start-data path (updateFromStartData) for this and later scenes.
        applySceneSupported = false;
        pendingRequestId = null;
        postRaw(shareData);
      }
    }, ACK_TIMEOUT_MS);
  }

  function postRaw(shareData) {
    try {
      iframe.contentWindow.postMessage(shareData, terriaOrigin || '*');
    } catch (e) { /* ignore */ }
    setTimeout(function () { root.classList.remove('is-switching'); }, 1500);
  }

  /* ------------------------------------------------------------------ */
  /* Scene application                                                   */
  /* ------------------------------------------------------------------ */

  function keyFor(sceneIndex, stepIndex) {
    return sceneIndex + ':' + (stepIndex === null || stepIndex === undefined
      ? 'base' : stepIndex);
  }

  function applyState(sceneIndex, stepIndex) {
    var scene = scenes[sceneIndex];
    if (!scene) return;
    var key = keyFor(sceneIndex, stepIndex);
    if (key === currentKey) return;

    if (mode === 'bridge' && scene.shareId) {
      currentKey = key;
      fetchShare(scene.shareId).then(function (share) {
        if (currentKey !== key) return; // superseded while fetching
        var shareData;
        if (stepIndex !== null && stepIndex !== undefined) {
          var story = extractStories(share)[stepIndex];
          if (!story || !story.shareData) return;
          shareData = stripStories(story.shareData);
        } else {
          shareData = stripStories(share);
        }
        postApply(shareData);
      }).catch(function () {
        if (currentKey === key) currentKey = null;
        if ((stepIndex === null || stepIndex === undefined) && scene.sceneUrl) {
          applyHash(scene.sceneUrl, key);
        }
      });
      return;
    }

    if (mode === 'hash' || mode === 'bridge') {
      // No share id (e.g. '#start=' links) or no bridge: hash swap.
      // Steps need the bridge; the base scene is the best we can do here.
      if (stepIndex !== null && stepIndex !== undefined) return;
      if (scene.sceneUrl) applyHash(scene.sceneUrl, key);
      return;
    }

    // 'pending' or 'idle': remembered in `desired`, applied once ready.
  }

  function applyHash(url, key) {
    currentKey = key;
    // '#clean&' empties Terria's accumulated initSources before the new
    // share is applied; already-loaded catalog models stay in memory.
    var swapUrl = url.replace('#', '#clean&');
    root.classList.add('is-switching');
    try {
      // Cross-origin Location.replace is allowed and, unlike setting
      // iframe.src, does not push a browser history entry.
      iframe.contentWindow.location.replace(swapUrl);
    } catch (e) {
      iframe.src = swapUrl;
    }
    setTimeout(function () { root.classList.remove('is-switching'); }, 1500);
  }

  // Sub-scene tab buttons carry a full share URL.
  function applySceneUrl(url) {
    if (!url) return;
    var match = url.match(/[#&]share=([A-Za-z0-9_-]+)/);
    var key = 'url:' + url;
    if (key === currentKey) return;
    if (mode === 'bridge' && match && resolveEndpoint) {
      currentKey = key;
      fetchShare(match[1]).then(function (share) {
        if (currentKey !== key) return;
        postApply(stripStories(share));
      }).catch(function () {
        if (currentKey === key) currentKey = null;
        applyHash(url, key);
      });
    } else if (mode === 'hash' || mode === 'bridge') {
      applyHash(url, key);
    }
  }

  function scheduleApply(sceneIndex, stepIndex) {
    desired = { sceneIndex: sceneIndex, stepIndex: stepIndex };
    if (pendingTimer) clearTimeout(pendingTimer);
    pendingTimer = setTimeout(function () {
      pendingTimer = null;
      applyState(sceneIndex, stepIndex);
    }, SCENE_DEBOUNCE_MS);
  }

  /* ------------------------------------------------------------------ */
  /* Active card / step detection                                        */
  /* ------------------------------------------------------------------ */

  function activateCard(card) {
    cards.forEach(function (c) { c.classList.toggle('is-active', c === card); });
    var index = parseInt(card.getAttribute('data-scene-index'), 10);
    dots.forEach(function (dot, dotIndex) {
      dot.classList.toggle('is-active', dotIndex === index);
    });
    var scene = scenes[index];
    if (!scene) return;
    if (scene.steps > 1) {
      // The step observer drives the map inside this chapter.
      return;
    }
    if (scene.sceneUrl || scene.shareId) {
      scheduleApply(index, null);
    }
    // Cards without a scene keep the previous map view.
  }

  function activateStep(stepEl) {
    var sceneIndex = parseInt(stepEl.getAttribute('data-scene-index'), 10);
    var stepIndex = parseInt(stepEl.getAttribute('data-step-index'), 10);
    steps.forEach(function (s) {
      if (parseInt(s.getAttribute('data-scene-index'), 10) === sceneIndex) {
        s.classList.toggle('is-active', s === stepEl);
      }
    });
    scheduleApply(sceneIndex, stepIndex);
  }

  if ('IntersectionObserver' in window) {
    var activeObserver = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        if (entry.target.classList.contains('storymap-step')) {
          activateStep(entry.target);
        } else {
          activateCard(entry.target);
        }
      });
    }, { rootMargin: '-45% 0px -45% 0px', threshold: 0 });
    cards.forEach(function (card) { activeObserver.observe(card); });
    steps.forEach(function (step) { activeObserver.observe(step); });
  } else {
    cards.forEach(function (card) { card.classList.add('is-active'); });
  }

  if (cards.length) activateCard(cards[0]);

  /* ------------------------------------------------------------------ */
  /* Sub-scene tabs + progress dots                                      */
  /* ------------------------------------------------------------------ */

  root.addEventListener('click', function (event) {
    var btn = event.target.closest('.scene-tab-btn');
    if (btn) {
      var group = btn.parentElement.querySelectorAll('.scene-tab-btn');
      Array.prototype.forEach.call(group, function (b) {
        b.classList.toggle('is-active', b === btn);
      });
      applySceneUrl(btn.getAttribute('data-scene-url'));
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
