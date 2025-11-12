/**
 * Data Stories Edit Form JavaScript
 * Modular content block system aligned with rapid response
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
      
      // Wait for Quill to be available
      function waitForQuill(callback) {
        if (typeof Quill !== 'undefined') {
          callback();
        } else {
          setTimeout(function(){ waitForQuill(callback); }, 50);
        }
      }
      
      // Section management
      let sectionIndex = $('.content-section-editor').length;
      let sectionBlockCounters = {};
      let sectionQuillEditors = {};
      
      // Initialize existing sections
      $('.content-section-editor').each(function(index) {
        const sectionId = index;
        initializeSectionBlocks($(this), sectionId);
      });
      
      // Add section button
      $('#add-section-btn').on('click', function() {
        addNewSection();
      });
      
      // Remove section
      $(document).on('click', '.remove-section-btn', function() {
        if (confirm('Are you sure you want to remove this section?')) {
          $(this).closest('.content-section-editor').remove();
          updateSectionOrder();
        }
      });
      
      // Move section up
      $(document).on('click', '.move-section-up', function() {
        const $section = $(this).closest('.content-section-editor');
        const $prev = $section.prev('.content-section-editor');
        if ($prev.length) {
          $section.insertBefore($prev);
          updateSectionOrder();
        }
      });
      
      // Move section down
      $(document).on('click', '.move-section-down', function() {
        const $section = $(this).closest('.content-section-editor');
        const $next = $section.next('.content-section-editor');
        if ($next.length) {
          $section.insertAfter($next);
          updateSectionOrder();
        }
      });
      
      // Update section order
      function updateSectionOrder() {
        $('.content-section-editor').each(function(index) {
          $(this).find('.section-order').val(index);
          // Update all name attributes
          $(this).find('[name^="sections["]').each(function() {
            const name = $(this).attr('name');
            const newName = name.replace(/sections\[\d+\]/, 'sections[' + index + ']');
            $(this).attr('name', newName);
          });
        });
      }
      
      // Add new section
      function addNewSection() {
        const template = $('#section-template').html();
        if (!template) {
          console.error('Section template not found');
          return;
        }
        
        const $newSection = $(template);
        
        // Update indices
        $newSection.find('[name*="sections"]').each(function() {
          const name = $(this).attr('name');
          if (name) {
            $(this).attr('name', name.replace(/\[0\]/g, '[' + sectionIndex + ']'));
          }
        });
        
        // Update IDs
        $newSection.find('[id*="section-"]').each(function() {
          const id = $(this).attr('id');
          if (id) {
            $(this).attr('id', id.replace(/section-\d+/, 'section-' + sectionIndex));
          }
        });
        
        $('#sections-container').append($newSection);
        initializeSectionBlocks($newSection, sectionIndex);
        sectionIndex++;
      }
      
      // Initialize section blocks
      function initializeSectionBlocks($section, sectionId) {
        sectionBlockCounters[sectionId] = 0;
        sectionQuillEditors[sectionId] = {};
        
        const $blocksContainer = $section.find('.section-content-blocks');
        const blocksContainerId = 'section-' + sectionId + '-blocks';
        $blocksContainer.attr('id', blocksContainerId);
        
        // Load existing blocks from metadata or content
        loadExistingSectionBlocks($section, sectionId);
        
        // Add text block button
        $section.find('.add-text-block').on('click', function() {
          addTextBlock(sectionId);
        });
        
        // Add Terria block button
        $section.find('.add-terria-block').on('click', function() {
          addTerriaBlock(sectionId);
        });
        
        // Add media block button
        $section.find('.add-media-block').on('click', function() {
          addMediaBlock(sectionId);
        });
      }
      
      // Load existing section blocks
      function loadExistingSectionBlocks($section, sectionId) {
        const metadataField = $section.find('.section-blocks-metadata');
        const blocksMetadata = metadataField.val();
        
        if (blocksMetadata && blocksMetadata.trim()) {
          try {
            const blocks = JSON.parse(blocksMetadata);
            blocks.forEach(blockData => {
              if (blockData.type === 'text') {
                addTextBlock(sectionId, blockData.content);
              } else if (blockData.type === 'terria') {
                addTerriaBlock(sectionId, blockData);
              } else if (blockData.type === 'media') {
                addMediaBlock(sectionId, blockData);
              }
            });
          } catch (e) {
            console.warn('Error parsing blocks metadata:', e);
            // Fallback: create single text block with existing content
            const existingContent = $section.find('.section-content-field').val();
            if (existingContent && existingContent.trim()) {
              addTextBlock(sectionId, existingContent);
            }
          }
        } else {
          // No metadata, check for existing content
          const existingContent = $section.find('.section-content-field').val();
          const terriaLink = $section.find('.section-terria-link').val();
          
          if (existingContent && existingContent.trim()) {
            addTextBlock(sectionId, existingContent);
          }
          
          if (terriaLink && terriaLink.trim()) {
            addTerriaBlock(sectionId, { url: terriaLink });
          }
        }
      }
      
      // Add text block
      function addTextBlock(sectionId, content = '') {
        const blockId = 'section-' + sectionId + '-block-' + (++sectionBlockCounters[sectionId]);
        const $container = $('#section-' + sectionId + '-blocks');
        
        const html = `
          <div class="content-block" data-block-id="${blockId}" data-block-type="text">
            <div class="content-block-header">
              <h5 class="content-block-title">
                <i class="fa fa-text-width"></i>
                Text Content
              </h5>
              <div class="content-block-controls">
                <button type="button" class="btn btn-sm btn-default move-block-up" title="Move Up">
                  <i class="fa fa-chevron-up"></i>
                </button>
                <button type="button" class="btn btn-sm btn-default move-block-down" title="Move Down">
                  <i class="fa fa-chevron-down"></i>
                </button>
                <button type="button" class="btn btn-sm btn-danger delete-block" title="Delete">
                  <i class="fa fa-trash"></i>
                </button>
              </div>
            </div>
            <div class="content-block-body">
              <div class="quill-editor" id="${blockId}-editor"></div>
            </div>
          </div>
        `;
        
        $container.append(html);
        
        // Initialize Quill editor
        waitForQuill(function() {
          const quill = new Quill('#' + blockId + '-editor', {
            theme: 'snow',
            modules: {
              toolbar: [
                [{ 'header': [2, 3, false] }],
                ['bold', 'italic', 'underline'],
                [{ 'list': 'ordered'}, { 'list': 'bullet' }],
                ['link', 'image'],
                ['clean']
              ]
            },
            placeholder: 'Enter your content here...'
          });
          
          if (content) {
            quill.clipboard.dangerouslyPasteHTML(content);
          }
          
          quill.on('text-change', function() {
            updateSectionContent(sectionId);
          });
          
          sectionQuillEditors[sectionId][blockId] = quill;
        });
        
        addBlockEventListeners(blockId, sectionId);
        updateSectionContent(sectionId);
      }
      
      // Add Terria map block
      function addTerriaBlock(sectionId, data = {}) {
        const blockId = 'section-' + sectionId + '-block-' + (++sectionBlockCounters[sectionId]);
        const $container = $('#section-' + sectionId + '-blocks');
        
        const html = `
          <div class="content-block" data-block-id="${blockId}" data-block-type="terria">
            <div class="content-block-header">
              <h5 class="content-block-title">
                <i class="fa fa-map"></i>
                Terria Map
              </h5>
              <div class="content-block-controls">
                <button type="button" class="btn btn-sm btn-default move-block-up" title="Move Up">
                  <i class="fa fa-chevron-up"></i>
                </button>
                <button type="button" class="btn btn-sm btn-default move-block-down" title="Move Down">
                  <i class="fa fa-chevron-down"></i>
                </button>
                <button type="button" class="btn btn-sm btn-danger delete-block" title="Delete">
                  <i class="fa fa-trash"></i>
                </button>
              </div>
            </div>
            <div class="content-block-body">
              <div class="terria-block-form">
                <div class="form-group">
                  <label>Terria Share Link</label>
                  <input type="text" class="form-control terria-url" value="${data.url || ''}" 
                         placeholder="https://ihp-wins.unesco.org/terria/#share=abc123">
                  <small class="help-block">Paste a Terria share link or JSON config</small>
                </div>
                <div class="form-group">
                  <label>Title (optional)</label>
                  <input type="text" class="form-control terria-title" value="${data.title || ''}" 
                         placeholder="Map title">
                </div>
                <div class="form-group">
                  <button type="button" class="btn btn-sm btn-info preview-terria">
                    <i class="fa fa-eye"></i> Preview Map
                  </button>
                </div>
                <div class="terria-preview" style="display: none;"></div>
              </div>
            </div>
          </div>
        `;
        
        $container.append(html);
        addTerriaBlockEventListeners(blockId, sectionId);
        addBlockEventListeners(blockId, sectionId);
        updateSectionContent(sectionId);
      }
      
      // Add media/iframe block
      function addMediaBlock(sectionId, data = {}) {
        const blockId = 'section-' + sectionId + '-block-' + (++sectionBlockCounters[sectionId]);
        const $container = $('#section-' + sectionId + '-blocks');
        
        const html = `
          <div class="content-block" data-block-id="${blockId}" data-block-type="media">
            <div class="content-block-header">
              <h5 class="content-block-title">
                <i class="fa fa-play-circle"></i>
                Media / Iframe
              </h5>
              <div class="content-block-controls">
                <button type="button" class="btn btn-sm btn-default move-block-up" title="Move Up">
                  <i class="fa fa-chevron-up"></i>
                </button>
                <button type="button" class="btn btn-sm btn-default move-block-down" title="Move Down">
                  <i class="fa fa-chevron-down"></i>
                </button>
                <button type="button" class="btn btn-sm btn-danger delete-block" title="Delete">
                  <i class="fa fa-trash"></i>
                </button>
              </div>
            </div>
            <div class="content-block-body">
              <div class="media-block-form">
                <div class="form-group">
                  <label>URL or Embed Code</label>
                  <textarea class="form-control media-url" rows="3" placeholder="Enter URL, YouTube link, or paste embed code">${data.url || ''}</textarea>
                  <small class="help-block">
                    Examples:<br>
                    • YouTube: https://www.youtube.com/watch?v=VIDEO_ID<br>
                    • Embed code: &lt;iframe src="..." &gt;&lt;/iframe&gt;
                  </small>
                </div>
                <div class="form-group">
                  <label>Title (optional)</label>
                  <input type="text" class="form-control media-title" value="${data.title || ''}" placeholder="Media title">
                </div>
                <div class="row">
                  <div class="col-sm-6">
                    <div class="form-group">
                      <label>Width</label>
                      <input type="text" class="form-control media-width" value="${data.width || '100%'}" placeholder="100%">
                    </div>
                  </div>
                  <div class="col-sm-6">
                    <div class="form-group">
                      <label>Height (px)</label>
                      <input type="number" class="form-control media-height" value="${data.height || '400'}" placeholder="400">
                    </div>
                  </div>
                </div>
                <div class="form-group">
                  <button type="button" class="btn btn-sm btn-info preview-media">
                    <i class="fa fa-eye"></i> Preview
                  </button>
                </div>
                <div class="media-preview" style="display: none;"></div>
              </div>
            </div>
          </div>
        `;
        
        $container.append(html);
        addMediaBlockEventListeners(blockId, sectionId);
        addBlockEventListeners(blockId, sectionId);
        updateSectionContent(sectionId);
      }
      
      // Add block event listeners (move, delete)
      function addBlockEventListeners(blockId, sectionId) {
        const $block = $('[data-block-id="' + blockId + '"]');
        
        $block.find('.move-block-up').on('click', function() {
          const $prev = $block.prev('.content-block');
          if ($prev.length) {
            $block.insertBefore($prev);
            updateSectionContent(sectionId);
          }
        });
        
        $block.find('.move-block-down').on('click', function() {
          const $next = $block.next('.content-block');
          if ($next.length) {
            $block.insertAfter($next);
            updateSectionContent(sectionId);
          }
        });
        
        $block.find('.delete-block').on('click', function() {
          if (confirm('Are you sure you want to delete this block?')) {
            const editorId = blockId + '-editor';
            if (sectionQuillEditors[sectionId] && sectionQuillEditors[sectionId][editorId]) {
              delete sectionQuillEditors[sectionId][editorId];
            }
            $block.remove();
            updateSectionContent(sectionId);
          }
        });
      }
      
      // Add Terria block event listeners
      function addTerriaBlockEventListeners(blockId, sectionId) {
        const $block = $('[data-block-id="' + blockId + '"]');
        
        $block.find('.terria-url, .terria-title').on('input', function() {
          updateSectionContent(sectionId);
        });
        
        $block.find('.preview-terria').on('click', function() {
          const $preview = $block.find('.terria-preview');
          const url = $block.find('.terria-url').val();
          
          if ($preview.is(':visible')) {
            $preview.hide();
          } else if (url) {
            const iframe = `<iframe src="${url}" frameborder="0" allowfullscreen mozallowfullscreen webkitallowfullscreen></iframe>`;
            $preview.html(iframe).show();
          } else {
            alert('Please enter a Terria share link first');
          }
        });
      }
      
      // Add media block event listeners
      function addMediaBlockEventListeners(blockId, sectionId) {
        const $block = $('[data-block-id="' + blockId + '"]');
        
        $block.find('.media-url, .media-title, .media-width, .media-height').on('input', function() {
          updateSectionContent(sectionId);
        });
        
        $block.find('.preview-media').on('click', function() {
          const $preview = $block.find('.media-preview');
          const url = $block.find('.media-url').val();
          const width = $block.find('.media-width').val() || '100%';
          const height = $block.find('.media-height').val() || '400';
          
          if ($preview.is(':visible')) {
            $preview.hide();
          } else if (url) {
            const processedContent = processContentForEmbed(url, width, height);
            $preview.html(processedContent).show();
          } else {
            alert('Please enter a URL or embed code first');
          }
        });
      }
      
      // Process content for embed
      function processContentForEmbed(content, width, height) {
        if (!content || !content.trim()) return '';
        
        content = content.trim();
        
        // Check if it's already an embed code
        if (content.includes('<iframe') || content.includes('<embed')) {
          return content;
        }
        
        // Check if it's a YouTube URL
        const youtubeMatch = content.match(/(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([a-zA-Z0-9_-]+)/);
        if (youtubeMatch) {
          const videoId = youtubeMatch[1];
          return `<iframe src="https://www.youtube.com/embed/${videoId}" width="${width}" height="${height}" frameborder="0" allowfullscreen></iframe>`;
        }
        
        // For any other URL, create a regular iframe
        return `<iframe src="${content}" width="${width}" height="${height}" frameborder="0" allowfullscreen></iframe>`;
      }
      
      // Update section content from blocks
      function updateSectionContent(sectionId) {
        const $section = $('.content-section-editor').eq(sectionId);
        if (!$section.length) return;
        
        const $container = $section.find('.section-content-blocks');
        let contentHtml = '';
        const blocksMetadata = [];
        let hasTerriaMap = false;
        let terriaLink = '';
        
        $container.find('.content-block').each(function() {
          const $block = $(this);
          const blockId = $block.data('block-id');
          const blockType = $block.data('block-type');
          
          if (blockType === 'text') {
            const editorId = blockId + '-editor';
            const quill = sectionQuillEditors[sectionId] && sectionQuillEditors[sectionId][editorId];
            if (quill) {
              const html = quill.root.innerHTML;
              const text = quill.getText().trim();
              if (text) {
                contentHtml += html + '\n\n';
                blocksMetadata.push({
                  type: 'text',
                  content: html
                });
              }
            }
          } else if (blockType === 'terria') {
            const url = $block.find('.terria-url').val();
            const title = $block.find('.terria-title').val();
            
            if (url) {
              if (title) {
                contentHtml += `<h3>${title}</h3>\n`;
              }
              contentHtml += `<iframe src="${url}" width="100%" height="600" frameborder="0" allowfullscreen mozallowfullscreen webkitallowfullscreen></iframe>\n\n`;
              
              blocksMetadata.push({
                type: 'terria',
                url: url,
                title: title
              });
              
              if (!hasTerriaMap) {
                hasTerriaMap = true;
                terriaLink = url;
              }
            }
          } else if (blockType === 'media') {
            const url = $block.find('.media-url').val();
            const title = $block.find('.media-title').val();
            const width = $block.find('.media-width').val() || '100%';
            const height = $block.find('.media-height').val() || '400';
            
            if (url) {
              if (title) {
                contentHtml += `<h3>${title}</h3>\n`;
              }
              contentHtml += processContentForEmbed(url, width, height) + '\n\n';
              
              blocksMetadata.push({
                type: 'media',
                url: url,
                title: title,
                width: width,
                height: height
              });
            }
          }
        });
        
        // Update hidden fields
        $section.find('.section-content-field').val(contentHtml);
        $section.find('.section-blocks-metadata').val(JSON.stringify(blocksMetadata));
        
        // Update Terria link for backward compatibility
        if (terriaLink) {
          $section.find('.section-terria-link').val(terriaLink);
        }
      }
      
      // Auto-generate slug from title
      $('#title').on('blur', function() {
        const title = $(this).val();
        const $slug = $('#slug');
        
        if (!title) return;
        
        if (!$slug.val() || $slug.data('auto-generated')) {
          const generatedSlug = title.toLowerCase()
            .replace(/[^\w\s-]/g, '')
            .replace(/[\s_]+/g, '-')
            .replace(/^-+|-+$/g, '');
          
          $slug.val(generatedSlug);
          $slug.data('auto-generated', true);
        }
      });
      
      $('#slug').on('input', function() {
        $(this).data('auto-generated', false);
      });
      
      // Form submission
      $('form').on('submit', function(e) {
        // Update all section content before submit
        $('.content-section-editor').each(function(index) {
          updateSectionContent(index);
        });
      });
      
      // ========================================
      // IMAGE UPLOAD FUNCTIONALITY
      // ========================================
      
      let uploadedImages = [];
      
      // Load existing uploaded images
      function loadUploadedImages() {
        const uploadedData = $('#uploaded-images-data').val();
        if (uploadedData) {
          try {
            uploadedImages = JSON.parse(uploadedData);
            uploadedImages.forEach(img => {
              addUploadedImagePreview(img);
            });
          } catch (e) {
            console.error('Error parsing uploaded images data:', e);
          }
        }
      }
      
      // Handle file upload
      $('#image-upload').on('change', function(e) {
        e.stopPropagation();
        const files = this.files;
        if (files.length > 0) {
          Array.from(files).forEach(file => {
            if (file.type.startsWith('image/')) {
              uploadImage(file);
            }
          });
          this.value = '';
        }
      });
      
      // Handle dropzone click
      $('#image-dropzone').on('click', function(e) {
        e.preventDefault();
        e.stopPropagation();
        $('#image-upload').trigger('click');
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
        if (files.length > 0) {
          Array.from(files).forEach(file => {
            if (file.type.startsWith('image/')) {
              uploadImage(file);
            }
          });
        }
      });
      
      // Upload image function
      function uploadImage(file) {
        const formData = new FormData();
        formData.append('upload', file);
        
        // Show upload progress
        const progressId = 'progress-' + Date.now();
        const progressHtml = `
          <div id="${progressId}" class="upload-progress">
            <p>Uploading ${file.name}...</p>
            <div class="progress">
              <div class="progress-bar" style="width: 0%"></div>
            </div>
          </div>
        `;
        $('#uploaded-images-preview').append(progressHtml);
        
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
                $('#' + progressId + ' .progress-bar').css('width', percentComplete + '%');
              }
            }, false);
            return xhr;
          },
          success: function(response) {
            $('#' + progressId).remove();
            if (response.uploaded === 1) {
              const imageData = {
                url: response.url,
                fileName: response.fileName,
                alt: file.name.replace(/\.[^/.]+$/, ""),
                caption: ''
              };
              uploadedImages.push(imageData);
              addUploadedImagePreview(imageData);
              updateUploadedImagesData();
            } else {
              alert('Error uploading image: ' + (response.error ? response.error.message : 'Unknown error'));
            }
          },
          error: function() {
            $('#' + progressId).remove();
            alert('Error uploading image. Please try again.');
          }
        });
      }
      
      // Add uploaded image preview
      function addUploadedImagePreview(imageData) {
        const imageId = 'uploaded-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9);
        const imageHtml = `
          <div class="uploaded-image-item" data-image-id="${imageId}">
            <img src="${imageData.url}" alt="${imageData.alt}" class="uploaded-image-preview">
            <div class="uploaded-image-info">
              <input type="text" class="image-alt form-control" value="${imageData.alt}" placeholder="Alt text">
              <input type="text" class="image-caption form-control" value="${imageData.caption}" placeholder="Caption (optional)">
              <div class="uploaded-image-actions">
                <button type="button" class="btn btn-sm btn-info image-copy-url" data-url="${imageData.url}">
                  <i class="fa fa-copy"></i> Copy URL
                </button>
                <button type="button" class="btn btn-sm btn-danger image-remove" data-image-id="${imageId}">
                  <i class="fa fa-trash"></i>
                </button>
              </div>
            </div>
          </div>
        `;
        $('#uploaded-images-preview').append(imageHtml);
      }
      
      // Copy image URL to clipboard
      $(document).on('click', '.image-copy-url', function() {
        const url = $(this).data('url');
        navigator.clipboard.writeText(url).then(function() {
          const $btn = $(event.target).closest('.image-copy-url');
          const originalText = $btn.html();
          $btn.html('<i class="fa fa-check"></i> Copied!');
          setTimeout(() => {
            $btn.html(originalText);
          }, 2000);
        });
      });
      
      // Remove uploaded image
      $(document).on('click', '.image-remove', function() {
        const imageId = $(this).data('image-id');
        const $item = $('[data-image-id="' + imageId + '"]');
        const imageUrl = $item.find('img').attr('src');
        
        $item.remove();
        uploadedImages = uploadedImages.filter(img => img.url !== imageUrl);
        updateUploadedImagesData();
      });
      
      // Update uploaded images data
      function updateUploadedImagesData() {
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
        uploadedImages = currentImages;
        $('#uploaded-images-data').val(JSON.stringify(uploadedImages));
      }
      
      // Update image data when alt text or caption changes
      $(document).on('change input', '.image-alt, .image-caption', function() {
        updateUploadedImagesData();
      });
      
      // Load existing images on page load
      loadUploadedImages();
      
      console.log('Data Stories editor initialized successfully');
    });
  });
})();
