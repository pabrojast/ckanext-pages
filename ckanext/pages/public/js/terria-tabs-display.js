/**
 * Terria Tabs Display + map shell (classic Data Stories show page)
 *
 * - Tab switching for baked .terria-tabs-display blocks
 * - ensure allow="geolocation; fullscreen" on existing iframes
 * - wrap maps/media in .ds-map-shell with a Fullscreen control
 * - 100% / 100vw width becomes viewport-wide; custom sizes stay contained
 */

(function() {
  var ALLOW = 'geolocation; fullscreen';

  function waitForJQuery(callback, attempts) {
    attempts = attempts || 0;

    if (typeof jQuery !== 'undefined' && typeof $ !== 'undefined') {
      try {
        if (typeof $().jquery !== 'undefined') {
          callback($);
          return;
        }
      } catch (e) {
        console.warn('jQuery test failed:', e);
      }
    }

    if (typeof jQuery !== 'undefined' && typeof $ === 'undefined') {
      window.$ = jQuery;
      callback(jQuery);
      return;
    }

    if (attempts > 200) {
      console.error('jQuery failed to load after 10 seconds');
      return;
    }

    setTimeout(function() {
      waitForJQuery(callback, attempts + 1);
    }, 50);
  }

  function isFullBleedWidth(iframe) {
    if (!iframe) {
      return true;
    }
    var styleWidth = (iframe.style && iframe.style.width) || '';
    var attrWidth = iframe.getAttribute('width') || '';
    var width = String(styleWidth || attrWidth).trim();
    if (!width) {
      return true;
    }
    return /^(100%|100vw)$/i.test(width);
  }

  function ensureIframeAllow(iframe) {
    var current = (iframe.getAttribute('allow') || '').toLowerCase();
    if (current.indexOf('fullscreen') === -1 || current.indexOf('geolocation') === -1) {
      iframe.setAttribute('allow', ALLOW);
    }
    if (!iframe.hasAttribute('allowfullscreen')) {
      iframe.setAttribute('allowfullscreen', '');
    }
    iframe.setAttribute('mozallowfullscreen', '');
    iframe.setAttribute('webkitallowfullscreen', '');
  }

  function getLabels($root) {
    var $source = $root.closest('.story-sections-full');
    if (!$source.length) {
      $source = $('.story-sections-full').first();
    }
    return {
      enter: $source.attr('data-fs-enter') || 'Full Screen',
      exit: $source.attr('data-fs-exit') || 'Exit Full Screen'
    };
  }

  function getFullscreenElement() {
    return (
      document.fullscreenElement ||
      document.webkitFullscreenElement ||
      document.msFullscreenElement ||
      document.mozFullScreenElement ||
      null
    );
  }

  function requestNativeFullscreen(el) {
    if (el.requestFullscreen) {
      return el.requestFullscreen();
    }
    if (el.webkitRequestFullscreen) {
      el.webkitRequestFullscreen();
      return null;
    }
    if (el.msRequestFullscreen) {
      el.msRequestFullscreen();
      return null;
    }
    if (el.mozRequestFullScreen) {
      el.mozRequestFullScreen();
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

  function bindFullscreen($shell, labels) {
    var shell = $shell[0];
    var $btn = $shell.find('.ds-map-fullscreen-btn');
    if (!shell || !$btn.length) {
      return;
    }
    var $icon = $btn.find('i');
    var $label = $btn.find('.ds-map-fullscreen-label');

    function isNative() {
      return getFullscreenElement() === shell;
    }

    function isFallback() {
      return $shell.hasClass('ds-map-shell-fallback');
    }

    function setButtonState(active) {
      $btn.toggleClass('is-active', active);
      $btn.attr('aria-pressed', active ? 'true' : 'false');
      if ($icon.length) {
        $icon.attr('class', active ? 'fa fa-compress' : 'fa fa-expand');
      }
      if ($label.length) {
        $label.text(active ? labels.exit : labels.enter);
      }
    }

    function sync() {
      var active = isNative() || isFallback();
      $shell.toggleClass('ds-map-shell-active', active);
      if (!active) {
        document.body.classList.remove('ds-map-shell-open');
      }
      setButtonState(active);
    }

    function enterFallback() {
      $shell.addClass('ds-map-shell-fallback ds-map-shell-active');
      document.body.classList.add('ds-map-shell-open');
      setButtonState(true);
    }

    function exitFallback() {
      $shell.removeClass('ds-map-shell-fallback ds-map-shell-active');
      document.body.classList.remove('ds-map-shell-open');
      setButtonState(false);
    }

    $btn.on('click', function(e) {
      var result;
      e.preventDefault();

      if (isNative()) {
        result = exitNativeFullscreen();
        if (result && typeof result.catch === 'function') {
          result.catch(function() { exitFallback(); });
        }
        return;
      }
      if (isFallback()) {
        exitFallback();
        return;
      }

      result = requestNativeFullscreen(shell);
      if (result === false) {
        enterFallback();
        return;
      }
      if (result && typeof result.then === 'function') {
        result.catch(function() { enterFallback(); });
        return;
      }
      window.setTimeout(sync, 0);
    });

    document.addEventListener('fullscreenchange', sync);
    document.addEventListener('webkitfullscreenchange', sync);
    document.addEventListener('msfullscreenchange', sync);
    document.addEventListener('mozfullscreenchange', sync);
    document.addEventListener('keydown', function(e) {
      if (e.key === 'Escape' && isFallback()) {
        exitFallback();
      }
    });

    sync();
  }

  function wrapInShell($node, fullBleed, labels) {
    if ($node.closest('.ds-map-shell').length) {
      return $node.closest('.ds-map-shell');
    }

    var cls = 'ds-map-shell ' + (fullBleed ? 'is-full-width' : 'is-custom-width');
    $node.wrap('<div class="' + cls + '"></div>');
    var $shell = $node.parent();
    $shell.prepend(
      '<div class="ds-map-shell-toolbar">' +
        '<button type="button" class="ds-map-fullscreen-btn" aria-pressed="false">' +
          '<i class="fa fa-expand" aria-hidden="true"></i>' +
          '<span class="ds-map-fullscreen-label"></span>' +
        '</button>' +
      '</div>'
    );
    $shell.find('.ds-map-fullscreen-label').text(labels.enter);
    bindFullscreen($shell, labels);
    return $shell;
  }

  function enhanceClassicStory($) {
    var $root = $('.story-sections-full');
    if (!$root.length) {
      $root = $('.data-story-classic .story-section .section-content').closest('.story-sections');
    }
    if (!$root.length) {
      return;
    }

    var labels = getLabels($root);

    $root.find('.terria-tabs-display').each(function() {
      var $tabs = $(this);
      $tabs.find('iframe').each(function() {
        ensureIframeAllow(this);
      });
      var firstIframe = $tabs.find('iframe').get(0);
      wrapInShell($tabs, isFullBleedWidth(firstIframe), labels);
    });

    $root.find('.section-content iframe').each(function() {
      var iframe = this;
      var $iframe = $(iframe);
      if ($iframe.closest('.ds-map-shell').length || $iframe.closest('.terria-tabs-display').length) {
        return;
      }
      ensureIframeAllow(iframe);
      wrapInShell($iframe, isFullBleedWidth(iframe), labels);
    });
  }

  waitForJQuery(function($) {
    $(document).ready(function() {

      $('.terria-tabs-display').each(function() {
        var $tabsDisplay = $(this);
        var $navItems = $tabsDisplay.find('.terria-tabs-nav-display li');
        var $tabPanels = $tabsDisplay.find('.terria-tab-display');

        $navItems.on('click', function() {
          var tabIndex = $(this).data('tab');
          $navItems.removeClass('active');
          $(this).addClass('active');
          $tabPanels.removeClass('active').hide();
          $tabPanels.filter('[data-tab="' + tabIndex + '"]').addClass('active').show();
        });

        if ($navItems.length > 0 && !$navItems.filter('.active').length) {
          $navItems.first().addClass('active');
          $tabPanels.first().addClass('active').show();
        }
      });

      enhanceClassicStory($);
    });
  });
})();
