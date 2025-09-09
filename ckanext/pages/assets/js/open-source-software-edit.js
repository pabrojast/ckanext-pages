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
    if (window.__os_edit_bound) { return; }
    window.__os_edit_bound = true;
    $(document).ready(function() {
      
      // ================================================================
      // FORM VALIDATION AND INTERACTIVITY
      // ================================================================
      
      // Auto-generate name from title
      $('#title').on('input', function() {
        if (!$('#name').data('manually-edited')) {
          var title = $(this).val();
          var name = title.toLowerCase()
            .replace(/[^a-z0-9\s-]/g, '')
            .replace(/\s+/g, '-')
            .replace(/-+/g, '-')
            .replace(/^-|-$/g, '');
          $('#name').val(name);
        }
      });
      
      // Mark name as manually edited if user types in it
      $('#name').on('input', function() {
        $(this).data('manually-edited', true);
      });
      
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
      
      // ================================================================
      // IMAGE UPLOAD SYSTEM
      // ================================================================
      
      // Track uploaded images
      var uploadedImages = [];
      var uploadedLogo = null;
      
      // Load existing uploaded images from hidden field
      function loadExistingImages() {
        var existingData = $('#uploaded_images').val();
        if (existingData) {
          try {
            uploadedImages = JSON.parse(existingData);
            updateImagePreview();
          } catch (e) {
            console.warn('Could not parse existing images data');
          }
        }
      }
      
      // Update image preview area
      function updateImagePreview() {
        var $preview = $('#image-preview');
        if (!$preview.length) {
          $('#image-dropzone').after('<div id="image-preview" class="image-preview-container"></div>');
          $preview = $('#image-preview');
        }
        
        $preview.empty();
        
        if (uploadedImages.length > 0) {
          $preview.append('<h4>Uploaded Images</h4>');
          uploadedImages.forEach(function(image, index) {
            var imageHtml = `
              <div class="preview-image-item" data-index="${index}">
                <img src="${image.url}" alt="${image.alt}" class="preview-image">
                <div class="image-controls">
                  <input type="text" class="form-control image-alt-input" value="${image.alt}" placeholder="Image description">
                  <button type="button" class="btn btn-sm btn-danger remove-image">
                    <i class="fa fa-times"></i> Remove
                  </button>
                </div>
              </div>
            `;
            $preview.append(imageHtml);
          });
        }
        
        // Update hidden field
        $('#uploaded_images').val(JSON.stringify(uploadedImages));
      }
      
      // Update logo preview
      function updateLogoPreview() {
        var $preview = $('#logo-preview');
        if (!$preview.length) {
          $('#logo-dropzone').after('<div id="logo-preview" class="logo-preview-container"></div>');
          $preview = $('#logo-preview');
        }
        
        $preview.empty();
        
        if (uploadedLogo) {
          var logoHtml = `
            <div class="logo-preview-item">
              <h4>Logo Preview</h4>
              <img src="${uploadedLogo.url}" alt="Logo" class="logo-preview-img">
              <div class="logo-controls">
                <p class="text-muted">Logo automatically resized to 200x80px</p>
                <button type="button" class="btn btn-sm btn-danger remove-logo">
                  <i class="fa fa-times"></i> Remove Logo
                </button>
              </div>
            </div>
          `;
          $preview.append(logoHtml);
        }
      }
      
      // Upload image function
      function uploadImage(file, isLogo = false) {
        if (!file || !file.type.startsWith('image/')) {
          alert('Please select a valid image file.');
          return;
        }
        
        if (file.size > 10 * 1024 * 1024) { // 10MB limit
          alert('File size must be less than 10MB.');
          return;
        }
        
        var formData = new FormData();
        formData.append('upload', file);
        
        // Add special flag for logo processing
        if (isLogo) {
          formData.append('is_logo', 'true');
          // Check if background should be added
          if ($('#add-background').is(':checked')) {
            formData.append('add_background', 'true');
          }
        }
        
        // Show upload progress
        var progressHtml = `
          <div class="upload-progress">
            <div class="progress">
              <div class="progress-bar" role="progressbar" style="width: 0%"></div>
            </div>
            <p>Uploading ${isLogo ? 'logo' : 'image'}...</p>
          </div>
        `;
        
        if (isLogo) {
          $('#logo-dropzone').append(progressHtml);
        } else {
          $('#image-dropzone').append(progressHtml);
        }
        
        $.ajax({
          url: '/upload',
          type: 'POST',
          data: formData,
          processData: false,
          contentType: false,
          xhr: function() {
            var xhr = new window.XMLHttpRequest();
            xhr.upload.addEventListener("progress", function(evt) {
              if (evt.lengthComputable) {
                var percentComplete = (evt.loaded / evt.total) * 100;
                $('.progress-bar').css('width', percentComplete + '%');
              }
            }, false);
            return xhr;
          },
          success: function(response) {
            $('.upload-progress').remove();
            
            if (response.uploaded) {
              if (isLogo) {
                uploadedLogo = {
                  url: response.url,
                  filename: response.fileName
                };
                updateLogoPreview();
                
                // Update header image field if it's empty
                if (!$('#header_image').val()) {
                  $('#header_image').val(response.url);
                }
                
              } else {
                var altText = prompt('Please provide a description for this image:');
                if (altText) {
                  uploadedImages.push({
                    url: response.url,
                    alt: altText,
                    filename: response.fileName
                  });
                  updateImagePreview();
                } else {
                  alert('Image description is required. Upload cancelled.');
                }
              }
            } else {
              alert('Upload failed. Please try again.');
            }
          },
          error: function(xhr, status, error) {
            $('.upload-progress').remove();
            console.error('Upload error:', error);
            alert('Upload failed: ' + error);
          }
        });
      }
      
      // Handle image upload
      $('#image-upload').on('change', function(e) {
        e.stopPropagation();
        const files = this.files;
        for (let i = 0; i < files.length; i++) {
          if (files[i].type.startsWith('image/')) {
            uploadImage(files[i], false);
          }
        }
        this.value = '';
      });
      
      // Handle logo upload
      $('#logo-upload').on('change', function(e) {
        e.stopPropagation();
        const files = this.files;
        if (files.length > 0 && files[0].type.startsWith('image/')) {
          uploadImage(files[0], true);
          this.value = '';
        }
      });
      
      // Handle dropzone click
      $('#image-dropzone').on('click', function(e) {
        e.preventDefault();
        e.stopPropagation();
        $('#image-upload').trigger('click');
      });
      
      // Handle logo dropzone click
      $('#logo-dropzone').on('click', function(e) {
        e.preventDefault();
        e.stopPropagation();
        $('#logo-upload').trigger('click');
      });
      
      // Handle dropzone drag and drop
      $('#image-dropzone').on('dragover', function(e) {
        e.preventDefault();
        e.stopPropagation();
        $(this).addClass('dragover');
      });
      
      $('#image-dropzone').on('dragleave', function(e) {
        e.preventDefault();
        e.stopPropagation();
        $(this).removeClass('dragover');
      });
      
      $('#image-dropzone').on('drop', function(e) {
        e.preventDefault();
        e.stopPropagation();
        $(this).removeClass('dragover');
        
        const files = e.originalEvent.dataTransfer.files;
        for (let i = 0; i < files.length; i++) {
          if (files[i].type.startsWith('image/')) {
            uploadImage(files[i], false);
          }
        }
      });
      
      // Handle logo dropzone drag and drop
      $('#logo-dropzone').on('dragover', function(e) {
        e.preventDefault();
        e.stopPropagation();
        $(this).addClass('dragover');
      });
      
      $('#logo-dropzone').on('dragleave', function(e) {
        e.preventDefault();
        e.stopPropagation();
        $(this).removeClass('dragover');
      });
      
      $('#logo-dropzone').on('drop', function(e) {
        e.preventDefault();
        e.stopPropagation();
        $(this).removeClass('dragover');
        
        const files = e.originalEvent.dataTransfer.files;
        if (files.length > 0 && files[0].type.startsWith('image/')) {
          uploadImage(files[0], true);
        }
      });
      
      // Handle image removal
      $(document).on('click', '.remove-image', function(e) {
        e.preventDefault();
        var index = $(this).closest('.preview-image-item').data('index');
        uploadedImages.splice(index, 1);
        updateImagePreview();
      });
      
      // Handle logo removal
      $(document).on('click', '.remove-logo', function(e) {
        e.preventDefault();
        uploadedLogo = null;
        updateLogoPreview();
      });
      
      // Handle alt text changes
      $(document).on('input', '.image-alt-input', function() {
        var index = $(this).closest('.preview-image-item').data('index');
        uploadedImages[index].alt = $(this).val();
        $('#uploaded_images').val(JSON.stringify(uploadedImages));
      });
      
      // ================================================================
      // HEADER DISPLAY MODE PREVIEW
      // ================================================================
      
      $('input[name="header_display_mode"]').on('change', function() {
        var mode = $(this).val();
        $('.header-display-option').removeClass('active');
        $(this).closest('.header-display-option').addClass('active');
        
        // Update preview based on mode
        updateHeaderPreview(mode);
      });
      
      function updateHeaderPreview(mode) {
        var title = $('#title').val() || 'Software Title';
        
        $('.preview-banner h4').text(title);
        
        // Add visual feedback about logo requirement
        if ((mode === 'logo' || mode === 'logo_text') && !uploadedLogo) {
          $('.text-warning').show();
        } else {
          $('.text-warning').hide();
        }
      }
      
      // Update preview when title changes
      $('#title').on('input', function() {
        var mode = $('input[name="header_display_mode"]:checked').val();
        updateHeaderPreview(mode);
      });
      
      // ================================================================
      // HANDLE NATIVE HTML MULTI-SELECT FIELDS
      // ================================================================
      
      // Handle native multi-select fields and convert to comma-separated values
      function handleNativeMultiSelects() {
        // Handle software categories
        var $categorySelect = $('#software_category');
        if ($categorySelect.length) {
          var selectedCategories = $categorySelect.val();
          if (selectedCategories && Array.isArray(selectedCategories)) {
            // Create hidden field with comma-separated values
            $('input[name="software_category_hidden"]').remove();
            $('<input>').attr({
              type: 'hidden',
              name: 'software_category',
              value: selectedCategories.join(',')
            }).appendTo('form');
            // Disable original select to prevent double submission
            $categorySelect.attr('name', 'software_category_original').prop('disabled', true);
          }
        }
        
        // Handle programming languages
        var $langSelect = $('#programming_language');
        if ($langSelect.length) {
          var selectedLangs = $langSelect.val();
          if (selectedLangs && Array.isArray(selectedLangs)) {
            $('input[name="programming_language_hidden"]').remove();
            $('<input>').attr({
              type: 'hidden',
              name: 'programming_language',
              value: selectedLangs.join(',')
            }).appendTo('form');
            $langSelect.attr('name', 'programming_language_original').prop('disabled', true);
          }
        }
        
        // Handle platforms
        var $platformSelect = $('#platform');
        if ($platformSelect.length) {
          var selectedPlatforms = $platformSelect.val();
          if (selectedPlatforms && Array.isArray(selectedPlatforms)) {
            $('input[name="platform_hidden"]').remove();
            $('<input>').attr({
              type: 'hidden',
              name: 'platform',
              value: selectedPlatforms.join(',')
            }).appendTo('form');
            $platformSelect.attr('name', 'platform_original').prop('disabled', true);
          }
        }
      }
      
      // ================================================================
      // FORM SUBMISSION HANDLING
      // ================================================================
      
      $('form').on('submit', function(e) {
        // Handle multi-select fields before validation
        handleNativeMultiSelects();
        // Validate required fields
        var title = $('#title').val().trim();
        var name = $('#name').val().trim();
        
        if (!title) {
          alert('Title is required.');
          $('#title').focus();
          e.preventDefault();
          return false;
        }
        
        if (!name) {
          alert('Name is required.');
          $('#name').focus();
          e.preventDefault();
          return false;
        }
        
        // Validate header display mode
        var headerMode = $('input[name="header_display_mode"]:checked').val();
        if ((headerMode === 'logo' || headerMode === 'logo_text') && !uploadedLogo && !$('#header_image').val()) {
          alert('Logo display modes require either a logo image to be uploaded or a header image URL to be provided.');
          e.preventDefault();
          return false;
        }
        
        return true;
      });
      
      // ================================================================
      // INITIALIZATION
      // ================================================================
      
      // Load existing data
      loadExistingImages();
      
      // Initialize multi-select dropdowns
      $('.multi-select-dropdown').each(function() {
        var $dropdown = $(this);
        var fieldName = $dropdown.data('field');
        if (fieldName) {
          var currentValue = $('#' + fieldName).val();
          if (currentValue) {
            var values = currentValue.split(',');
            values.forEach(function(value) {
              $dropdown.find('input[value="' + value.trim() + '"]').prop('checked', true);
            });
            // Trigger change to update display
            $dropdown.find('input[type="checkbox"]:first').trigger('change');
          }
        }
      });
      
      // Initialize header display mode
      var currentMode = $('input[name="header_display_mode"]:checked').val();
      if (currentMode) {
        updateHeaderPreview(currentMode);
      }
      
      console.log('Open source software edit form initialized');
      
    }); // Close document.ready
  }); // Close waitForJQuery function
})(); // Close main function
