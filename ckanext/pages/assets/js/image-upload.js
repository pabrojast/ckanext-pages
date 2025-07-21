/**
 * Image Upload Management Module
 * Handles image uploads, logo management, and gallery functionality
 */

(function() {
  'use strict';

  const ImageUpload = {
    uploadedImages: [],
    logoUrl: '',

    init: function() {
      this.loadUploadedImages();
      this.bindEvents();
    },

    // Load existing uploaded images from hidden input
    loadUploadedImages: function() {
      const uploadedData = $('#uploaded-images-data').val();
      if (uploadedData) {
        try {
          this.uploadedImages = JSON.parse(uploadedData);
          const self = this;
          this.uploadedImages.forEach(img => {
            self.addUploadedImagePreview(img);
          });
        } catch (e) {
          console.error('Error parsing uploaded images data:', e);
        }
      }
      
      // Load existing logo from header_image field
      const headerImage = $('#header_image').val();
      if (headerImage) {
        this.logoUrl = headerImage;
        this.showLogoPreview(headerImage);
      }
    },

    // Bind event handlers
    bindEvents: function() {
      const self = this;

      // Handle file upload
      $('#image-upload').on('change', function(e) {
        e.stopPropagation();
        const files = this.files;
        if (files.length > 0) {
          Array.from(files).forEach(file => {
            if (file.type.startsWith('image/')) {
              self.uploadImage(file, false);
            }
          });
          this.value = '';
        }
      });
      
      // Handle logo upload
      $('#logo-upload').on('change', function(e) {
        e.stopPropagation();
        const files = this.files;
        if (files.length > 0 && files[0].type.startsWith('image/')) {
          self.uploadImage(files[0], true);
          this.value = '';
        }
      });
      
      // Handle dropzone clicks
      $('#image-dropzone').on('click', function(e) {
        e.preventDefault();
        e.stopPropagation();
        $('#image-upload').trigger('click');
      });
      
      $('#logo-dropzone').on('click', function(e) {
        e.preventDefault();
        e.stopPropagation();
        $('#logo-upload').trigger('click');
      });
      
      // Handle drag and drop for image dropzone
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
        if (files.length > 0) {
          Array.from(files).forEach(file => {
            if (file.type.startsWith('image/')) {
              self.uploadImage(file, false);
            }
          });
        }
      });
      
      // Handle drag and drop for logo dropzone
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
          self.uploadImage(files[0], true);
        }
      });

      // Remove logo
      $('#remove-logo').on('click', function() {
        self.removeLogo();
      });

      // Update image data when alt text or caption changes
      $(document).on('change input', '.image-alt, .image-caption', function() {
        // Remove required-field class when alt text is provided
        if ($(this).hasClass('image-alt') && $(this).val().trim()) {
          $(this).removeClass('required-field');
        } else if ($(this).hasClass('image-alt') && !$(this).val().trim()) {
          $(this).addClass('required-field');
        }
        self.updateUploadedImagesData();
      });

      // Update upload count when images are added or removed
      $(document).on('DOMNodeInserted DOMNodeRemoved', '#uploaded-images-preview', function() {
        setTimeout(() => self.updateUploadCount(), 100);
      });
    },

    // Upload image function
    uploadImage: function(file, isLogo) {
      const self = this;
      const formData = new FormData();
      formData.append('upload', file);
      
      if (isLogo) {
        formData.append('is_logo', 'true');
        // Get checkbox value
        const addBackground = $('#add-background').is(':checked');
        if (addBackground) {
          formData.append('add_background', 'true');
        }
      }
      
      const progressId = `progress-${Date.now()}`;
      const progressHtml = `
        <div id="${progressId}" class="upload-progress">
          <p>Uploading ${file.name}...</p>
          <div class="progress">
            <div class="progress-bar" style="width: 0%"></div>
          </div>
        </div>
      `;
      
      if (isLogo) {
        $('#logo-dropzone').after(progressHtml);
      } else {
        $('#uploaded-images-preview').append(progressHtml);
      }
      
      $.ajax({
        url: '/pages_upload',
        type: 'POST',
        data: formData,
        processData: false,
        contentType: false,
        xhr: function() {
          const xhr = new window.XMLHttpRequest();
          xhr.upload.addEventListener("progress", function(evt) {
            if (evt.lengthComputable) {
              const percentComplete = (evt.loaded / evt.total) * 100;
              $(`#${progressId} .progress-bar`).css('width', percentComplete + '%');
            }
          }, false);
          return xhr;
        },
        success: function(response) {
          $(`#${progressId}`).remove();
          if (response.uploaded === 1) {
            if (isLogo) {
              self.logoUrl = response.url;
              $('#header_image').val(response.url);
              self.showLogoPreview(response.url);
            } else {
              const imageData = {
                url: response.url,
                fileName: response.fileName,
                alt: '', // Leave empty for user to provide descriptive name
                caption: ''
              };
              self.uploadedImages.push(imageData);
              self.addUploadedImagePreview(imageData);
              self.updateUploadedImagesData();
            }
          } else {
            alert('Error uploading image: ' + (response.error ? response.error.message : 'Unknown error'));
          }
        },
        error: function() {
          $(`#${progressId}`).remove();
          alert('Error uploading image. Please try again.');
        }
      });
    },

    // Show logo preview
    showLogoPreview: function(url) {
      $('#logo-preview-img').attr('src', url);
      $('#logo-preview').show();
      $('#logo-dropzone').hide();
      
      // Update header display preview
      this.updateHeaderDisplayPreview(url);
    },

    // Remove logo
    removeLogo: function() {
      this.logoUrl = '';
      $('#header_image').val('');
      $('#logo-preview').hide();
      $('#logo-dropzone').show();
      
      // Reset header display preview
      $('.preview-logo-img').each(function() {
        $(this).html('<i class="fa fa-image"></i>');
      });
    },

    // Update header display preview with logo
    updateHeaderDisplayPreview: function(logoUrl) {
      if (logoUrl) {
        $('.preview-logo-img').each(function() {
          $(this).html('<img src="' + logoUrl + '" style="max-width: 100%; max-height: 100%; object-fit: contain;">');
        });
      }
    },

    // Add uploaded image preview
    addUploadedImagePreview: function(imageData) {
      const imageId = `uploaded-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
      const altRequired = imageData.alt ? '' : 'required-field';
      const imageHtml = `
        <div class="uploaded-image-item" data-image-id="${imageId}">
          <img src="${imageData.url}" alt="${imageData.alt}" class="uploaded-image-preview">
          <div class="uploaded-image-info">
            <input type="text" class="image-alt ${altRequired}" value="${imageData.alt}" placeholder="Enter descriptive name (required)" title="Please provide a descriptive name for this image">
            <input type="text" class="image-caption" value="${imageData.caption}" placeholder="Caption (optional)">
            <div class="uploaded-image-actions">
              <button type="button" class="image-copy-url" onclick="window.ImageUpload.copyImageUrl('${imageData.url}')">
                <i class="fa fa-copy"></i> Copy URL
              </button>
              <button type="button" class="image-remove" onclick="window.ImageUpload.removeUploadedImage('${imageId}')">
                <i class="fa fa-trash"></i>
              </button>
            </div>
          </div>
        </div>
      `;
      $('#uploaded-images-preview').append(imageHtml);
      
      // Focus on the alt text field if it's empty to encourage immediate naming
      if (!imageData.alt) {
        setTimeout(() => {
          $(`[data-image-id="${imageId}"] .image-alt`).focus();
        }, 100);
      }
    },

    // Copy image URL to clipboard
    copyImageUrl: function(url) {
      navigator.clipboard.writeText(url).then(function() {
        const btn = event.target.closest('.image-copy-url');
        const originalText = btn.innerHTML;
        btn.innerHTML = '<i class="fa fa-check"></i> Copied!';
        setTimeout(() => {
          btn.innerHTML = originalText;
        }, 2000);
      });
    },

    // Remove uploaded image
    removeUploadedImage: function(imageId) {
      const $removedItem = $(`.uploaded-image-item[data-image-id="${imageId}"]`);
      const imageUrl = $removedItem.find('img').attr('src');
      $removedItem.remove();
      
      this.uploadedImages = this.uploadedImages.filter(img => img.url !== imageUrl);
      this.updateUploadedImagesData();
    },

    // Update uploaded images data
    updateUploadedImagesData: function() {
      const currentImages = [];
      $('.uploaded-image-item').each(function() {
        const $item = $(this);
        const imageData = {
          url: $item.find('img').attr('src'),
          fileName: $item.find('img').attr('src').split('/').pop(),
          alt: $item.find('.image-alt').val(),
          caption: $item.find('.image-caption').val()
        };
        currentImages.push(imageData);
      });
      
      this.uploadedImages = currentImages;
      $('#uploaded-images-data').val(JSON.stringify(this.uploadedImages));
      
      const galleryData = this.uploadedImages.map(img => ({
        type: 'uploaded',
        url: img.url,
        alt: img.alt,
        caption: img.caption
      }));
      $('#image-gallery-data').val(JSON.stringify(galleryData));
    },

    // Update upload count
    updateUploadCount: function() {
      const count = $('.uploaded-image-item').length;
      $('.upload-count').text(count);
    }
  };

  // Expose globally
  window.ImageUpload = ImageUpload;

})();
