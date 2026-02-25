/* AI Water Tools JavaScript - Water Management AI Tools */

(function() {
  'use strict';

  function waitForJQuery(callback) {
    if (typeof jQuery !== 'undefined') {
      callback(jQuery);
    } else {
      setTimeout(function() {
        waitForJQuery(callback);
      }, 50);
    }
  }

  waitForJQuery(function($) {
    $(document).ready(function() {

      // ================================================================
      // READ MORE FUNCTIONALITY
      // ================================================================

      $(document).on('click', '.read-more-toggle', function(e) {
        e.preventDefault();
        e.stopPropagation();

        var $this = $(this);
        var $parent = $this.closest('.ai-tool-excerpt');
        var $short = $parent.find('.excerpt-short');
        var $full = $parent.find('.excerpt-full');
        var moreText = $this.data('more-text') || 'Read more';
        var lessText = $this.data('less-text') || 'Read less';

        if ($full.is(':visible')) {
          $full.slideUp(200);
          $short.slideDown(200);
          $this.text(moreText);
        } else {
          $short.slideUp(200);
          $full.slideDown(200);
          $this.text(lessText);
        }

        return false;
      });

      window.toggleReadMore = function(button) {
        var excerpt = button.parentElement;
        var preview = excerpt.querySelector('.excerpt-preview');
        var full = excerpt.querySelector('.excerpt-full');

        if (full.style.display === 'none') {
          preview.style.display = 'none';
          full.style.display = 'inline';
          button.innerHTML = '<i class="fa fa-minus"></i> Read less';
          button.classList.add('expanded');
        } else {
          preview.style.display = 'inline';
          full.style.display = 'none';
          button.innerHTML = '<i class="fa fa-plus"></i> Read more';
          button.classList.remove('expanded');
        }
      };

      // ================================================================
      // UNIFIED DROPDOWN SYSTEM
      // ================================================================

      $('.unified-filter-btn').on('click', function(e) {
        e.preventDefault();
        e.stopPropagation();

        var $dropdown = $(this).closest('.unified-dropdown');
        var $menu = $dropdown.find('.unified-dropdown-menu');
        var $filterItem = $dropdown.closest('.filter-item');

        // Close all other dropdowns
        $('.unified-dropdown').not($dropdown).removeClass('show');
        $('.unified-dropdown-menu').not($menu).hide();
        $('.filter-item').not($filterItem).css('z-index', '1');

        $dropdown.toggleClass('show');
        $menu.toggle();

        if ($dropdown.hasClass('show')) {
          $filterItem.css('z-index', '1000');
        } else {
          $filterItem.css('z-index', '1');
        }
      });

      // Handle checkbox changes – update button text
      $(document).on('change', '.unified-option input[type="checkbox"]', function() {
        var $dropdown = $(this).closest('.unified-dropdown');
        var $button = $dropdown.find('.unified-filter-btn');
        var $text = $button.find('.filter-text');
        var $checkboxes = $dropdown.find('input[type="checkbox"]');

        var selectedOptions = [];
        $checkboxes.each(function() {
          if ($(this).is(':checked')) {
            selectedOptions.push($(this).next('span').text().trim());
          }
        });

        var originalText = $text.data('original') || $text.text();
        if (!$text.data('original')) {
          $text.data('original', originalText);
        }

        if (selectedOptions.length === 0) {
          $text.text(originalText);
        } else if (selectedOptions.length === 1) {
          $text.text(selectedOptions[0]);
        } else if (selectedOptions.length <= 2) {
          $text.text(selectedOptions.join(', '));
        } else {
          $text.text(selectedOptions.length + ' selected');
        }
      });

      // Handle radio changes – update text and auto-close
      $(document).on('change', '.unified-option input[type="radio"]', function() {
        var $dropdown = $(this).closest('.unified-dropdown');
        var $button = $dropdown.find('.unified-filter-btn');
        var $text = $button.find('.filter-text');
        var selectedText = $(this).next('span').text().trim();

        $text.text(selectedText);

        setTimeout(function() {
          $dropdown.removeClass('show');
          $dropdown.find('.unified-dropdown-menu').hide();
        }, 250);
      });

      // Select All / Clear All
      $(document).on('click', '.unified-dropdown .select-all-btn', function(e) {
        e.preventDefault();
        $(this).closest('.unified-dropdown')
          .find('input[type="checkbox"]').prop('checked', true).trigger('change');
      });

      $(document).on('click', '.unified-dropdown .clear-all-btn', function(e) {
        e.preventDefault();
        $(this).closest('.unified-dropdown')
          .find('input[type="checkbox"]').prop('checked', false).trigger('change');
      });

      // Close dropdowns on outside click
      $(document).on('click', function(e) {
        if (!$(e.target).closest('.unified-dropdown, .unified-filters-container').length) {
          $('.unified-dropdown').removeClass('show');
          $('.unified-dropdown-menu').hide();
          $('.filter-item').css('z-index', '1');
        }
      });

      // Prevent dropdown from closing when clicking inside menu
      $('.unified-dropdown-menu').on('click', function(e) {
        e.stopPropagation();
      });

      // Initialize dropdown labels on page load
      $('.unified-dropdown').each(function() {
        var $dropdown = $(this);
        var $text = $dropdown.find('.filter-text');

        if (!$text.data('original')) {
          $text.data('original', $text.text());
        }

        var $checkboxes = $dropdown.find('input[type="checkbox"]');
        if ($checkboxes.length > 0) {
          $checkboxes.first().trigger('change');
        }

        var $selectedRadio = $dropdown.find('input[type="radio"]:checked');
        if ($selectedRadio.length) {
          $selectedRadio.trigger('change');
        }
      });

      // ================================================================
      // FILTER RESET
      // ================================================================

      window.resetFilters = function() {
        var $form = $('form');
        $form.find('input[type="text"], input[type="search"]').val('');
        $form.find('select').prop('selectedIndex', 0);
        $form.find('input[type="checkbox"]').prop('checked', false);
        $form.find('input[type="radio"][value=""]').prop('checked', true);
        $form.find('input[type="radio"]').not('[value=""]').prop('checked', false);

        // Reset dropdown labels
        $('.unified-dropdown').each(function() {
          var $text = $(this).find('.filter-text');
          var original = $text.data('original') || $text.text();
          $text.text(original);
        });

        // Trigger change events to refresh computed labels
        $('.unified-dropdown').each(function() {
          var $cb = $(this).find('input[type="checkbox"]').first();
          var $radio = $(this).find('input[type="radio"][value=""]');
          if ($cb.length) $cb.trigger('change');
          if ($radio.length) $radio.trigger('change');
        });

        $form.submit();
      };

      // ================================================================
      // CARD GRID ANIMATIONS
      // ================================================================

      function animateCards() {
        $('.ai-tool-card').each(function(index) {
          var $card = $(this);
          if (!$card.hasClass('animated')) {
            $card.css({
              'animation-delay': (index * 0.05) + 's'
            });
            $card.addClass('animated');
          }
        });
      }

      animateCards();

      // ================================================================
      // TOOLTIPS
      // ================================================================

      if (typeof $().tooltip === 'function') {
        $('[data-toggle="tooltip"]').tooltip();
      }

      // ================================================================
      // AI WATER EXCERPT TOGGLE (list view)
      // ================================================================

      window.toggleAiWaterExcerpt = function(button) {
        var excerpt = button.parentElement;
        var preview = excerpt.querySelector('.excerpt-preview');
        var full = excerpt.querySelector('.excerpt-full');
        if (full.style.display === 'none' || !full.style.display) {
          preview.style.display = 'none';
          full.style.display = 'inline';
          button.innerHTML = '<i class="fa fa-minus"></i> Read less';
          button.classList.add('expanded');
        } else {
          preview.style.display = 'inline';
          full.style.display = 'none';
          button.innerHTML = '<i class="fa fa-plus"></i> Read more';
          button.classList.remove('expanded');
        }
      };

      // ================================================================
      // IMAGE GALLERY AND MODAL FUNCTIONALITY
      // ================================================================

      // Image modal for gallery
      $(document).on('click', '.gallery-image', function(e) {
        e.preventDefault();
        e.stopPropagation();

        var $img = $(this);
        var imageUrl = $img.data('image') || $img.attr('src');
        var caption = $img.data('caption') || $img.attr('alt') || '';

        if (imageUrl) {
          $('#modalImage').attr('src', imageUrl);
          $('#modalImage').attr('alt', caption);
          $('#imageModalTitle').text(caption || 'Image Preview');
          $('#modalCaption').text(caption);

          if (typeof $.fn.modal !== 'undefined') {
            $('#imageModal').modal('show');
          } else {
            $('#imageModal').css('display', 'block').addClass('show');
          }
        }
      });

      // Close modal functionality
      $(document).on('click', '.close, .modal', function(e) {
        if (e.target === this) {
          if (typeof $.fn.modal !== 'undefined') {
            $('#imageModal').modal('hide');
          }
          $('#imageModal').css('display', 'none').removeClass('show');
        }
      });

      // Escape key to close modal
      $(document).on('keyup', function(e) {
        if (e.keyCode === 27) {
          if (typeof $.fn.modal !== 'undefined') {
            $('#imageModal').modal('hide');
          }
          $('#imageModal').css('display', 'none').removeClass('show');
        }
      });

      // ================================================================
      // GALLERY IMAGE HOVER EFFECTS
      // ================================================================

      $('.gallery-image').on('load', function() {
        $(this).addClass('loaded').css('opacity', '1');
      });

      $('.gallery-image').css('cursor', 'pointer');

      $('.gallery-image-item').hover(
        function() {
          $(this).find('.image-overlay').css('opacity', '1');
        },
        function() {
          $(this).find('.image-overlay').css('opacity', '0');
        }
      );

      // ================================================================
      // QUILL EDITOR SYNC
      // ================================================================

      $(document).on('submit', '.software-form, .ai-water-form', function() {
        if (typeof Quill !== 'undefined') {
          document.querySelectorAll('.quill-editor').forEach(function(editorEl) {
            var quill = Quill.find(editorEl);
            if (quill) {
              var textarea = editorEl.parentElement.querySelector('textarea');
              if (textarea) {
                textarea.value = quill.root.innerHTML;
              }
            }
          });
        }
      });

      // ================================================================
      // DEBUG INFO
      // ================================================================

      console.log('AI Water Tools functionality initialized');
      console.log('AI tool cards found:', $('.ai-tool-card').length);
      console.log('Unified dropdowns found:', $('.unified-dropdown').length);

    }); // End document ready
  }); // End waitForJQuery
})(); // End IIFE
