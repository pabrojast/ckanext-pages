/**
 * CRIDA Case Study Edit Form JavaScript
 * Handles coordinate input, dataset search, theme/partner management
 */

(function($) {
  'use strict';

  var CRIDAEdit = {
    selectedDatasets: [],
    selectedDocuments: [],

    init: function() {
      this.initCoordinateInputs();
      this.initThemesSelector();
      this.initPartnersInput();
      this.initDatasetSearch();
      this.initDocumentUpload();
      this.initSubmissionButtons();
      this.initHighlightsRepeater();
      this.initCategoryCheckboxes();
      this.loadExistingData();
    },

    /**
     * Initialize coordinate input fields with validation.
     */
    initCoordinateInputs: function() {
      var $lat = $('#field-latitude');
      var $lon = $('#field-longitude');

      if (!$lat.length || !$lon.length) return;

      // Validate on input
      $lat.on('input', function() {
        var val = parseFloat($(this).val());
        if (isNaN(val) || val < -90 || val > 90) {
          $(this).closest('.form-group').addClass('has-error');
        } else {
          $(this).closest('.form-group').removeClass('has-error');
        }
      });

      $lon.on('input', function() {
        var val = parseFloat($(this).val());
        if (isNaN(val) || val < -180 || val > 180) {
          $(this).closest('.form-group').addClass('has-error');
        } else {
          $(this).closest('.form-group').removeClass('has-error');
        }
      });

      // Simple map preview using OpenStreetMap image
      var updateMapPreview = function() {
        var lat = parseFloat($lat.val());
        var lon = parseFloat($lon.val());
        var $preview = $('#crida-coord-preview');

        if (!$preview.length) return;

        if (!isNaN(lat) && !isNaN(lon) && lat >= -90 && lat <= 90 && lon >= -180 && lon <= 180) {
          var osmUrl = 'https://www.openstreetmap.org/export/embed.html?bbox=' +
            (lon - 2) + ',' + (lat - 2) + ',' + (lon + 2) + ',' + (lat + 2) +
            '&layer=mapnik&marker=' + lat + ',' + lon;
          $preview.html(
            '<iframe src="' + osmUrl + '" style="width:100%;height:250px;border:1px solid #ddd;' +
            'border-radius:6px;" loading="lazy"></iframe>' +
            '<small class="text-muted" style="display:block;margin-top:0.3rem;">' +
            '<i class="fa fa-map-marker"></i> ' + lat.toFixed(4) + ', ' + lon.toFixed(4) +
            '</small>'
          );
        } else {
          $preview.html(
            '<div style="width:100%;height:250px;background:#f0f4f8;border-radius:6px;' +
            'display:flex;align-items:center;justify-content:center;color:#999;">' +
            '<i class="fa fa-map-marker" style="font-size:2rem;margin-right:0.5rem;"></i>' +
            'Enter coordinates to see map preview</div>'
          );
        }
      };

      $lat.on('change', updateMapPreview);
      $lon.on('change', updateMapPreview);

      // Initial render
      updateMapPreview();
    },

    /**
     * Initialize themes multi-select with checkboxes.
     */
    initThemesSelector: function() {
      var $container = $('#crida-themes-container');
      if (!$container.length) return;

      var themes = [
        'Drought', 'Urban Water Security', 'Flood',
        'Nature Based Solutions', 'Transboundary Water',
        'Demand Growth', 'Shared Vision Planning',
        'Ecosystem Services', 'Climate Adaptation',
        'Water-Energy Nexus',
      ];

      // Get existing values
      var existingVal = $('#field-themes').val() || '[]';
      var selected = [];
      try {
        selected = JSON.parse(existingVal);
      } catch (e) {
        selected = [];
      }

      var html = '<div class="crida-themes-checkboxes">';
      themes.forEach(function(theme) {
        var checked = selected.indexOf(theme) !== -1 ? ' checked' : '';
        html += '<label class="crida-theme-checkbox">' +
          '<input type="checkbox" value="' + theme + '"' + checked + '> ' +
          '<span>' + theme + '</span>' +
          '</label>';
      });
      html += '</div>';

      $container.html(html);

      // Sync to hidden field on change
      $container.on('change', 'input[type="checkbox"]', function() {
        var vals = [];
        $container.find('input:checked').each(function() {
          vals.push($(this).val());
        });
        $('#field-themes').val(JSON.stringify(vals));
      });
    },

    /**
     * Initialize partners tag-style input.
     */
    initPartnersInput: function() {
      var $input = $('#crida-partner-input');
      var $container = $('#crida-partners-container');
      var $hidden = $('#field-partners');

      if (!$input.length) return;

      var partners = [];
      try {
        partners = JSON.parse($hidden.val() || '[]');
      } catch (e) {
        partners = [];
      }

      var renderTags = function() {
        var html = '';
        partners.forEach(function(p, i) {
          html += '<span class="crida-partner-tag">' +
            '<i class="fa fa-building-o"></i> ' + p +
            ' <span class="remove-btn" data-idx="' + i + '">&times;</span>' +
            '</span>';
        });
        $container.html(html);
        $hidden.val(JSON.stringify(partners));
      };

      $input.on('keydown', function(e) {
        if (e.key === 'Enter' || e.key === ',') {
          e.preventDefault();
          var val = $(this).val().trim();
          if (val && partners.indexOf(val) === -1) {
            partners.push(val);
            renderTags();
          }
          $(this).val('');
        }
      });

      $container.on('click', '.remove-btn', function() {
        var idx = parseInt($(this).data('idx'));
        partners.splice(idx, 1);
        renderTags();
      });

      renderTags();
    },

    /**
     * Initialize dataset search and linking.
     */
    initDatasetSearch: function() {
      var self = this;
      var $search = $('#crida-dataset-search');
      var $results = $('#crida-dataset-results');
      var $selected = $('#crida-selected-datasets');
      var $hidden = $('#field-related-datasets-json');

      if (!$search.length) return;

      // Load existing datasets
      try {
        self.selectedDatasets = JSON.parse($hidden.val() || '[]');
      } catch (e) {
        self.selectedDatasets = [];
      }

      var renderSelected = function() {
        var html = '';
        self.selectedDatasets.forEach(function(ds, i) {
          html += '<span class="crida-selected-dataset">' +
            '<i class="fa fa-database"></i> ' + (ds.title || ds.id) +
            ' <span class="remove-btn" data-idx="' + i + '">&times;</span>' +
            '</span>';
        });
        $selected.html(html);
        $hidden.val(JSON.stringify(self.selectedDatasets));
      };

      var searchTimeout;
      $search.on('keyup', function() {
        var q = $(this).val().trim();
        if (q.length < 2) {
          $results.removeClass('active').empty();
          return;
        }

        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(function() {
          $.ajax({
            url: '/api/3/action/package_search',
            data: { q: q, rows: 10 },
            success: function(data) {
              var results = (data.result && data.result.results) || [];
              var html = '';
              results.forEach(function(pkg) {
                // Skip already selected
                var isSelected = self.selectedDatasets.some(function(s) {
                  return s.id === pkg.id;
                });
                if (isSelected) return;

                html += '<div class="crida-dataset-result-item" data-id="' +
                  pkg.id + '" data-title="' + (pkg.title || '').replace(/"/g, '&quot;') + '">' +
                  '<i class="fa fa-database"></i> ' + (pkg.title || pkg.name) +
                  '</div>';
              });

              if (!html) {
                html = '<div class="crida-dataset-result-item" style="color:#999;">No results found</div>';
              }

              $results.html(html).addClass('active');
            },
            error: function() {
              $results.html(
                '<div class="crida-dataset-result-item" style="color:#999;">Search error</div>'
              ).addClass('active');
            },
          });
        }, 300);
      });

      $results.on('click', '.crida-dataset-result-item', function() {
        var id = $(this).data('id');
        var title = $(this).data('title');
        if (id && !self.selectedDatasets.some(function(s) { return s.id === id; })) {
          self.selectedDatasets.push({ id: id, title: title });
          renderSelected();
        }
        $results.removeClass('active').empty();
        $search.val('');
      });

      $selected.on('click', '.remove-btn', function() {
        var idx = parseInt($(this).data('idx'));
        self.selectedDatasets.splice(idx, 1);
        renderSelected();
      });

      // Close results on click outside
      $(document).on('click', function(e) {
        if (!$(e.target).closest('.crida-dataset-selector').length) {
          $results.removeClass('active');
        }
      });

      renderSelected();
    },

    /**
     * Initialize document upload handling.
     */
    initDocumentUpload: function() {
      var self = this;
      var $input = $('#crida-document-upload');
      var $list = $('#crida-documents-list');
      var $hidden = $('#field-related-documents-json');

      if (!$input.length) return;

      try {
        self.selectedDocuments = JSON.parse($hidden.val() || '[]');
      } catch (e) {
        self.selectedDocuments = [];
      }

      var renderDocuments = function() {
        var html = '';
        self.selectedDocuments.forEach(function(doc, i) {
          html += '<div class="crida-document-item">' +
            '<i class="fa fa-file-o"></i> ' +
            '<span>' + (doc.name || doc.url || 'Document') + '</span>' +
            ' <span class="remove-btn" data-idx="' + i + '">&times;</span>' +
            '</div>';
        });
        $list.html(html);
        $hidden.val(JSON.stringify(self.selectedDocuments));
      };

      $input.on('change', function() {
        var files = this.files;
        if (!files.length) return;

        for (var i = 0; i < files.length; i++) {
          var file = files[i];
          var formData = new FormData();
          formData.append('upload', file);
          formData.append('image_url', '');

          $.ajax({
            url: '/api/3/action/ckanext_pages_upload',
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            success: function(response) {
              var url = response.result && response.result.url;
              if (url) {
                self.selectedDocuments.push({
                  name: file.name,
                  url: url,
                  type: file.type,
                  size: file.size,
                });
                renderDocuments();
              }
            },
            error: function() {
              console.error('CRIDA: Document upload failed for', file.name);
            },
          });
        }

        // Reset file input
        $(this).val('');
      });

      $list.on('click', '.remove-btn', function() {
        var idx = parseInt($(this).data('idx'));
        self.selectedDocuments.splice(idx, 1);
        renderDocuments();
      });

      renderDocuments();
    },

    /**
     * Initialize submission action buttons.
     */
    initSubmissionButtons: function() {
      $('.crida-submit-action').on('click', function(e) {
        var action = $(this).data('action');
        $('#field-submission-action').val(action);

        if (action === 'submit') {
          if (!confirm('Submit this case study for review? Once submitted, it will be reviewed by an administrator.')) {
            e.preventDefault();
            return;
          }
        }

        if (action === 'publish') {
          if (!confirm('Publish this case study? It will be immediately visible to the public.')) {
            e.preventDefault();
            return;
          }
        }
      });
    },

    /**
     * Initialize highlights repeatable field.
     */
    initHighlightsRepeater: function() {
      var $container = $('#crida-highlights-container');
      var $hidden = $('#field-highlights');
      var $addBtn = $('#crida-add-highlight');

      if (!$container.length) return;

      var highlights = [];
      try {
        highlights = JSON.parse($hidden.val() || '[]');
      } catch (e) {
        highlights = [];
      }

      var renderHighlights = function() {
        var html = '';
        highlights.forEach(function(h, i) {
          html += '<div class="crida-highlight-item input-group" style="margin-bottom:0.5rem;">' +
            '<input type="text" class="form-control crida-highlight-input" ' +
            'value="' + (h || '').replace(/"/g, '&quot;') + '" data-idx="' + i + '" ' +
            'placeholder="e.g., CRIDA Step 1: Decision context assessment">' +
            '<span class="input-group-btn">' +
            '<button type="button" class="btn btn-danger crida-remove-highlight" data-idx="' + i + '">' +
            '<i class="fa fa-times"></i></button></span></div>';
        });
        $container.html(html);
        $hidden.val(JSON.stringify(highlights));
      };

      $addBtn.on('click', function(e) {
        e.preventDefault();
        highlights.push('');
        renderHighlights();
        $container.find('.crida-highlight-input').last().focus();
      });

      $container.on('input', '.crida-highlight-input', function() {
        var idx = parseInt($(this).data('idx'));
        highlights[idx] = $(this).val();
        $hidden.val(JSON.stringify(highlights));
      });

      $container.on('click', '.crida-remove-highlight', function(e) {
        e.preventDefault();
        var idx = parseInt($(this).data('idx'));
        highlights.splice(idx, 1);
        renderHighlights();
      });

      renderHighlights();

      // Start with one empty highlight if none exist
      if (highlights.length === 0) {
        highlights.push('');
        renderHighlights();
      }
    },

    /**
     * Sync multi-select checkbox groups to their hidden JSON fields.
     */
    initCategoryCheckboxes: function() {
      var mappings = [
        { checks: 'sector_check', hidden: '#field-sector' },
        { checks: 'solution_check', hidden: '#field-solution-type' },
        { checks: 'challenge_check', hidden: '#field-climate-challenge' },
      ];

      mappings.forEach(function(m) {
        $('input[name="' + m.checks + '"]').on('change', function() {
          var selected = [];
          $('input[name="' + m.checks + '"]:checked').each(function() {
            selected.push($(this).val());
          });
          $(m.hidden).val(JSON.stringify(selected));
        });
      });
    },

    /**
     * Load existing data for edit mode.
     */
    loadExistingData: function() {
      // Themes checkboxes
      var themesVal = $('#field-themes').val();
      if (themesVal) {
        try {
          var themes = JSON.parse(themesVal);
          themes.forEach(function(t) {
            $('#crida-themes-container input[value="' + t + '"]').prop('checked', true);
          });
        } catch (e) { /* ignore */ }
      }
    },
  };

  $(document).ready(function() {
    if ($('#crida-case-study-form').length) {
      CRIDAEdit.init();
    }
  });

})(jQuery);
