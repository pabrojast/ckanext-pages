/* Open Source Software JavaScript - Water Management Tools */

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
      // READ MORE FUNCTIONALITY
      // ================================================================
      
      // Read more toggle functionality - Use event delegation for dynamic content
      $(document).on('click', '.read-more-toggle', function(e) {
        e.preventDefault();
        e.stopPropagation();
        
        const $this = $(this);
        const $parent = $this.closest('.software-excerpt');
        const $short = $parent.find('.excerpt-short');
        const $full = $parent.find('.excerpt-full');
        const moreText = $this.data('more-text') || 'Read more';
        const lessText = $this.data('less-text') || 'Read less';
        
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
      
      // Software Read More functionality for list view
      window.toggleSoftwareExcerpt = function(button) {
        const softwareExcerpt = button.parentElement;
        const preview = softwareExcerpt.querySelector('.excerpt-preview');
        const full = softwareExcerpt.querySelector('.excerpt-full');
        
        if (full.style.display === 'none') {
          // Show full text
          preview.style.display = 'none';
          full.style.display = 'inline';
          button.innerHTML = '<i class="fa fa-minus"></i> Read less';
          button.classList.add('expanded');
        } else {
          // Show preview text
          preview.style.display = 'inline';
          full.style.display = 'none';
          button.innerHTML = '<i class="fa fa-plus"></i> Read more';
          button.classList.remove('expanded');
        }
      };
      
      // ================================================================
      // MULTI-SELECT DROPDOWN FUNCTIONALITY
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
        $checkboxes.each(function() {
          if ($(this).is(':checked')) {
            selectedOptions.push($(this).closest('label').text().trim());
          }
        });
        
        // Update button text
        if (selectedOptions.length === 0) {
          var defaultText = $dropdown.find('.multi-select-option:first label').text().includes('Programming') ? 
            'All Categories' : 'All Languages';
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
      
      // Initialize button text on page load
      $('.multi-select-dropdown').each(function() {
        $(this).find('input[type="checkbox"]:first').trigger('change');
      });
      
      // ================================================================
      // IMAGE GALLERY AND MODAL FUNCTIONALITY
      // ================================================================
      
      // Image modal functionality
      $('.image-container, .gallery-image').on('click', function(e) {
        e.preventDefault();
        e.stopPropagation();
        
        const $img = $(this).find('.gallery-image').length ? $(this).find('.gallery-image') : $(this);
        const imageUrl = $img.attr('src');
        const caption = $img.attr('alt') || $img.siblings('.image-caption').text() || 'Image';
        
        if (imageUrl) {
          $('#modalImage').attr('src', imageUrl);
          $('#modalImage').attr('alt', caption);
          $('#modalCaption').text(caption);
          $('#imageModalTitle').text(caption);
          
          // Use Bootstrap modal if available, otherwise custom modal
          if (typeof $.fn.modal !== 'undefined') {
            $('#imageModal').modal('show');
          } else {
            $('#imageModal').css('display', 'block').addClass('show');
          }
        }
      });
      
      // Handle clicks on images within markdown content
      $('.software-content-body img, .learning-resources-content img, .installation-content img').on('click', function(e) {
        e.preventDefault();
        e.stopPropagation();
        
        var $img = $(this);
        var imageUrl = $img.attr('src');
        var caption = $img.attr('alt') || $img.attr('title') || 'Image';
        
        if (imageUrl) {
          $('#modalImage').attr('src', imageUrl);
          $('#modalImage').attr('alt', caption);
          $('#modalCaption').text(caption);
          $('#imageModalTitle').text(caption);
          
          if (typeof $.fn.modal !== 'undefined') {
            $('#imageModal').modal('show');
          } else {
            $('#imageModal').css('display', 'block').addClass('show');
          }
        }
      });
      
      // Close modal functionality
      $('.close, .modal').on('click', function(e) {
        if (e.target === this) {
          $('#imageModal').modal('hide').css('display', 'none').removeClass('show');
        }
      });
      
      // Escape key to close modal
      $(document).on('keyup', function(e) {
        if (e.keyCode === 27) { // ESC key
          $('#imageModal').modal('hide').css('display', 'none').removeClass('show');
        }
      });
      
      // ================================================================
      // ENHANCED LINK STYLING AND RESOURCE CARDS
      // ================================================================
      
      // Enhanced link styling for YouTube, OpenLearning and external resources
      function enhanceResourceLinks() {
        // Style YouTube links in learning resources
        $('.learning-resources-content a[href*="youtube.com"], .learning-resources-content a[href*="youtu.be"]').each(function() {
          var $link = $(this);
          if (!$link.hasClass('resource-card')) {
            $link.addClass('youtube-link');
          }
        });
        
        // Style OpenLearning links in learning resources
        $('.learning-resources-content a[href*="openlearning.unesco.org"]').each(function() {
          var $link = $(this);
          if (!$link.hasClass('resource-card')) {
            $link.addClass('openlearning-link');
            
            // Check if logo image is available
            var img = new Image();
            img.onload = function() {
              $link.addClass('has-logo');
            };
            img.onerror = function() {
              $link.removeClass('has-logo');
            };
            img.src = '/openlearning.png';
          }
        });
        
        // Style blog and tutorial links in installation
        $('.installation-content a[href*="blog"], .installation-content a[href*="tutorial"]').each(function() {
          var $link = $(this);
          if (!$link.hasClass('resource-card')) {
            $link.addClass('blog-link');
          }
        });
      }
      
      // ================================================================
      // IMAGE LOADING AND HOVER EFFECTS
      // ================================================================
      
      // Add loading animation for images
      $('.gallery-image').on('load', function() {
        $(this).addClass('loaded').css('opacity', '1');
      });
      
      // Ensure images are clickable
      $('.gallery-image').css('cursor', 'pointer');
      
      // Add hover effects
      $('.gallery-image-item').hover(
        function() {
          $(this).find('.image-overlay').css('opacity', '1');
        },
        function() {
          $(this).find('.image-overlay').css('opacity', '0');
        }
      );
      
      // ================================================================
      // FILE UPLOAD FUNCTIONALITY FOR EDIT VIEW
      // ================================================================
      
      // File upload functionality for edit forms
      function initializeFileUploads() {
        // General image upload handling
        $('.upload-zone').on('click', function(e) {
          if (e.target === this || $(e.target).hasClass('upload-zone-content')) {
            $(this).find('input[type="file"]').click();
          }
        });
        
        // Drag and drop functionality
        $('.upload-zone').on('dragover', function(e) {
          e.preventDefault();
          $(this).addClass('dragover');
        });
        
        $('.upload-zone').on('dragleave', function(e) {
          e.preventDefault();
          $(this).removeClass('dragover');
        });
        
        $('.upload-zone').on('drop', function(e) {
          e.preventDefault();
          $(this).removeClass('dragover');
          
          const files = e.originalEvent.dataTransfer.files;
          if (files.length > 0) {
            const fileInput = $(this).find('input[type="file"]')[0];
            fileInput.files = files;
            $(fileInput).trigger('change');
          }
        });
        
        // File input change handler
        $('input[type="file"]').on('change', function() {
          const files = this.files;
          if (files && files.length > 0) {
            const file = files[0];
            const $uploadZone = $(this).closest('.upload-zone');
            
            // Show preview for images
            if (file.type.startsWith('image/')) {
              const reader = new FileReader();
              reader.onload = function(e) {
                showImagePreview($uploadZone, e.target.result, file.name);
              };
              reader.readAsDataURL(file);
            }
          }
        });
        
        // Remove image functionality
        $(document).on('click', '.remove-image', function(e) {
          e.preventDefault();
          e.stopPropagation();
          
          const $uploadZone = $(this).closest('.upload-zone');
          const $fileInput = $uploadZone.find('input[type="file"]');
          
          // Clear the file input
          $fileInput.val('');
          
          // Reset upload zone to original state
          resetUploadZone($uploadZone);
        });
      }
      
      function showImagePreview($uploadZone, imageSrc, fileName) {
        const isLogo = $uploadZone.hasClass('logo-upload-zone');
        const logoText = isLogo ? '<div class="upload-note">Will be automatically resized to 200x80px</div>' : '';
        
        const previewHtml = `
          <div class="image-preview">
            <img src="${imageSrc}" alt="${fileName}" class="preview-image">
            <div class="image-info">
              <div class="file-name">${fileName}</div>
              ${logoText}
              <button type="button" class="btn btn-sm btn-danger remove-image">
                <i class="fa fa-times"></i> Remove
              </button>
            </div>
          </div>
        `;
        
        $uploadZone.html(previewHtml);
        $uploadZone.addClass('has-preview');
      }
      
      function resetUploadZone($uploadZone) {
        const isLogo = $uploadZone.hasClass('logo-upload-zone');
        const icon = isLogo ? 'fa-picture-o' : 'fa-upload';
        const title = isLogo ? 'Upload Logo Image' : 'Upload Images';
        const subtitle = isLogo ? 'Drag and drop or click to upload logo' : 'Drag and drop or click to upload images';
        const note = isLogo ? 'Logo will be automatically resized to 200x80 pixels' : 'Supported formats: JPG, PNG, GIF';
        
        const originalHtml = `
          <div class="upload-zone-content">
            <i class="fa ${icon}"></i>
            <h4>${title}</h4>
            <p>${subtitle}</p>
            <small class="text-muted">${note}</small>
          </div>
          <input type="file" class="file-input" accept="image/*" ${isLogo ? '' : 'multiple'}>
        `;
        
        $uploadZone.html(originalHtml);
        $uploadZone.removeClass('has-preview');
      }
      
      // ================================================================
      // INITIALIZATION
      // ================================================================
      
      // Initialize all functionality
      enhanceResourceLinks();
      initializeFileUploads();
      
      // Initialize tooltips if Bootstrap is available
      if (typeof $().tooltip === 'function') {
        $('[data-toggle="tooltip"]').tooltip();
      }
      
      // Re-run enhancement if content is dynamically loaded
      setTimeout(enhanceResourceLinks, 1000);
      
      // Debug info
      console.log('Open Source Software functionality initialized');
      console.log('Gallery images found:', $('.gallery-image').length);
      console.log('Multi-select dropdowns found:', $('.multi-select-dropdown').length);
      console.log('Upload zones found:', $('.upload-zone').length);
      
    }); // End document ready
    
  }); // End waitForJQuery
  
})(); // End main function