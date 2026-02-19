/* Open Source Software Edit Form JavaScript */

(function() {
  'use strict';
  
  // Wait for jQuery to be available
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
      // MULTI-SELECT DROPDOWN FUNCTIONALITY FOR EDIT FORM
      // ================================================================
      
      // Multi-Select Dropdown Functionality
      $('.multi-select-button').on('click', function(e) {
        e.preventDefault();
        e.stopPropagation();
        
        var $dropdown = $(this).closest('.multi-select-dropdown');
        var $menu = $dropdown.find('.multi-select-menu');
        
        // Close all other dropdowns
        $('.multi-select-dropdown').not($dropdown).removeClass('open');
        $('.multi-select-menu').not($menu).hide();
        
        // Toggle this dropdown
        $dropdown.toggleClass('open');
        $menu.toggle();
      });
      
      // Handle checkbox changes
      $('.multi-select-option input[type="checkbox"]').on('change', function() {
        var $dropdown = $(this).closest('.multi-select-dropdown');
        var $button = $dropdown.find('.multi-select-button');
        var $text = $button.find('.multi-select-text');
        var $checkboxes = $dropdown.find('input[type="checkbox"]');
        
        var selectedOptions = [];
        var selectedValues = [];
        $checkboxes.each(function() {
          if ($(this).is(':checked')) {
            selectedOptions.push($(this).closest('label').text().trim());
            selectedValues.push($(this).val());
          }
        });
        
        // Update hidden field with comma-separated values
        var hiddenField = $dropdown.data('field');
        if (hiddenField) {
          $('#' + hiddenField).val(selectedValues.join(','));
        }
        
        // Update button text
        if (selectedOptions.length === 0) {
          var defaultText = $dropdown.find('.multi-select-option:first label').text().includes('Programming') ? 
            'Select Languages' : 'Select Categories';
          $text.text(defaultText);
        } else if (selectedOptions.length === 1) {
          $text.text(selectedOptions[0]);
        } else if (selectedOptions.length <= 3) {
          $text.text(selectedOptions.join(', '));
        } else {
          $text.text(selectedOptions.length + ' selected');
        }
      });
      
      // Select All functionality
      $('.select-all-btn').on('click', function(e) {
        e.preventDefault();
        var $dropdown = $(this).closest('.multi-select-dropdown');
        $dropdown.find('input[type="checkbox"]').prop('checked', true).trigger('change');
      });
      
      // Clear All functionality
      $('.clear-all-btn').on('click', function(e) {
        e.preventDefault();
        var $dropdown = $(this).closest('.multi-select-dropdown');
        $dropdown.find('input[type="checkbox"]').prop('checked', false).trigger('change');
      });
      
      // Close dropdowns when clicking outside
      $(document).on('click', function(e) {
        if (!$(e.target).closest('.multi-select-dropdown').length) {
          $('.multi-select-dropdown').removeClass('open');
          $('.multi-select-menu').hide();
        }
      });
      
      // Prevent dropdown from closing when clicking inside menu
      $('.multi-select-menu').on('click', function(e) {
        e.stopPropagation();
      });
      
      // NOTE: Quill editors are initialized in the inline script of the template
      // to avoid duplicate toolbar rendering. Do not initialize Quill here.

      // NOTE: Image upload, dropzone handlers, header display preview,
      // form submission, and title-to-name auto-generation are handled
      // in the inline script of the template.
      // Do not duplicate those handlers here.

      // NOTE: Form submission handling, validation, and initialization
      // are handled in the inline script of the template.
      // Do not duplicate those handlers here.
      
      console.log('Open source software edit form initialized');
      
    }); // Close document.ready
  }); // Close waitForJQuery function
})(); // Close main function
