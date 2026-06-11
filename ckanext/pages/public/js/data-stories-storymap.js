/**
 * Data Stories — Story Map (scrollytelling) viewer
 *
 * One sticky Terria iframe + scrolling narrative cards. When a card becomes
 * active, the map switches scene. Scene changes use a fragment navigation on
 * the iframe ('#clean&share=...'), which Terria picks up via its hashchange
 * listener without reloading the document. When the Terria instance exposes
 * the postMessage bridge and 'usePostMessage' is enabled, scenes are applied
 * through 'applyScene' messages instead (clean stratum replacement).
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
  var dots = Array.prototype.slice.call(root.querySelectorAll('.storymap-dot'));
  if (!iframe || !cards.length) return;

  var scenes = config.scenes || [];
  var terriaOrigin = config.terriaOrigin || null;
  var firstSceneUrl = null;
  for (var i = 0; i < scenes.length; i++) {
    if (scenes[i].sceneUrl) { firstSceneUrl = scenes[i].sceneUrl; break; }
  }

  var iframeLoaded = false;
  var terriaReady = false;
  var currentSceneUrl = null;
  var pendingTimer = null;
  var PLACEHOLDER_TIMEOUT_MS = 20000;
  var SCENE_DEBOUNCE_MS = 250;

  /* ------------------------------------------------------------------ */
  /* Iframe lazy load + placeholder                                      */
  /* ------------------------------------------------------------------ */

  function loadIframe() {
    if (iframeLoaded || !firstSceneUrl) return;
    iframeLoaded = true;
    currentSceneUrl = firstSceneUrl;
    iframe.src = firstSceneUrl;

    // Safety net: if Terria never posts "ready" (older build, blocked
    // message), drop the placeholder anyway after a generous timeout.
    setTimeout(hidePlaceholder, PLACEHOLDER_TIMEOUT_MS);
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

  window.addEventListener('message', function (event) {
    if (terriaOrigin && event.origin !== terriaOrigin) return;
    if (event.data === 'ready') {
      terriaReady = true;
      hidePlaceholder();
      if (config.usePostMessage && iframe.contentWindow) {
        // Handshake so the bridge accepts subsequent scene messages.
        iframe.contentWindow.postMessage(
          { allowOrigin: window.location.origin }, '*');
      }
    } else if (event.data && event.data.type === 'sceneApplied') {
      root.classList.remove('is-switching');
    }
  });

  /* ------------------------------------------------------------------ */
  /* Scene switching                                                     */
  /* ------------------------------------------------------------------ */

  function toSwapUrl(url) {
    // '#clean&' empties Terria's accumulated initSources before the new
    // share is applied; already-loaded catalog models stay in memory.
    return url.replace('#', '#clean&');
  }

  function applyScene(url) {
    if (!url || url === currentSceneUrl) return;
    if (!iframeLoaded) {
      // Not loaded yet: remember the scene so the lazy observer starts
      // the iframe directly on it (no eager load from afar).
      firstSceneUrl = url;
      return;
    }
    currentSceneUrl = url;
    root.classList.add('is-switching');

    if (config.usePostMessage && terriaReady && window.fetch &&
        config.sceneResolveEndpoint) {
      applySceneViaPostMessage(url);
      return;
    }
    applySceneViaHash(url);
  }

  function applySceneViaHash(url) {
    var swapUrl = toSwapUrl(url);
    try {
      // Cross-origin Location.replace is allowed and, unlike setting
      // iframe.src, does not push a browser history entry.
      iframe.contentWindow.location.replace(swapUrl);
    } catch (e) {
      iframe.src = swapUrl;
    }
    // Hash swaps have no completion signal; clear the transition shortly.
    setTimeout(function () { root.classList.remove('is-switching'); }, 1500);
  }

  function applySceneViaPostMessage(url) {
    var match = url.match(/[#&]share=([^&]+)/);
    if (!match) { applySceneViaHash(url); return; }

    fetch(config.sceneResolveEndpoint.replace('__ID__', encodeURIComponent(match[1])))
      .then(function (resp) {
        if (!resp.ok) throw new Error('resolve failed');
        return resp.json();
      })
      .then(function (shareData) {
        iframe.contentWindow.postMessage({
          type: 'applyScene',
          shareData: shareData,
          requestId: 'scene-' + Date.now()
        }, terriaOrigin || '*');
      })
      .catch(function () { applySceneViaHash(url); });
  }

  function scheduleScene(url) {
    if (pendingTimer) clearTimeout(pendingTimer);
    pendingTimer = setTimeout(function () {
      pendingTimer = null;
      applyScene(url);
    }, SCENE_DEBOUNCE_MS);
  }

  /* ------------------------------------------------------------------ */
  /* Active card detection                                               */
  /* ------------------------------------------------------------------ */

  function activateCard(card) {
    cards.forEach(function (c) { c.classList.toggle('is-active', c === card); });
    var index = parseInt(card.getAttribute('data-scene-index'), 10);
    dots.forEach(function (dot, dotIndex) {
      dot.classList.toggle('is-active', dotIndex === index);
    });
    var scene = scenes[index];
    if (scene && scene.sceneUrl) {
      scheduleScene(scene.sceneUrl);
    }
    // Cards without a scene keep the previous map view.
  }

  if ('IntersectionObserver' in window) {
    var activeObserver = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) activateCard(entry.target);
      });
    }, { rootMargin: '-45% 0px -45% 0px', threshold: 0 });
    cards.forEach(function (card) { activeObserver.observe(card); });
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
      applyScene(btn.getAttribute('data-scene-url'));
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
