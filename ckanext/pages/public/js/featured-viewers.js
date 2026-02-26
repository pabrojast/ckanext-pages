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
    var container = document.getElementById('fv-map-container');
    if (!btn || !container) return;

    var exitBtn = null;

    btn.addEventListener('click', function (e) {
      e.preventDefault();
      container.classList.toggle('fv-fullscreen');

      if (container.classList.contains('fv-fullscreen')) {
        // Create exit button
        exitBtn = document.createElement('button');
        exitBtn.className = 'fv-map-action-btn';
        exitBtn.style.cssText =
          'position:fixed;top:1rem;right:1rem;z-index:10000;background:#fff;box-shadow:0 2px 8px rgba(0,0,0,0.2);';
        exitBtn.innerHTML = '<i class="fa fa-compress"></i> Exit Full Screen';
        exitBtn.addEventListener('click', function () {
          container.classList.remove('fv-fullscreen');
          if (exitBtn && exitBtn.parentNode) exitBtn.parentNode.removeChild(exitBtn);
        });
        document.body.appendChild(exitBtn);
      } else {
        if (exitBtn && exitBtn.parentNode) exitBtn.parentNode.removeChild(exitBtn);
      }
    });

    // ESC key to exit
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && container.classList.contains('fv-fullscreen')) {
        container.classList.remove('fv-fullscreen');
        if (exitBtn && exitBtn.parentNode) exitBtn.parentNode.removeChild(exitBtn);
      }
    });
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
