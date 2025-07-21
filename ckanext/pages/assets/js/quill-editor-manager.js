/**
 * Quill Editor Management Module
 * Handles initialization and management of Quill WYSIWYG editors
 */

(function() {
  'use strict';

  const QuillEditorManager = {
    quillEditors: {},

    init: function() {
      // Initialize Quill editors after a short delay to ensure DOM is ready
      setTimeout(() => {
        this.initializeQuillEditors();
      }, 100);
      
      // Force hide textareas after initialization
      setTimeout(() => {
        this.forceHideQuillTextareas();
      }, 200);
      setTimeout(() => {
        this.forceHideQuillTextareas();
      }, 1000);
    },

    // Initialize all Quill editors
    initializeQuillEditors: function() {
      const self = this;
      
      // Full editor configuration for comprehensive content
      const fullToolbar = [
        [{ 'header': [1, 2, 3, false] }],
        ['bold', 'italic', 'underline', 'strike'],
        [{ 'color': [] }, { 'background': [] }],
        [{ 'list': 'ordered'}, { 'list': 'bullet' }],
        [{ 'indent': '-1'}, { 'indent': '+1' }],
        ['blockquote', 'code-block'],
        ['link'],
        ['clean'],
        [{ 'align': [] }]
      ];
      
      // Compact editor configuration for simpler content
      const compactToolbar = [
        [{ 'header': [2, 3, false] }],
        ['bold', 'italic', 'underline'],
        [{ 'list': 'ordered'}, { 'list': 'bullet' }],
        ['link'],
        ['clean']
      ];
      
      // Configuration for different field types
      const editorConfigs = {
        'content-editor': {
          placeholder: 'Detailed description of the tool, its purpose, and main water management capabilities...',
          theme: 'snow',
          modules: {
            toolbar: fullToolbar,
            history: { delay: 1000, maxStack: 50 }
          }
        },
        'technical-requirements-editor': {
          placeholder: 'System requirements, dependencies, supported platforms...',
          theme: 'snow',
          modules: {
            toolbar: compactToolbar,
            history: { delay: 1000, maxStack: 50 }
          }
        },
        'installation-instructions-editor': {
          placeholder: 'Step-by-step installation and basic usage instructions...',
          theme: 'snow',
          modules: {
            toolbar: fullToolbar,
            history: { delay: 1000, maxStack: 50 }
          }
        },
        'learning-resources-editor': {
          placeholder: 'List learning resources, tutorials, courses, and training materials...',
          theme: 'snow',
          modules: {
            toolbar: fullToolbar,
            history: { delay: 1000, maxStack: 50 }
          }
        },
        'example-applications-editor': {
          placeholder: 'Describe real-world examples and use cases...',
          theme: 'snow',
          modules: {
            toolbar: compactToolbar,
            history: { delay: 1000, maxStack: 50 }
          }
        },
        'excerpt-editor': {
          placeholder: 'Brief summary that appears in tool listings...',
          theme: 'snow',
          modules: {
            toolbar: [
              ['bold', 'italic', 'underline'],
              [{ 'list': 'ordered'}, { 'list': 'bullet' }],
              ['link'],
              ['clean']
            ],
            history: { delay: 1000, maxStack: 50 }
          }
        }
      };
      
      // Initialize each editor
      Object.keys(editorConfigs).forEach(editorId => {
        const editorElement = document.getElementById(editorId);
        if (editorElement) {
          self.initializeEditor(editorId, editorConfigs[editorId]);
        }
      });
      
      // Setup form submission handler
      this.setupFormSubmissionHandler();
      
      // Setup keyboard shortcuts and auto-save
      this.setupKeyboardShortcuts();
      this.setupAutoSave();
      
      // Setup character counter for excerpt editor
      this.setupCharacterCounter();
      
      // Expose global sync function
      window.syncAllQuillEditors = function() {
        self.syncAllEditors();
      };
    },

    // Initialize individual editor
    initializeEditor: function(editorId, config) {
      const self = this;
      const editorElement = document.getElementById(editorId);
      
      // Show loading state
      $(editorElement).addClass('quill-loading');
      
      // Get the corresponding textarea
      const textareaId = editorId.replace('-editor', '').replace(/-/g, '_');
      const textarea = document.getElementById(textareaId);
      
      // Initialize Quill
      const quill = new Quill(`#${editorId}`, config);
      
      // Set initial content from textarea
      if (textarea && textarea.value) {
        try {
          // Try to parse as HTML first, fallback to plain text
          quill.clipboard.dangerouslyPasteHTML(textarea.value);
        } catch (e) {
          quill.setText(textarea.value);
        }
      }
      
      // Force hide the textarea after initialization
      if (textarea) {
        $(textarea).css({
          'display': 'none',
          'visibility': 'hidden',
          'position': 'absolute',
          'left': '-9999px',
          'top': '-9999px',
          'width': '1px',
          'height': '1px',
          'opacity': '0',
          'z-index': '-9999'
        });
      }
      
      // Sync content back to textarea on changes
      quill.on('text-change', function() {
        if (textarea) {
          textarea.value = quill.root.innerHTML;
          $(textarea).trigger('change');
        }
      });
      
      // Store reference for later use
      this.quillEditors[editorId] = quill;
      
      // Remove loading state
      setTimeout(() => {
        $(editorElement).removeClass('quill-loading');
        console.log(`Quill editor ${editorId} initialized successfully`);
      }, 500);
      
      // Add focus/blur effects
      quill.on('selection-change', function(range) {
        if (range) {
          $(editorElement).addClass('ql-focused');
        } else {
          $(editorElement).removeClass('ql-focused');
        }
      });
      
      // Enhance accessibility
      $(editorElement).attr('role', 'textbox');
      $(editorElement).attr('aria-label', config.placeholder);
    },

    // Setup form submission handler
    setupFormSubmissionHandler: function() {
      const self = this;
      
      $('form').on('submit', function(e) {
        console.log('Form submitting, syncing Quill editors...');
        self.syncAllEditors();
      });
    },

    // Setup keyboard shortcuts
    setupKeyboardShortcuts: function() {
      const self = this;
      
      Object.keys(this.quillEditors).forEach(editorId => {
        const quill = this.quillEditors[editorId];
        
        // Add custom keyboard shortcuts
        quill.keyboard.addBinding({
          key: 's',
          ctrlKey: true
        }, function() {
          // Prevent default save dialog and sync content
          const textareaId = editorId.replace('-editor', '').replace(/-/g, '_');
          const textarea = document.getElementById(textareaId);
          if (textarea) {
            textarea.value = quill.root.innerHTML;
          }
          return false;
        });
      });
    },

    // Setup auto-save functionality
    setupAutoSave: function() {
      let autoSaveTimeout;
      
      Object.keys(this.quillEditors).forEach(editorId => {
        const quill = this.quillEditors[editorId];
        
        quill.on('text-change', function() {
          clearTimeout(autoSaveTimeout);
          autoSaveTimeout = setTimeout(() => {
            const textareaId = editorId.replace('-editor', '').replace(/-/g, '_');
            const textarea = document.getElementById(textareaId);
            if (textarea) {
              textarea.value = quill.root.innerHTML;
              // Could add visual feedback here for auto-save
            }
          }, 2000); // Auto-save after 2 seconds of inactivity
        });
      });
    },

    // Setup character counter for excerpt editor
    setupCharacterCounter: function() {
      if (this.quillEditors['excerpt-editor']) {
        const excerptQuill = this.quillEditors['excerpt-editor'];
        const $counter = $('.character-counter');
        const $currentCount = $('.current-count');
        const $counterStatus = $('.counter-status');
        const maxLength = 200;
        
        function updateCharacterCount() {
          const text = excerptQuill.getText();
          const currentLength = text.trim().length;
          
          $currentCount.text(currentLength);
          
          // Update counter visual state
          $counter.removeClass('warning over-limit');
          $counterStatus.removeClass('optimal warning over-limit');
          
          if (currentLength > maxLength) {
            $counter.addClass('over-limit');
            $counterStatus.addClass('over-limit').text('Too long');
          } else if (currentLength > maxLength * 0.8) {
            $counter.addClass('warning');
            $counterStatus.addClass('warning').text('Almost full');
          } else if (currentLength > 50) {
            $counterStatus.addClass('optimal').text('Good length');
          } else {
            $counterStatus.text('');
          }
        }
        
        // Update counter on text change
        excerptQuill.on('text-change', updateCharacterCount);
        
        // Initial count update
        setTimeout(updateCharacterCount, 100);
      }
    },

    // Sync all editors with their textareas
    syncAllEditors: function() {
      Object.keys(this.quillEditors).forEach(editorId => {
        const quill = this.quillEditors[editorId];
        const textareaId = editorId.replace('-editor', '').replace(/-/g, '_');
        const textarea = document.getElementById(textareaId);
        
        if (quill && textarea) {
          const content = quill.root.innerHTML;
          textarea.value = content;
          $(textarea).trigger('change');
          console.log(`Synced ${textareaId}: ${content.length} characters`);
        }
      });
    },

    // Force hide all Quill textareas
    forceHideQuillTextareas: function() {
      $('.quill-wrapper textarea, textarea[id="excerpt"], textarea[id="content"], textarea[id="technical_requirements"], textarea[id="installation_instructions"], textarea[id="learning_resources"], textarea[id="example_applications"]').each(function() {
        $(this).css({
          'display': 'none !important',
          'visibility': 'hidden !important',
          'position': 'absolute !important',
          'left': '-9999px !important',
          'top': '-9999px !important',
          'width': '1px !important',
          'height': '1px !important',
          'opacity': '0 !important',
          'z-index': '-9999 !important'
        }).hide();
      });
    }
  };

  // Expose globally
  window.QuillEditorManager = QuillEditorManager;

})();
