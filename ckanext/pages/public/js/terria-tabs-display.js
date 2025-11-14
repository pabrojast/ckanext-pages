/**
 * Terria Tabs Display JavaScript
 * Handles tab switching functionality for Terria maps in Data Stories show page
 */

(function() {
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

  waitForJQuery(function($) {
    $(document).ready(function() {

      // Initialize all Terria tabs displays
      $('.terria-tabs-display').each(function() {
        const $tabsDisplay = $(this);
        const $navItems = $tabsDisplay.find('.terria-tabs-nav-display li');
        const $tabPanels = $tabsDisplay.find('.terria-tab-display');

        // Handle tab click
        $navItems.on('click', function() {
          const tabIndex = $(this).data('tab');

          // Update navigation active state
          $navItems.removeClass('active');
          $(this).addClass('active');

          // Update panels visibility
          $tabPanels.removeClass('active').hide();
          $tabPanels.filter(`[data-tab="${tabIndex}"]`).addClass('active').show();
        });

        // Ensure first tab is active on load
        if ($navItems.length > 0 && !$navItems.filter('.active').length) {
          $navItems.first().addClass('active');
          $tabPanels.first().addClass('active').show();
        }
      });

    });
  });
})();
