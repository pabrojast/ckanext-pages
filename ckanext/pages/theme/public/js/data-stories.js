/**
 * Data Stories JavaScript
 * Provides interactive functionality for data stories
 */

(function (factory) {
  if (typeof define === 'function' && define.amd) {
    // AMD/RequireJS
    define(['jquery'], function ($) {
      factory($, window, document);
    });
  } else {
    // Fallback: wait until DOM ready so jQuery is likely available
    var initWhenReady = function () {
      if (window.jQuery) {
        factory(window.jQuery, window, document);
      } else {
        // Retry after a short delay if jQuery still loading
        setTimeout(initWhenReady, 50);
      }
    };

    if (document.readyState === 'complete' || document.readyState === 'interactive') {
      initWhenReady();
    } else {
      document.addEventListener('DOMContentLoaded', initWhenReady);
    }
  }
})(function ($, window, document) {
  'use strict';

  // Namespace for data stories functionality
  var DataStories = {

    /**
     * Initialize all data stories functionality
     */
    init: function () {
      this.initSectionEditor();
      this.initSearchFilters();
      this.initMarkdownEditor();
      this.initTerriaConfig();
      this.initSlugGenerator();
      this.initSectionReordering();
    },

    /**
     * Section Editor - Add/Remove sections dynamically
     */
    initSectionEditor: function () {
      var self = this;
      var sectionIndex = $('#sections-container .section-editor').length;

      // Add new section
      $('#add-section-btn').on('click', function () {
        var template = $('#section-template').html();
        if (!template) {
          console.error('Section template not found');
          return;
        }

        var $newSection = $(template);

        // Update section index in field names
        $newSection.find('[name*="sections"]').each(function () {
          var name = $(this).attr('name');
          if (name) {
            $(this).attr('name', name.replace('[0]', '[' + sectionIndex + ']'));
          }
        });

        // Update IDs to ensure uniqueness
        $newSection.find('[id*="terria"]').each(function () {
          var id = $(this).attr('id');
          if (id) {
            $(this).attr('id', id.replace('new', 'section-' + sectionIndex));
          }
        });

        // Append to container
        $('#sections-container').append($newSection);
        sectionIndex++;

        // Scroll to new section
        $newSection[0].scrollIntoView({ behavior: 'smooth', block: 'center' });

        // Show notification
        self.showNotification('Section added', 'success');
      });

      // Remove section
      $(document).on('click', '.remove-section-btn', function () {
        var $section = $(this).closest('.section-editor');

        // Confirm deletion
        if (confirm('Are you sure you want to remove this section?')) {
          $section.fadeOut(300, function () {
            $(this).remove();
            self.showNotification('Section removed', 'info');
          });
        }
      });

      // Section type change handler
      $(document).on('change', '.section-type-select', function () {
        var sectionType = $(this).val();
        var $section = $(this).closest('.section-editor');

        // Update section title in panel header
        var defaultTitle = self.getSectionDefaultTitle(sectionType);
        $section.find('.panel-title').text(defaultTitle);

        // Optionally auto-fill title field
        var $titleInput = $section.find('input[name*="[title]"]');
        if (!$titleInput.val()) {
          $titleInput.val(defaultTitle);
        }
      });
    },

    /**
     * Get default title for section type
     */
    getSectionDefaultTitle: function (sectionType) {
      var titles = {
        'introduction': 'Introduction',
        'research_question': 'Research Question',
        'study_area': 'Study Area',
        'data_sources': 'Data Sources',
        'methodology': 'Methodology',
        'spatial_analysis': 'Spatial Analysis',
        'results': 'Results',
        'discussion': 'Discussion',
        'conclusions': 'Conclusions',
        'references': 'References',
        'acknowledgments': 'Acknowledgments',
        'custom': 'Custom Section'
      };
      return titles[sectionType] || sectionType.replace(/_/g, ' ').replace(/\b\w/g, function (l) {
        return l.toUpperCase();
      });
    },

    /**
     * Search and Filters
     */
    initSearchFilters: function () {
      var self = this;

      // Live search
      $('#story-search').on('input', function () {
        var query = $(this).val().toLowerCase();
        self.filterStories(query);
      });

      // Status filter
      $('#status-filter').on('change', function () {
        var status = $(this).val();
        self.filterStoriesByStatus(status);
      });

      // Organization filter
      $('#organization-filter').on('change', function () {
        var orgId = $(this).val();
        self.filterStoriesByOrganization(orgId);
      });

      // Clear filters
      $('#clear-filters-btn').on('click', function () {
        $('#story-search').val('');
        $('#status-filter').val('');
        $('#organization-filter').val('');
        $('.story-card').show();
        self.showNotification('Filters cleared', 'info');
      });
    },

    /**
     * Filter stories by search query
     */
    filterStories: function (query) {
      $('.story-card').each(function () {
        var $card = $(this);
        var title = $card.find('.story-card-title').text().toLowerCase();
        var abstract = $card.find('.story-card-abstract').text().toLowerCase();

        if (title.indexOf(query) !== -1 || abstract.indexOf(query) !== -1) {
          $card.show();
        } else {
          $card.hide();
        }
      });

      this.updateResultsCount();
    },

    /**
     * Filter stories by status
     */
    filterStoriesByStatus: function (status) {
      if (!status) {
        $('.story-card').show();
      } else {
        $('.story-card').each(function () {
          var $card = $(this);
          var cardStatus = $card.data('status');
          if (cardStatus === status) {
            $card.show();
          } else {
            $card.hide();
          }
        });
      }

      this.updateResultsCount();
    },

    /**
     * Filter stories by organization
     */
    filterStoriesByOrganization: function (orgId) {
      if (!orgId) {
        $('.story-card').show();
      } else {
        $('.story-card').each(function () {
          var $card = $(this);
          var cardOrgId = $card.data('organization');
          if (cardOrgId === orgId) {
            $card.show();
          } else {
            $card.hide();
          }
        });
      }

      this.updateResultsCount();
    },

    /**
     * Update results count display
     */
    updateResultsCount: function () {
      var visibleCount = $('.story-card:visible').length;
      var totalCount = $('.story-card').length;
      $('#results-count').text(visibleCount + ' of ' + totalCount + ' stories');
    },

    /**
     * Markdown Editor Enhancement
     */
    initMarkdownEditor: function () {
      $('.markdown-editor').each(function () {
        var $editor = $(this);

        // Add toolbar if needed
        // For now, just add some helpful attributes
        $editor.attr('spellcheck', 'true');

        // Add preview functionality
        var $previewBtn = $('<button type="button" class="btn btn-sm btn-default">Preview</button>');
        var $previewDiv = $('<div class="markdown-preview" style="display:none; margin-top:10px; padding:15px; border:1px solid #ddd; border-radius:4px;"></div>');

        $editor.after($previewDiv);
        $editor.after($previewBtn);

        $previewBtn.on('click', function () {
          var markdown = $editor.val();
          if ($previewDiv.is(':visible')) {
            $previewDiv.hide();
            $previewBtn.text('Preview');
          } else {
            // Simple markdown rendering (could be enhanced with marked.js)
            var html = markdown
              .replace(/^### (.*$)/gim, '<h3>$1</h3>')
              .replace(/^## (.*$)/gim, '<h2>$1</h2>')
              .replace(/^# (.*$)/gim, '<h1>$1</h1>')
              .replace(/\*\*(.*)\*\*/gim, '<strong>$1</strong>')
              .replace(/\*(.*)\*/gim, '<em>$1</em>')
              .replace(/\n/gim, '<br>');

            $previewDiv.html(html).show();
            $previewBtn.text('Hide Preview');
          }
        });
      });
    },

    /**
     * Terria Configuration Helpers
     */
    initTerriaConfig: function () {
      var self = this;

      // Validate Terria share links
      $('input[name*="[terria_share_link]"]').on('blur', function () {
        var $input = $(this);
        var url = $input.val();

        if (url && !self.isValidTerriaUrl(url)) {
          $input.addClass('error');
          self.showNotification('Invalid Terria URL', 'warning');
        } else {
          $input.removeClass('error');
        }
      });

      // Validate Terria JSON config
      $('textarea[name*="[terria_config]"]').on('blur', function () {
        var $textarea = $(this);
        var json = $textarea.val();

        if (json) {
          try {
            JSON.parse(json);
            $textarea.removeClass('error');
          } catch (e) {
            $textarea.addClass('error');
            self.showNotification('Invalid JSON in Terria config', 'warning');
          }
        }
      });

      // Format JSON button
      $(document).on('click', '.format-json-btn', function () {
        var $textarea = $(this).siblings('textarea[name*="[terria_config]"]');
        var json = $textarea.val();

        try {
          var formatted = JSON.stringify(JSON.parse(json), null, 2);
          $textarea.val(formatted);
          self.showNotification('JSON formatted', 'success');
        } catch (e) {
          self.showNotification('Cannot format invalid JSON', 'error');
        }
      });
    },

    /**
     * Check if URL is valid Terria URL
     */
    isValidTerriaUrl: function (url) {
      try {
        var urlObj = new URL(url);
        return urlObj.hash.includes('#share=') || urlObj.hash.includes('#start=');
      } catch (e) {
        return false;
      }
    },

    /**
     * Auto-generate slug from title
     */
    initSlugGenerator: function () {
      var $title = $('#title');
      var $slug = $('#slug');

      if ($title.length && $slug.length) {
        $title.on('blur', function () {
          var title = $(this).val();

          // Only auto-generate if slug is empty or was auto-generated
          if (!$slug.val() || $slug.data('auto-generated')) {
            var slug = title
              .toLowerCase()
              .replace(/[^\w\s-]/g, '')
              .replace(/[\s_]+/g, '-')
              .replace(/^-+|-+$/g, '');

            $slug.val(slug);
            $slug.data('auto-generated', true);
          }
        });

        // Mark slug as manually edited if user types in it
        $slug.on('input', function () {
          $(this).data('auto-generated', false);
        });
      }
    },

    /**
     * Section Reordering with Drag & Drop
     */
    initSectionReordering: function () {
      var $container = $('#sections-container');

      if ($container.length && typeof $.fn.sortable === 'function') {
        $container.sortable({
          handle: '.section-drag-handle',
          placeholder: 'section-placeholder',
          axis: 'y',
          update: function (event, ui) {
            // Update order_index fields
            $container.find('.section-editor').each(function (index) {
              $(this).find('input[name*="[order_index]"]').val(index);
            });
          }
        });

        // Add drag handles
        $('.section-editor .panel-heading').prepend(
          '<span class="section-drag-handle"><i class="fa fa-bars"></i></span>'
        );
      }
    },

    /**
     * Show notification message
     */
    showNotification: function (message, type) {
      type = type || 'info';

      var $notification = $('<div class="alert alert-' + type + ' alert-dismissible" role="alert">')
        .html(
          '<button type="button" class="close" data-dismiss="alert">&times;</button>' +
          '<i class="fa fa-info-circle"></i> ' + message
        )
        .hide();

      // Add to page
      if ($('.page-header').length) {
        $('.page-header').after($notification);
      } else {
        $('body').prepend($notification);
      }

      // Show with animation
      $notification.fadeIn(300);

      // Auto-dismiss after 5 seconds
      setTimeout(function () {
        $notification.fadeOut(300, function () {
          $(this).remove();
        });
      }, 5000);
    }
  };

  // Initialize on document ready
  $(document).ready(function () {
    DataStories.init();
  });

  // Expose to global scope for external use
  window.DataStories = DataStories;

  return DataStories;
});
