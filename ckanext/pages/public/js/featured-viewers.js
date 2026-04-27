/**
 * Featured Viewers — JavaScript
 * Handles interactivity for the featured viewers pages.
 */
(function () {
  'use strict';

  /* ------------------------------------------------------------------
   * Slug generation from title (edit form)
   * ----------------------------------------------------------------*/
  function initSlugGenerator() {
    var titleInput = document.getElementById('fv-title');
    var slugInput = document.getElementById('fv-slug');
    if (!titleInput || !slugInput) return;

    // Only auto-generate if slug is empty
    var manualSlug = slugInput.value.trim() !== '';

    titleInput.addEventListener('input', function () {
      if (manualSlug) return;
      slugInput.value = generateSlug(titleInput.value);
    });

    slugInput.addEventListener('input', function () {
      manualSlug = slugInput.value.trim() !== '';
    });
  }

  function generateSlug(text) {
    return text
      .toLowerCase()
      .trim()
      .replace(/[^\w\s-]/g, '')
      .replace(/[-\s]+/g, '-')
      .replace(/^-+|-+$/g, '')
      .substring(0, 200);
  }

  /* ------------------------------------------------------------------
   * Terria map preview (edit form)
   * ----------------------------------------------------------------*/
  function initMapPreview() {
    var linkInput = document.getElementById('fv-terria-link');
    var previewBtn = document.getElementById('fv-preview-map');
    var previewContainer = document.getElementById('fv-map-preview');
    if (!linkInput || !previewContainer) return;

    function loadPreview() {
      var url = linkInput.value.trim();
      if (!url) {
        previewContainer.innerHTML =
          '<div class="fv-map-preview-placeholder">' +
          '<i class="fa fa-map-o"></i>' +
          '<p>Enter a Terria share link above to preview the map</p></div>';
        return;
      }

      // Add embed parameters
      var embedUrl = url;
      if (url.indexOf('#') !== -1 && url.indexOf('?') === -1) {
        var parts = url.split('#');
        embedUrl = parts[0] + '?hideWorkbench=1&hideExplorerPanel=1#' + parts[1];
      }

      previewContainer.innerHTML =
        '<iframe src="' + embedUrl + '" ' +
        'allow="geolocation" loading="lazy" ' +
        'title="Map Preview"></iframe>';
    }

    if (previewBtn) {
      previewBtn.addEventListener('click', function (e) {
        e.preventDefault();
        loadPreview();
      });
    }

    // Auto-preview if link already has a value
    if (linkInput.value.trim()) {
      loadPreview();
    }
  }

  /* ------------------------------------------------------------------
   * Full-screen map toggle (show page)
   * ----------------------------------------------------------------*/
  function initFullScreen() {
    var btn = document.getElementById('fv-fullscreen-btn');
    var shell = document.getElementById('fv-map-shell');
    if (!btn || !shell) return;

    var label = btn.querySelector('.fv-map-action-label');
    var icon = btn.querySelector('i');
    var enterLabel = btn.getAttribute('data-enter-label') || 'Full Screen';
    var exitLabel = btn.getAttribute('data-exit-label') || 'Exit Full Screen';

    function getFullscreenElement() {
      return (
        document.fullscreenElement ||
        document.webkitFullscreenElement ||
        document.msFullscreenElement ||
        document.mozFullScreenElement ||
        null
      );
    }

    function isNativeFullscreen() {
      return getFullscreenElement() === shell;
    }

    function isFallbackFullscreen() {
      return shell.classList.contains('fv-map-shell-fullscreen');
    }

    function setButtonState(active) {
      btn.setAttribute('aria-pressed', active ? 'true' : 'false');
      btn.classList.toggle('fv-map-action-btn-primary-active', active);

      if (icon) {
        icon.className = active ? 'fa fa-compress' : 'fa fa-expand';
        icon.setAttribute('aria-hidden', 'true');
      }

      if (label) {
        label.textContent = active ? exitLabel : enterLabel;
      }
    }

    function syncFullScreenState() {
      var active = isNativeFullscreen() || isFallbackFullscreen();

      shell.classList.toggle('fv-map-shell-active', active);

      if (!active) {
        document.body.classList.remove('fv-map-shell-open');
      }

      setButtonState(active);
    }

    function requestNativeFullscreen() {
      if (shell.requestFullscreen) {
        return shell.requestFullscreen();
      }
      if (shell.webkitRequestFullscreen) {
        shell.webkitRequestFullscreen();
        return null;
      }
      if (shell.msRequestFullscreen) {
        shell.msRequestFullscreen();
        return null;
      }
      if (shell.mozRequestFullScreen) {
        shell.mozRequestFullScreen();
        return null;
      }
      return false;
    }

    function exitNativeFullscreen() {
      if (document.exitFullscreen) {
        return document.exitFullscreen();
      }
      if (document.webkitExitFullscreen) {
        document.webkitExitFullscreen();
        return null;
      }
      if (document.msExitFullscreen) {
        document.msExitFullscreen();
        return null;
      }
      if (document.mozCancelFullScreen) {
        document.mozCancelFullScreen();
        return null;
      }
      return false;
    }

    function enterFallbackFullscreen() {
      shell.classList.add('fv-map-shell-fullscreen');
      shell.classList.add('fv-map-shell-active');
      document.body.classList.add('fv-map-shell-open');
      setButtonState(true);
    }

    function exitFallbackFullscreen() {
      shell.classList.remove('fv-map-shell-fullscreen');
      shell.classList.remove('fv-map-shell-active');
      document.body.classList.remove('fv-map-shell-open');
      setButtonState(false);
    }

    btn.addEventListener('click', function (e) {
      var result;

      e.preventDefault();

      if (isNativeFullscreen()) {
        result = exitNativeFullscreen();
        if (result && typeof result.catch === 'function') {
          result.catch(function () {
            exitFallbackFullscreen();
          });
        }
        return;
      }

      if (isFallbackFullscreen()) {
        exitFallbackFullscreen();
        return;
      }

      result = requestNativeFullscreen();

      if (result === false) {
        enterFallbackFullscreen();
        return;
      }

      if (result && typeof result.then === 'function') {
        result.catch(function () {
          enterFallbackFullscreen();
        });
        return;
      }

      // Older vendor-prefixed APIs fire fullscreenchange but do not return a promise.
      window.setTimeout(syncFullScreenState, 0);
    });

    document.addEventListener('fullscreenchange', syncFullScreenState);
    document.addEventListener('webkitfullscreenchange', syncFullScreenState);
    document.addEventListener('msfullscreenchange', syncFullScreenState);
    document.addEventListener('mozfullscreenchange', syncFullScreenState);

    document.addEventListener('fullscreenerror', function () {
      if (!isNativeFullscreen()) {
        enterFallbackFullscreen();
      }
    });
    document.addEventListener('webkitfullscreenerror', function () {
      if (!isNativeFullscreen()) {
        enterFallbackFullscreen();
      }
    });
    document.addEventListener('msfullscreenerror', function () {
      if (!isNativeFullscreen()) {
        enterFallbackFullscreen();
      }
    });
    document.addEventListener('mozfullscreenerror', function () {
      if (!isNativeFullscreen()) {
        enterFallbackFullscreen();
      }
    });

    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && isFallbackFullscreen()) {
        exitFallbackFullscreen();
      }
    });

    syncFullScreenState();
  }

  /* ------------------------------------------------------------------
   * Copy link to clipboard (show page)
   * ----------------------------------------------------------------*/
  function initCopyLink() {
    var btn = document.getElementById('fv-copy-link');
    if (!btn) return;

    btn.addEventListener('click', function (e) {
      e.preventDefault();
      var url = window.location.href;
      if (navigator.clipboard) {
        navigator.clipboard.writeText(url).then(function () {
          showTooltip(btn, 'Link copied!');
        });
      } else {
        // Fallback
        var input = document.createElement('input');
        input.value = url;
        document.body.appendChild(input);
        input.select();
        document.execCommand('copy');
        document.body.removeChild(input);
        showTooltip(btn, 'Link copied!');
      }
    });
  }

  function showTooltip(el, text) {
    var original = el.innerHTML;
    el.innerHTML = '<i class="fa fa-check"></i> ' + text;
    setTimeout(function () {
      el.innerHTML = original;
    }, 2000);
  }

  /* ------------------------------------------------------------------
   * Lazy-load Terria iframes on list page
   * ----------------------------------------------------------------*/
  function initLazyIframes() {
    if (!('IntersectionObserver' in window)) return;

    var lazyFrames = document.querySelectorAll('[data-terria-src]');
    if (!lazyFrames.length) return;

    var observer = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            var el = entry.target;
            var iframe = document.createElement('iframe');
            iframe.src = el.getAttribute('data-terria-src');
            iframe.setAttribute('loading', 'lazy');
            iframe.setAttribute('allow', 'geolocation');
            iframe.style.cssText = 'width:100%;height:100%;border:none;';
            el.innerHTML = '';
            el.appendChild(iframe);
            observer.unobserve(el);
          }
        });
      },
      { rootMargin: '200px' }
    );

    lazyFrames.forEach(function (frame) {
      observer.observe(frame);
    });
  }

  /* ------------------------------------------------------------------
   * Initialize on DOM ready
   * ----------------------------------------------------------------*/
  function init() {
    initSlugGenerator();
    initMapPreview();
    initFullScreen();
    initCopyLink();
    initLazyIframes();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
