/**
 * Open Source Software Edit Form JavaScript
 * Main form functionality and initialization
 */

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
    // Global variables
    let uploadedImages = [];
    let logoUrl = '';
    let selectedMemberStates = [];

    // Get current site domain dynamically
    function getSiteApiUrl() {
      const currentDomain = window.location.hostname;
      const currentPort = window.location.port;
      const protocol = window.location.protocol;
      
      let apiUrl = protocol + '//' + currentDomain;
      if (currentPort && currentPort !== '80' && currentPort !== '443') {
        apiUrl += ':' + currentPort;
      }
      
      return apiUrl + '/api/3/action/';
    }

    // Auto-generate URL from title
    $('#title').on('input', function() {
      if ($('#name').prop('readonly')) {
        var title = $(this).val().toLowerCase()
          .replace(/[^\w ]+/g,'')
          .replace(/ +/g,'-');
        $('#name').val(title);
      }
    });
    
    // Toggle URL field editing
    $('#edit-url-btn').on('click', function() {
      var $urlField = $('#name');
      var $btn = $(this);
      
      if ($urlField.prop('readonly')) {
        $urlField.prop('readonly', false).focus();
        $btn.html('<i class="fa fa-lock"></i>').attr('title', 'Lock auto-generation');
        $btn.removeClass('btn-default').addClass('btn-warning');
      } else {
        $urlField.prop('readonly', true);
        $btn.html('<i class="fa fa-edit"></i>').attr('title', 'Edit URL manually');
        $btn.removeClass('btn-warning').addClass('btn-default');
        var title = $('#title').val().toLowerCase()
          .replace(/[^\w ]+/g,'')
          .replace(/ +/g,'-');
        $urlField.val(title);
      }
    });

    // Handle multiple selects - convert arrays to comma-separated strings
    function handleMultipleSelects() {
      // Handle categories
      const categories = $('#software_category').val();
      if (categories && Array.isArray(categories)) {
        $('<input>').attr({
          type: 'hidden',
          name: 'software_category_list',
          value: categories.join(',')
        }).appendTo('form');
      }
      
      // Handle programming languages
      const languages = $('#programming_language').val();
      if (languages && Array.isArray(languages)) {
        $('<input>').attr({
          type: 'hidden',
          name: 'programming_language_list',
          value: languages.join(',')
        }).appendTo('form');
      }
      
      // Handle platforms
      const platforms = $('#platform').val();
      if (platforms && Array.isArray(platforms)) {
        $('<input>').attr({
          type: 'hidden',
          name: 'platform_list',
          value: platforms.join(',')
        }).appendTo('form');
      }
    }

    // Form validation
    $('form').on('submit', function(e) {
      var isValid = true;
      var title = $('#title').val().trim();
      var name = $('#name').val().trim();
      
      if (!title) {
        alert('Please enter a software title');
        $('#title').focus();
        isValid = false;
      }
      
      if (!name) {
        alert('Please enter a URL');
        $('#name').focus();
        isValid = false;
      }
      
      // Validate that all uploaded images have descriptive names
      var emptyAltFields = $('.image-alt').filter(function() {
        return !$(this).val().trim();
      });
      
      if (emptyAltFields.length > 0) {
        alert('Please provide descriptive names for all uploaded images before submitting.');
        emptyAltFields.first().focus();
        isValid = false;
      }
      
      if (!isValid) {
        e.preventDefault();
      } else {
        handleMultipleSelects();
        if (window.ImageUpload) {
          window.ImageUpload.updateUploadedImagesData();
        }
        if (window.MemberStates) {
          window.MemberStates.updateMemberStatesData();
        }
        if (window.syncAllQuillEditors) {
          window.syncAllQuillEditors();
        }
      }
    });
    
    // Confirmation for delete
    $('[data-confirm]').on('click', function(e) {
      if (!confirm($(this).data('confirm'))) {
        e.preventDefault();
      }
    });
    
    // Enhanced textarea auto-resize (only for non-Quill textareas)
    $('textarea:not([id="content"], [id="technical_requirements"], [id="installation_instructions"], [id="learning_resources"], [id="example_applications"])').each(function() {
      this.setAttribute('style', 'height:' + (this.scrollHeight) + 'px;overflow-y:hidden;');
    }).on('input', function() {
      this.style.height = 'auto';
      this.style.height = (this.scrollHeight) + 'px';
    });
    
    // Update title in header preview
    $('#title').on('input', function() {
      const title = $(this).val() || 'Software Title';
      $('.preview-banner h3, .preview-banner h4').text(title);
    });

    // Initialize header display mode selection
    function initializeHeaderDisplayMode() {
      const selectedOption = $('input[name="header_display_mode"]:checked');
      if (selectedOption.length) {
        selectedOption.closest('.header-display-option').addClass('selected');
      }
    }

    // Header display mode change handler
    $('input[name="header_display_mode"]').on('change', function() {
      const logoUrl = $('#header_image').val();
      
      // Update all preview banners based on selected mode
      $('.header-display-option').each(function() {
        const $option = $(this);
        const isSelected = $option.find('input').is(':checked');
        
        if (isSelected) {
          $option.addClass('selected');
        } else {
          $option.removeClass('selected');
        }
      });
      
      // Update logo preview images if logo exists
      if (logoUrl && window.ImageUpload) {
        window.ImageUpload.updateHeaderDisplayPreview(logoUrl);
      }
    });

    // Expose necessary functions and variables globally
    window.OpenSourceSoftwareEdit = {
      getSiteApiUrl: getSiteApiUrl,
      uploadedImages: uploadedImages,
      logoUrl: logoUrl,
      selectedMemberStates: selectedMemberStates,
      handleMultipleSelects: handleMultipleSelects,
      initializeHeaderDisplayMode: initializeHeaderDisplayMode
    };

    // Initialize components
    initializeHeaderDisplayMode();

    // Initialize other modules when they're available
    $(document).ready(function() {
      // Wait a bit for other modules to load
      setTimeout(function() {
        if (window.ImageUpload && typeof window.ImageUpload.init === 'function') {
          window.ImageUpload.init();
        }
        if (window.MemberStates && typeof window.MemberStates.init === 'function') {
          window.MemberStates.init();
        }
        if (window.OrganizationLoader && typeof window.OrganizationLoader.init === 'function') {
          window.OrganizationLoader.init();
        }
        if (window.QuillEditorManager && typeof window.QuillEditorManager.init === 'function') {
          window.QuillEditorManager.init();
        }
      }, 100);
    });

  }); // Close waitForJQuery function

})();
