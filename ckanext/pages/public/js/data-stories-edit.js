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
      
      // ========================================
      // COUNTRIES FIELD (aligned with rapid-response)
      // ========================================
      const countriesList = [
        'Afghanistan', 'Albania', 'Algeria', 'Andorra', 'Angola', 'Antigua and Barbuda',
        'Argentina', 'Armenia', 'Australia', 'Austria', 'Azerbaijan',
        'Bahamas', 'Bahrain', 'Bangladesh', 'Barbados', 'Belarus', 'Belgium',
        'Belize', 'Benin', 'Bhutan', 'Bolivia', 'Bosnia and Herzegovina', 'Botswana',
        'Brazil', 'Brunei', 'Bulgaria', 'Burkina Faso', 'Burundi', 'Cabo Verde',
        'Cambodia', 'Cameroon', 'Canada', 'Central African Republic', 'Chad', 'Chile',
        'China', 'Colombia', 'Comoros', 'Congo', 'Cook Islands', 'Costa Rica',
        "Cote d'Ivoire", 'Croatia', 'Cuba', 'Cyprus', 'Czech Republic',
        'Democratic Republic of the Congo', 'Denmark', 'Djibouti', 'Dominica',
        'Dominican Republic', 'Ecuador', 'Egypt', 'El Salvador', 'Equatorial Guinea',
        'Eritrea', 'Estonia', 'Eswatini', 'Ethiopia', 'Fiji', 'Finland',
        'France', 'Gabon', 'Gambia', 'Georgia', 'Germany', 'Ghana',
        'Greece', 'Grenada', 'Guatemala', 'Guinea', 'Guinea-Bissau', 'Guyana',
        'Haiti', 'Honduras', 'Hungary', 'Iceland', 'India', 'Indonesia',
        'Iran', 'Iraq', 'Ireland', 'Israel', 'Italy', 'Jamaica',
        'Japan', 'Jordan', 'Kazakhstan', 'Kenya', 'Kiribati', 'Kuwait',
        'Kyrgyzstan', 'Laos', 'Latvia', 'Lebanon', 'Lesotho', 'Liberia',
        'Libya', 'Lithuania', 'Luxembourg', 'Madagascar', 'Malawi', 'Malaysia',
        'Maldives', 'Mali', 'Malta', 'Marshall Islands', 'Mauritania', 'Mauritius',
        'Mexico', 'Micronesia', 'Moldova', 'Monaco', 'Mongolia', 'Montenegro',
        'Morocco', 'Mozambique', 'Myanmar', 'Namibia', 'Nauru', 'Nepal',
        'Netherlands', 'New Zealand', 'Nicaragua', 'Niger', 'Nigeria', 'Niue',
        'North Korea', 'North Macedonia', 'Norway', 'Oman', 'Pakistan', 'Palau',
        'Palestine', 'Panama', 'Papua New Guinea', 'Paraguay', 'Peru', 'Philippines',
        'Poland', 'Portugal', 'Qatar', 'Romania', 'Russia', 'Rwanda',
        'Saint Kitts and Nevis', 'Saint Lucia', 'Saint Vincent and the Grenadines',
        'Samoa', 'San Marino', 'Sao Tome and Principe', 'Saudi Arabia', 'Senegal', 'Serbia',
        'Seychelles', 'Sierra Leone', 'Singapore', 'Slovakia', 'Slovenia', 'Solomon Islands',
        'Somalia', 'South Africa', 'South Korea', 'South Sudan', 'Spain', 'Sri Lanka',
        'Sudan', 'Suriname', 'Sweden', 'Switzerland', 'Syria', 'Tajikistan',
        'Tanzania', 'Thailand', 'Timor-Leste', 'Togo', 'Tonga', 'Trinidad and Tobago',
        'Tunisia', 'Turkey', 'Turkmenistan', 'Tuvalu', 'Uganda', 'Ukraine',
        'United Arab Emirates', 'United Kingdom', 'United States', 'Uruguay', 'Uzbekistan',
        'Vanuatu', 'Vatican City', 'Venezuela', 'Vietnam', 'Yemen', 'Zambia', 'Zimbabwe'
      ];

      let selectedCountries = [];

      function getCountryElementId(name) {
        return 'story-country-' + name.toLowerCase().replace(/[^a-z0-9]+/g, '-');
      }

      function updateCountriesHiddenField() {
        // Always send a valid JSON array, even if empty
        const value = JSON.stringify(selectedCountries);
        $('#story-countries-data').val(value);
        console.log('[DataStories] Countries field updated:', value);
      }

      function addCountryToList(country) {
        const countryId = getCountryElementId(country.name);
        if ($('#' + countryId).length) {
          return;
        }

        const countryHtml = `
          <div class="country-item" id="${countryId}" data-country-name="${country.name}">
            <span class="country-name">${country.display_name || country.name}</span>
            <button type="button" class="btn btn-sm btn-danger remove-story-country" data-country-name="${country.name}">
              <i class="fa fa-times"></i>
            </button>
          </div>
        `;
        $('#story-selected-countries').append(countryHtml);
      }

      function loadExistingCountries() {
        const $hidden = $('#story-countries-data');
        const rawValue = $hidden.val();
        console.log('[DataStories] loadExistingCountries: hidden field exists:', $hidden.length > 0);
        console.log('[DataStories] loadExistingCountries: rawValue:', rawValue);

        if (!rawValue) {
          console.log('[DataStories] loadExistingCountries: rawValue is empty/falsy');
          selectedCountries = [];
          return;
        }

        try {
          const parsed = JSON.parse(rawValue);
          console.log('[DataStories] loadExistingCountries: parsed value:', parsed);
          if (Array.isArray(parsed)) {
            selectedCountries = parsed.map(function(entry) {
              if (typeof entry === 'string') {
                return { name: entry, display_name: entry };
              }
              return {
                name: entry.name || '',
                display_name: entry.display_name || entry.name || ''
              };
            }).filter(function(entry) {
              return entry.name;
            });
            console.log('[DataStories] loadExistingCountries: selectedCountries after parse:', selectedCountries);
          }
        } catch (e) {
          console.log('[DataStories] loadExistingCountries: JSON parse error:', e.message);
          // Fallback: comma-separated string
          const countryNames = rawValue.split(',').map(function(c) { return c.trim(); }).filter(Boolean);
          selectedCountries = countryNames.map(function(name) {
            return { name: name, display_name: name };
          });
        }

        selectedCountries.forEach(function(country) {
          addCountryToList(country);
        });
      }

      function initCountriesSelector() {
        const $select = $('#story-country-select');
        const $addButton = $('#story-add-country');
        const $list = $('#story-selected-countries');

        // Debug: Log the initial state of the hidden field
        var $initialHidden = $('#story-countries-data');
        console.log('[DataStories] initCountriesSelector - hidden field exists:', $initialHidden.length > 0);
        console.log('[DataStories] initCountriesSelector - initial hidden value:', $initialHidden.val());

        if (!$select.length || !$list.length) {
          return;
        }

        // Remove whitespace so :empty CSS works for empty state
        $list.empty();

        // Populate dropdown
        $select.empty();
        $select.append('<option value="">Select a country...</option>');
        countriesList.slice().sort().forEach(function(country) {
          $select.append('<option value="' + country + '">' + country + '</option>');
        });

        // Load any existing selections
        loadExistingCountries();
        updateCountriesHiddenField();

        // Add country handler
        $addButton.on('click', function() {
          const countryName = $select.val();
          if (!countryName) {
            return;
          }

          if (selectedCountries.find(function(c) { return c.name === countryName; })) {
            alert('This country has already been added');
            return;
          }

          const country = { name: countryName, display_name: countryName };
          selectedCountries.push(country);
          addCountryToList(country);
          updateCountriesHiddenField();
          $select.val('');
        });

        // Remove country handler
        $(document).on('click', '.remove-story-country', function() {
          const countryName = $(this).data('country-name');
          const countryId = '#' + getCountryElementId(countryName);
          $(countryId).remove();
          selectedCountries = selectedCountries.filter(function(c) { return c.name !== countryName; });
          updateCountriesHiddenField();
        });
      }

      // Initialize countries selector
      initCountriesSelector();

      // ========================================
      // PARTNERS FIELD
      // ========================================
      let selectedPartners = [];

      function getPartnerElementId(name) {
        return 'story-partner-' + name.toLowerCase().replace(/[^a-z0-9]+/g, '-');
      }

      function updatePartnersHiddenField() {
        const value = JSON.stringify(selectedPartners);
        $('#story-partners-data').val(value);
        console.log('[DataStories] Partners field updated:', value);
      }

      function addPartnerToList(partner) {
        const partnerId = getPartnerElementId(partner.name);
        if ($('#' + partnerId).length) {
          return;
        }

        const partnerHtml = `
          <div class="partner-item" id="${partnerId}" data-partner-name="${partner.name}" style="display: inline-flex; align-items: center; background: #e3f2fd; border: 1px solid #0072BC; border-radius: 20px; padding: 0.25rem 0.75rem; margin: 0.25rem; font-size: 0.9rem;">
            <i class="fa fa-building" style="margin-right: 0.5rem; color: #0072BC;"></i>
            <span class="partner-name">${partner.name}</span>
            <button type="button" class="btn btn-xs btn-link remove-story-partner" data-partner-name="${partner.name}" style="margin-left: 0.5rem; padding: 0; color: #dc3545;">
              <i class="fa fa-times"></i>
            </button>
          </div>
        `;
        $('#story-selected-partners').append(partnerHtml);
      }

      function loadExistingPartners() {
        const $hidden = $('#story-partners-data');
        const rawValue = $hidden.val();
        console.log('[DataStories] loadExistingPartners: rawValue:', rawValue);

        if (!rawValue) {
          selectedPartners = [];
          return;
        }

        try {
          const parsed = JSON.parse(rawValue);
          if (Array.isArray(parsed)) {
            selectedPartners = parsed.map(function(entry) {
              if (typeof entry === 'string') {
                return { name: entry };
              }
              return { name: entry.name || '' };
            }).filter(function(entry) {
              return entry.name;
            });
          }
        } catch (e) {
          console.log('[DataStories] loadExistingPartners: JSON parse error:', e.message);
          const partnerNames = rawValue.split(',').map(function(p) { return p.trim(); }).filter(Boolean);
          selectedPartners = partnerNames.map(function(name) {
            return { name: name };
          });
        }

        selectedPartners.forEach(function(partner) {
          addPartnerToList(partner);
        });
      }

      function initPartnersSelector() {
        const $input = $('#story-partner-input');
        const $addButton = $('#story-add-partner');
        const $list = $('#story-selected-partners');

        if (!$input.length || !$list.length) {
          return;
        }

        $list.empty();
        loadExistingPartners();
        updatePartnersHiddenField();

        // Add partner on button click
        $addButton.on('click', function() {
          const partnerName = $input.val().trim();
          if (!partnerName) {
            return;
          }

          if (selectedPartners.find(function(p) { return p.name.toLowerCase() === partnerName.toLowerCase(); })) {
            alert('This partner has already been added');
            return;
          }

          const partner = { name: partnerName };
          selectedPartners.push(partner);
          addPartnerToList(partner);
          updatePartnersHiddenField();
          $input.val('');
        });

        // Add partner on Enter key
        $input.on('keypress', function(e) {
          if (e.which === 13) {
            e.preventDefault();
            $addButton.click();
          }
        });

        // Remove partner handler
        $(document).on('click', '.remove-story-partner', function() {
          const partnerName = $(this).data('partner-name');
          const partnerId = '#' + getPartnerElementId(partnerName);
          $(partnerId).remove();
          selectedPartners = selectedPartners.filter(function(p) { return p.name !== partnerName; });
          updatePartnersHiddenField();
        });
      }

      // Initialize partners selector
      initPartnersSelector();

      // ========================================
      // DATASETS FIELD
      // ========================================
      let selectedDatasets = [];

      function extractDatasetId(raw) {
        if (!raw) return '';
        const trimmed = raw.trim();
        const match = trimmed.match(/dataset\/([^/?#]+)/);
        if (match && match[1]) {
          return match[1];
        }
        return trimmed;
      }

      function buildExtrasMap(extras) {
        const map = {};
        if (Array.isArray(extras)) {
          extras.forEach(function(entry) {
            if (entry && entry.key) {
              map[entry.key] = entry.value;
            }
          });
        }
        return map;
      }

      function buildDatasetMeta(pkg) {
        const extrasMap = buildExtrasMap(pkg.extras || []);
        const doi = pkg.doi || pkg.dataset_doi || extrasMap.doi || extrasMap.dataset_doi || '';
        const doiStatus = pkg.doi_status || extrasMap.doi_status || extrasMap.doi_state || '';
        const citation = pkg.citation || extrasMap.citation || '';
        const authors = extrasMap.authors || pkg.author || pkg.maintainer || '';

        return {
          id: pkg.id,
          name: pkg.name,
          title: pkg.title || pkg.name,
          doi: doi,
          doi_status: doiStatus || (doi ? 'pending' : ''),
          citation: citation,
          authors: authors,
          url: window.location.origin + '/dataset/' + pkg.name
        };
      }

      function updateDatasetsHiddenField() {
        const value = selectedDatasets.length ? JSON.stringify(selectedDatasets) : '';
        $('#story-datasets-data').val(value);
      }

      function renderDatasetsTable() {
        const $tbody = $('#story-datasets-table tbody');
        $tbody.empty();

        if (!selectedDatasets.length) {
          $tbody.append('<tr class="empty-state"><td colspan="4" class="text-muted">No datasets added yet.</td></tr>');
          updateDatasetsHiddenField();
          return;
        }

        selectedDatasets.forEach(function(ds, index) {
          const doiText = ds.doi ? (ds.doi + (ds.doi_status ? ' (' + ds.doi_status + ')' : '')) : 'Pending';
          const authorsText = ds.citation || ds.authors || '';
          const row = `
            <tr data-dataset-id="${ds.id}">
              <td><a href="${ds.url}" target="_blank" rel="noopener">${ds.title}</a></td>
              <td>${doiText}</td>
              <td>${authorsText || '<span class="text-muted">—</span>'}</td>
              <td class="text-center">
                <button type="button" class="btn btn-danger btn-sm remove-dataset-row" data-index="${index}">
                  <i class="fa fa-trash"></i>
                </button>
              </td>
            </tr>
          `;
          $tbody.append(row);
        });

        updateDatasetsHiddenField();
      }

      function loadExistingDatasets() {
        const raw = $('#story-datasets-data').val();
        if (!raw) {
          selectedDatasets = [];
          renderDatasetsTable();
          return;
        }
        try {
          const parsed = JSON.parse(raw);
          if (Array.isArray(parsed)) {
            selectedDatasets = parsed;
          } else {
            selectedDatasets = [];
          }
        } catch (e) {
          selectedDatasets = [];
        }
        renderDatasetsTable();
      }

      function fetchDataset(datasetId) {
        return $.ajax({
          url: '/api/3/action/package_show',
          method: 'GET',
          dataType: 'json',
          data: { id: datasetId }
        });
      }

      function addDatasetFromInput() {
        const rawInput = $('#story-dataset-input').val();
        const datasetId = extractDatasetId(rawInput);
        if (!datasetId) {
          alert('Please enter a dataset URL or name');
          return;
        }

        // Prevent duplicates
        if (selectedDatasets.find(function(ds) { return ds.name === datasetId || ds.id === datasetId; })) {
          alert('This dataset is already added');
          return;
        }

        fetchDataset(datasetId)
          .done(function(resp) {
            if (resp && resp.success && resp.result) {
              const meta = buildDatasetMeta(resp.result);
              selectedDatasets.push(meta);
              renderDatasetsTable();
              $('#story-dataset-input').val('');
            } else {
              alert('Dataset not found');
            }
          })
          .fail(function() {
            alert('Could not fetch dataset. Please check the URL or name.');
          });
      }

      $('#story-add-dataset').on('click', function() {
        addDatasetFromInput();
      });

      $('#story-dataset-input').on('keypress', function(e) {
        if (e.which === 13) {
          e.preventDefault();
          addDatasetFromInput();
        }
      });

      $(document).on('click', '.remove-dataset-row', function() {
        const idx = $(this).data('index');
        selectedDatasets.splice(idx, 1);
        renderDatasetsTable();
      });

      loadExistingDatasets();

      // Wait for Quill to be available
      function waitForQuill(callback) {
        if (typeof Quill !== 'undefined') {
          callback();
        } else {
          setTimeout(function(){ waitForQuill(callback); }, 50);
        }
      }
      
      // Register ImageResize module if available
      waitForQuill(function() {
        if (typeof ImageResize !== 'undefined') {
          Quill.register('modules/imageResize', ImageResize.default || ImageResize);
        }
      });
      
      // Section management
      let sectionIndex = $('.content-section-editor').length;
      let sectionBlockCounters = {};
      let sectionQuillEditors = {};
      
      // Initialize existing sections
      console.log('=== Initializing Data Stories Editor ===');
      console.log('Found ' + $('.content-section-editor').length + ' existing sections');

      $('.content-section-editor').each(function(index) {
        const sectionId = index;
        const $section = $(this);
        
        // Ensure data-section-id is set to the numeric index for JS consistency
        $section.attr('data-section-id', sectionId);
        
        const metadataField = $section.find('.section-blocks-metadata');
        console.log('[Init Section ' + sectionId + '] Metadata field found:', metadataField.length > 0);
        console.log('[Init Section ' + sectionId + '] Raw metadata value:', metadataField.val());
        console.log('[Init Section ' + sectionId + '] Debug type:', metadataField.data('debug-type'));
        console.log('[Init Section ' + sectionId + '] Debug truthy:', metadataField.data('debug-truthy'));
        initializeSectionBlocks($section, sectionId);
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
        console.log('[DataStories] Updating section order after drag/drop');
        
        // First pass: collect all mappings (oldSectionId -> newIndex) and save content
        const mappings = [];
        const savedEditors = {};
        const savedCounters = {};
        
        $('.content-section-editor').each(function(newIndex) {
          const $section = $(this);
          const oldSectionId = $section.attr('data-section-id');
          
          mappings.push({
            element: $section,
            oldId: oldSectionId,
            newIndex: newIndex
          });
          
          // Save editors and counters with old ID
          if (oldSectionId !== undefined && sectionQuillEditors[oldSectionId]) {
            savedEditors[oldSectionId] = sectionQuillEditors[oldSectionId];
          }
          if (oldSectionId !== undefined && sectionBlockCounters[oldSectionId] !== undefined) {
            savedCounters[oldSectionId] = sectionBlockCounters[oldSectionId];
          }
        });
        
        // Clear current editor/counter references
        Object.keys(sectionQuillEditors).forEach(function(key) {
          delete sectionQuillEditors[key];
        });
        Object.keys(sectionBlockCounters).forEach(function(key) {
          delete sectionBlockCounters[key];
        });
        
        // Second pass: update IDs, field names, and restore editors to new positions
        mappings.forEach(function(mapping) {
          const $section = mapping.element;
          const oldSectionId = mapping.oldId;
          const newIndex = mapping.newIndex;
          
          // Update order_index field
          $section.find('[name*="[order_index]"]').val(newIndex);
          $section.find('.section-order').val(newIndex);
          
          // Update section ID
          $section.attr('data-section-id', newIndex);
          $section.attr('id', 'section-' + newIndex);
          
          // Update all name attributes to match new index
          $section.find('[name^="sections["]').each(function() {
            const name = $(this).attr('name');
            const newName = name.replace(/sections\[\d+\]/, 'sections[' + newIndex + ']');
            $(this).attr('name', newName);
          });
          
          // Update blocks container ID
          $section.find('.section-content-blocks').attr('id', 'section-' + newIndex + '-blocks');
          
          // Update section number display if exists
          $section.find('.section-number').text(newIndex + 1);
          
          // Restore editors and counters with new index
          if (oldSectionId !== undefined && savedEditors[oldSectionId]) {
            sectionQuillEditors[newIndex] = savedEditors[oldSectionId];
          } else if (!sectionQuillEditors[newIndex]) {
            sectionQuillEditors[newIndex] = {};
          }
          if (oldSectionId !== undefined && savedCounters[oldSectionId] !== undefined) {
            sectionBlockCounters[newIndex] = savedCounters[oldSectionId];
          } else if (sectionBlockCounters[newIndex] === undefined) {
            sectionBlockCounters[newIndex] = 0;
          }
          
          // Update section content to reflect new structure
          updateSectionContent(newIndex);
        });
        
        console.log('[DataStories] Section order update complete');
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
        
        // Set order_index to current section count (append at end)
        $newSection.find('[name*="[order_index]"]').val(sectionIndex);
        
        // Set data-section-id before appending and initializing
        $newSection.attr('data-section-id', sectionIndex);
        $newSection.attr('id', 'section-' + sectionIndex);
        
        $('#sections-container').append($newSection);
        initializeSectionBlocks($newSection, sectionIndex);
        sectionIndex++;
        updateSectionOrder();
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

        // Update section content after loading existing blocks (with small delay for Quill init)
        setTimeout(function() {
          updateSectionContent(sectionId);
        }, 100);

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
        let blocksMetadata = metadataField.val();

        console.log('[Section ' + sectionId + '] Loading blocks, raw metadata:', blocksMetadata);
        console.log('[Section ' + sectionId + '] Metadata type:', typeof blocksMetadata);
        console.log('[Section ' + sectionId + '] Metadata length:', blocksMetadata ? blocksMetadata.length : 0);

        if (blocksMetadata && blocksMetadata.trim() && blocksMetadata !== 'null' && blocksMetadata !== '[]' && blocksMetadata !== 'None') {
          try {
            // Handle potential HTML-encoding (from input value attribute)
            let cleanedMetadata = blocksMetadata
              .replace(/&quot;/g, '"')
              .replace(/&amp;/g, '&')
              .replace(/&lt;/g, '<')
              .replace(/&gt;/g, '>')
              .replace(/&#39;/g, "'")
              .replace(/&#x27;/g, "'")
              .replace(/&#x2F;/g, '/')
              .trim();

            console.log('[Section ' + sectionId + '] Cleaned metadata:', cleanedMetadata.substring(0, 200));

            // Handle potential double-encoding or escaped JSON
            let blocks = cleanedMetadata;

            // If it's a string, try to parse it
            if (typeof blocks === 'string') {
              blocks = JSON.parse(blocks);
            }

            // If still a string after first parse (double-encoded), parse again
            if (typeof blocks === 'string') {
              blocks = JSON.parse(blocks);
            }

            console.log('[Section ' + sectionId + '] Parsed blocks:', blocks);
            console.log('[Section ' + sectionId + '] Blocks is array:', Array.isArray(blocks));
            console.log('[Section ' + sectionId + '] Blocks length:', blocks ? blocks.length : 0);

            if (Array.isArray(blocks) && blocks.length > 0) {
              blocks.forEach((blockData, blockIndex) => {
                console.log('[Section ' + sectionId + '] Loading block ' + blockIndex + ':', blockData.type, blockData);

                if (blockData.type === 'text') {
                  console.log('[Section ' + sectionId + '] -> Adding TEXT block');
                  addTextBlock(sectionId, blockData.content);
                } else if (blockData.type === 'terria') {
                  console.log('[Section ' + sectionId + '] -> Adding TERRIA block with tabs:', blockData.tabs);
                  addTerriaBlock(sectionId, blockData);
                } else if (blockData.type === 'media') {
                  console.log('[Section ' + sectionId + '] -> Adding MEDIA block');
                  addMediaBlock(sectionId, blockData);
                } else {
                  console.warn('[Section ' + sectionId + '] Unknown block type:', blockData.type);
                  // Try to add as text block with content if available
                  if (blockData.content) {
                    addTextBlock(sectionId, blockData.content);
                  }
                }
              });
              return; // Exit after loading blocks from metadata
            }
          } catch (e) {
            console.error('[Section ' + sectionId + '] Error parsing blocks metadata:', e);
            console.error('[Section ' + sectionId + '] Raw value was:', blocksMetadata);
          }
        }

        // Fallback: No valid metadata, check for existing content and terria link
        console.log('[Section ' + sectionId + '] No valid metadata, using fallback');
        const existingContent = $section.find('.section-content-field').val();
        const terriaLink = $section.find('.section-terria-link').val();

        console.log('[Section ' + sectionId + '] Fallback content length:', existingContent ? existingContent.length : 0);
        console.log('[Section ' + sectionId + '] Fallback terria link:', terriaLink);

        if (existingContent && existingContent.trim()) {
          console.log('[Section ' + sectionId + '] Fallback: Adding text block from content');
          addTextBlock(sectionId, existingContent);
        }

        if (terriaLink && terriaLink.trim()) {
          console.log('[Section ' + sectionId + '] Fallback: Adding Terria block from link:', terriaLink);
          addTerriaBlock(sectionId, { url: terriaLink });
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
          // Build modules config with ImageResize if available
          var modulesConfig = {
            toolbar: [
              [{ 'header': [2, 3, false] }],
              ['bold', 'italic', 'underline'],
              [{ 'list': 'ordered'}, { 'list': 'bullet' }],
              ['link', 'image'],
              ['clean']
            ]
          };
          if (typeof ImageResize !== 'undefined') {
            modulesConfig.imageResize = { displaySize: true };
          }
          
          const quill = new Quill('#' + blockId + '-editor', {
            theme: 'snow',
            modules: modulesConfig,
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
      
      // Add Terria map block with tabs support
      function addTerriaBlock(sectionId, data = {}) {
        const blockId = 'section-' + sectionId + '-block-' + (++sectionBlockCounters[sectionId]);
        const $container = $('#section-' + sectionId + '-blocks');

        // Initialize tabs if not present
        if (!data.tabs || !Array.isArray(data.tabs) || data.tabs.length === 0) {
          data.tabs = [{
            title: data.title || 'Map 1',
            url: data.url || ''
          }];
        }

        const html = `
          <div class="content-block terria-tabs-block" data-block-id="${blockId}" data-block-type="terria">
            <div class="content-block-header">
              <h5 class="content-block-title">
                <i class="fa fa-map"></i>
                Terria Maps with Tabs
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

                <!-- Tabs Navigation -->
                <div class="terria-tabs-nav" style="margin-bottom: 1rem;">
                  <div class="terria-tabs-list" style="display: flex; gap: 0.5rem; flex-wrap: wrap; align-items: center;">
                    ${data.tabs.map((tab, index) => `
                      <button type="button"
                              class="terria-tab-btn ${index === 0 ? 'active' : ''}"
                              data-tab-index="${index}"
                              style="padding: 0.5rem 1rem; border-radius: 8px; border: 2px solid #e9ecef; background: ${index === 0 ? 'linear-gradient(135deg, #0072BC 0%, #005A9C 100%)' : '#f8f9fa'}; color: ${index === 0 ? 'white' : '#6c757d'}; font-weight: 600; cursor: pointer; transition: all 0.3s ease;">
                        <i class="fa fa-map-marker"></i> ${tab.title || 'Map ' + (index + 1)}
                      </button>
                    `).join('')}
                    <button type="button"
                            class="add-terria-tab-btn"
                            style="padding: 0.5rem 1rem; border-radius: 8px; border: 2px dashed #0072BC; background: transparent; color: #0072BC; font-weight: 600; cursor: pointer; transition: all 0.3s ease;">
                      <i class="fa fa-plus"></i> Add Tab
                    </button>
                  </div>
                </div>

                <!-- Tabs Content -->
                <div class="terria-tabs-content">
                  ${data.tabs.map((tab, index) => `
                    <div class="terria-tab-panel ${index === 0 ? 'active' : ''}" data-tab-index="${index}" style="display: ${index === 0 ? 'block' : 'none'};">
                      <div class="form-group">
                        <label>Tab Title</label>
                        <input type="text"
                               class="form-control terria-tab-title"
                               value="${tab.title || ''}"
                               placeholder="Map ${index + 1}">
                      </div>
                      <div class="form-group">
                        <label>Terria Share Link</label>
                        <input type="text"
                               class="form-control terria-tab-url"
                               value="${tab.url || ''}"
                               placeholder="https://ihp-wins.unesco.org/terria/#share=abc123">
                        <small class="help-block">Paste a Terria share link or JSON config</small>
                      </div>
                      <div class="form-group" style="display: flex; gap: 0.5rem; flex-wrap: wrap;">
                        <button type="button" class="btn btn-sm btn-info preview-terria-tab">
                          <i class="fa fa-eye"></i> Preview Map
                        </button>
                        ${data.tabs.length > 1 ? `
                          <button type="button" class="btn btn-sm btn-danger delete-terria-tab">
                            <i class="fa fa-trash"></i> Delete Tab
                          </button>
                        ` : ''}
                      </div>
                      <div class="terria-tab-preview" style="display: none; margin-top: 1rem; border-radius: 12px; overflow: hidden; border: 2px solid #e9ecef;"></div>
                    </div>
                  `).join('')}
                </div>

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
            // Use blockId without '-editor' suffix since that's how we store it
            if (sectionQuillEditors[sectionId] && sectionQuillEditors[sectionId][blockId]) {
              delete sectionQuillEditors[sectionId][blockId];
            }
            $block.remove();
            updateSectionContent(sectionId);
          }
        });
      }
      
      // Add Terria block event listeners with tabs support
      function addTerriaBlockEventListeners(blockId, sectionId) {
        const $block = $('[data-block-id="' + blockId + '"]');

        // Switch between tabs - Using event delegation for dynamically added tabs
        $block.off('click.terriatab').on('click.terriatab', '.terria-tab-btn', function(e) {
          e.preventDefault();
          e.stopPropagation();

          const tabIndex = $(this).data('tab-index');

          // Update button styles
          $block.find('.terria-tab-btn').each(function() {
            const isActive = $(this).data('tab-index') === tabIndex;
            $(this).removeClass('active')
              .css('background', isActive ? 'linear-gradient(135deg, #0072BC 0%, #005A9C 100%)' : '#f8f9fa')
              .css('color', isActive ? 'white' : '#6c757d')
              .css('border-color', isActive ? '#0072BC' : '#e9ecef');
            if (isActive) {
              $(this).addClass('active');
            }
          });

          // Show/hide tab panels
          $block.find('.terria-tab-panel').each(function() {
            const panelIndex = $(this).data('tab-index');
            if (panelIndex === tabIndex) {
              $(this).show().addClass('active');
            } else {
              $(this).hide().removeClass('active');
            }
          });
        });

        // Add new tab - Using event delegation
        $block.off('click.addtab').on('click.addtab', '.add-terria-tab-btn', function(e) {
          e.preventDefault();
          e.stopPropagation();

          const $tabsList = $block.find('.terria-tabs-list');
          const $tabsContent = $block.find('.terria-tabs-content');
          const currentTabCount = $block.find('.terria-tab-panel').length;
          const newTabIndex = currentTabCount;

          // Create new tab button
          const $newTabBtn = $(`
            <button type="button"
                    class="terria-tab-btn"
                    data-tab-index="${newTabIndex}"
                    style="padding: 0.5rem 1rem; border-radius: 8px; border: 2px solid #e9ecef; background: #f8f9fa; color: #6c757d; font-weight: 600; cursor: pointer; transition: all 0.3s ease;">
              <i class="fa fa-map-marker"></i> Map ${newTabIndex + 1}
            </button>
          `);

          // Insert before "Add Tab" button
          $newTabBtn.insertBefore($(this));

          // Create new tab panel
          const $newPanel = $(`
            <div class="terria-tab-panel" data-tab-index="${newTabIndex}" style="display: none;">
              <div class="form-group">
                <label>Tab Title</label>
                <input type="text"
                       class="form-control terria-tab-title"
                       value="Map ${newTabIndex + 1}"
                       placeholder="Map ${newTabIndex + 1}">
              </div>
              <div class="form-group">
                <label>Terria Share Link</label>
                <input type="text"
                       class="form-control terria-tab-url"
                       value=""
                       placeholder="https://ihp-wins.unesco.org/terria/#share=abc123">
                <small class="help-block">Paste a Terria share link or JSON config</small>
              </div>
              <div class="form-group" style="display: flex; gap: 0.5rem; flex-wrap: wrap;">
                <button type="button" class="btn btn-sm btn-info preview-terria-tab">
                  <i class="fa fa-eye"></i> Preview Map
                </button>
                <button type="button" class="btn btn-sm btn-danger delete-terria-tab">
                  <i class="fa fa-trash"></i> Delete Tab
                </button>
              </div>
              <div class="terria-tab-preview" style="display: none; margin-top: 1rem; border-radius: 12px; overflow: hidden; border: 2px solid #e9ecef;"></div>
            </div>
          `);

          $tabsContent.append($newPanel);

          // Bind events to new tab
          bindTerriaTabEvents($block, newTabIndex, sectionId);

          // Switch to new tab
          $newTabBtn.trigger('click');

          updateSectionContent(sectionId);
        });

        // Bind events for existing tabs
        $block.find('.terria-tab-panel').each(function() {
          const tabIndex = $(this).data('tab-index');
          bindTerriaTabEvents($block, tabIndex, sectionId);
        });
      }

      // Bind events for individual Terria tab
      function bindTerriaTabEvents($block, tabIndex, sectionId) {
        const $panel = $block.find(`.terria-tab-panel[data-tab-index="${tabIndex}"]`);
        const $tabBtn = $block.find(`.terria-tab-btn[data-tab-index="${tabIndex}"]`);

        // Update tab button text when title changes
        $panel.find('.terria-tab-title').off('input').on('input', function() {
          const newTitle = $(this).val() || 'Map ' + (tabIndex + 1);
          $tabBtn.html(`<i class="fa fa-map-marker"></i> ${newTitle}`);
          updateSectionContent(sectionId);
        });

        // Update content when URL changes
        $panel.find('.terria-tab-url').off('input').on('input', function() {
          updateSectionContent(sectionId);
        });

        // Preview tab
        $panel.find('.preview-terria-tab').off('click').on('click', function() {
          const $preview = $panel.find('.terria-tab-preview');
          const url = $panel.find('.terria-tab-url').val();

          if ($preview.is(':visible')) {
            $preview.hide();
          } else if (url) {
            const iframe = `<iframe src="${url}" width="100%" height="500" frameborder="0" allowfullscreen mozallowfullscreen webkitallowfullscreen style="border-radius: 12px;"></iframe>`;
            $preview.html(iframe).show();
          } else {
            alert('Please enter a Terria share link first');
          }
        });

        // Delete tab
        $panel.find('.delete-terria-tab').off('click').on('click', function() {
          const tabCount = $block.find('.terria-tab-panel').length;

          if (tabCount <= 1) {
            alert('You must have at least one tab');
            return;
          }

          if (confirm('Are you sure you want to delete this tab?')) {
            // Remove tab button and panel
            $tabBtn.remove();
            $panel.remove();

            // If we deleted the active tab, activate the first remaining tab
            if ($panel.hasClass('active')) {
              $block.find('.terria-tab-btn').first().trigger('click');
            }

            // Renumber remaining tabs
            $block.find('.terria-tab-panel').each(function(index) {
              $(this).attr('data-tab-index', index);
              const $btn = $block.find('.terria-tab-btn').eq(index);
              $btn.attr('data-tab-index', index);

              // Update placeholder if title is empty
              const title = $(this).find('.terria-tab-title').val();
              if (!title) {
                $(this).find('.terria-tab-title').attr('placeholder', 'Map ' + (index + 1));
              }
            });

            updateSectionContent(sectionId);
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
        // Find section by data-section-id attribute, fallback to index if not found
        let $section = $('.content-section-editor[data-section-id="' + sectionId + '"]');
        if (!$section.length) {
          // Fallback: try by index position
          $section = $('.content-section-editor').eq(sectionId);
        }
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
            const editorId = blockId;
            const quill = sectionQuillEditors[sectionId] && sectionQuillEditors[sectionId][editorId];
            console.log('Processing text block:', blockId, 'Editor ID:', editorId, 'Quill exists:', !!quill);
            if (quill) {
              const html = quill.root.innerHTML;
              const text = quill.getText().trim();
              console.log('Text content length:', text.length);
              if (text) {
                contentHtml += html + '\n\n';
                blocksMetadata.push({
                  type: 'text',
                  content: html
                });
              }
            } else {
              console.warn('Quill editor not found for block:', blockId);
            }
          } else if (blockType === 'terria') {
            // Collect all tabs
            const tabs = [];
            $block.find('.terria-tab-panel').each(function() {
              const $panel = $(this);
              const tabTitle = $panel.find('.terria-tab-title').val();
              const tabUrl = $panel.find('.terria-tab-url').val();

              if (tabUrl) {
                tabs.push({
                  title: tabTitle || 'Map ' + (tabs.length + 1),
                  url: tabUrl
                });
              }
            });

            // Generate HTML for tabs
            if (tabs.length > 0) {
              // Add tabs navigation HTML
              contentHtml += '<div class="terria-tabs-display">\n';
              contentHtml += '<ul class="terria-tabs-nav-display">\n';
              tabs.forEach((tab, index) => {
                contentHtml += `  <li class="${index === 0 ? 'active' : ''}" data-tab="${index}">${tab.title}</li>\n`;
              });
              contentHtml += '</ul>\n';

              // Add tabs content HTML
              contentHtml += '<div class="terria-tabs-panels-display">\n';
              tabs.forEach((tab, index) => {
                contentHtml += `  <div class="terria-tab-display ${index === 0 ? 'active' : ''}" data-tab="${index}">\n`;
                contentHtml += `    <iframe src="${tab.url}" width="100%" height="600" frameborder="0" allowfullscreen mozallowfullscreen webkitallowfullscreen></iframe>\n`;
                contentHtml += '  </div>\n';
              });
              contentHtml += '</div>\n';
              contentHtml += '</div>\n\n';

              // Save to metadata
              blocksMetadata.push({
                type: 'terria',
                tabs: tabs
              });

              // Set first tab URL for backward compatibility
              if (!hasTerriaMap && tabs.length > 0) {
                hasTerriaMap = true;
                terriaLink = tabs[0].url;
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

        console.log('Section ' + sectionId + ' content updated:');
        console.log('- Content HTML length:', contentHtml.length);
        console.log('- Blocks metadata:', blocksMetadata);
        console.log('- Content field value:', $section.find('.section-content-field').val().substring(0, 100));

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
      
      // Form submission - Only for the main data stories form, not delete forms
      $('.data-stories-form, form.data-stories-form').on('submit', function(e) {
        console.log('Data story form submitting, updating section content...');
        updateCountriesHiddenField();
        updatePartnersHiddenField();
        // Debug: Log the countries hidden field value at submit time
        var countriesVal = $('#story-countries-data').val();
        console.log('[DataStories] Form submit - countries hidden field value:', countriesVal);
        console.log('[DataStories] Form submit - countries hidden field type:', typeof countriesVal);
        console.log('[DataStories] Form submit - selectedCountries array:', selectedCountries);
        // Debug: Log the partners hidden field value at submit time
        var partnersVal = $('#story-partners-data').val();
        console.log('[DataStories] Form submit - partners hidden field value:', partnersVal);
        console.log('[DataStories] Form submit - selectedPartners array:', selectedPartners);
        // Update all section content before submit
        $('.content-section-editor').each(function() {
          var sectionId = $(this).attr('data-section-id');
          if (sectionId !== undefined) {
            updateSectionContent(sectionId);
            console.log('Updated section ' + sectionId);
          }
        });
      });
      
      // ========================================
      // IMAGE UPLOAD FUNCTIONALITY
      // ========================================
      
      let uploadedImages = [];
      
      // Load existing uploaded images
      function loadUploadedImages() {
        const uploadedData = $('#uploaded-images-data').val();
        console.log('[Image Gallery] Raw uploaded_images value:', uploadedData);
        console.log('[Image Gallery] Value type:', typeof uploadedData);
        console.log('[Image Gallery] Value length:', uploadedData ? uploadedData.length : 0);
        
        if (uploadedData) {
          try {
            uploadedImages = JSON.parse(uploadedData);
            console.log('[Image Gallery] Parsed successfully:', uploadedImages);
            uploadedImages.forEach(img => {
              addUploadedImagePreview(img);
            });
          } catch (e) {
            console.error('[Image Gallery] Error parsing uploaded images data:', e);
            console.error('[Image Gallery] Failed data:', uploadedData.substring(0, 100));
          }
        } else {
          console.log('[Image Gallery] No uploaded images data found');
        }
      }
      
      // Upload queue for sequential uploads (avoid server timeout with parallel uploads)
      let uploadQueue = [];
      let isUploading = false;
      
      function processUploadQueue() {
        if (isUploading || uploadQueue.length === 0) {
          return;
        }
        
        isUploading = true;
        const file = uploadQueue.shift();
        uploadImageInternal(file, function() {
          isUploading = false;
          processUploadQueue();
        });
      }
      
      function queueImageUpload(file) {
        uploadQueue.push(file);
        processUploadQueue();
      }
      
      // Handle file upload
      $('#image-upload').on('change', function(e) {
        e.stopPropagation();
        const files = this.files;
        if (files.length > 0) {
          Array.from(files).forEach(file => {
            if (file.type.startsWith('image/')) {
              queueImageUpload(file);
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
              queueImageUpload(file);
            }
          });
        }
      });
      
      // Upload image function (internal - called by queue processor)
      function uploadImageInternal(file, onComplete) {
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
              
              // Update the first section's image_url field with the uploaded image
              const $firstSection = $('.content-section-editor').first();
              if ($firstSection.length) {
                const $imageUrlField = $firstSection.find('.section-image-url');
                if ($imageUrlField.length && !$imageUrlField.val()) {
                  $imageUrlField.val(response.url);
                  console.log('[DataStories] Updated first section image_url:', response.url);
                }
              }
            } else {
              alert('Error uploading image: ' + (response.error ? response.error.message : 'Unknown error'));
            }
            if (onComplete) onComplete();
          },
          error: function() {
            $('#' + progressId).remove();
            alert('Error uploading image. Please try again.');
            if (onComplete) onComplete();
          }
        });
      }
      
      // Add uploaded image preview
      function addUploadedImagePreview(imageData) {
        const imageId = 'uploaded-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9);
        const isFeatured = imageData.featured || false;
        const imageHtml = `
          <div class="uploaded-image-item ${isFeatured ? 'is-featured' : ''}" data-image-id="${imageId}">
            ${isFeatured ? '<div class="featured-badge"><i class="fa fa-star"></i> Featured</div>' : ''}
            <img src="${imageData.url}" alt="${imageData.alt}" class="uploaded-image-preview">
            <div class="uploaded-image-info">
              <input type="text" class="image-alt form-control" value="${imageData.alt}" placeholder="Alt text">
              <input type="text" class="image-caption form-control" value="${imageData.caption || ''}" placeholder="Caption (optional)">
              <div class="uploaded-image-actions">
                <button type="button" class="btn btn-sm ${isFeatured ? 'btn-warning' : 'btn-default'} image-set-featured" data-image-id="${imageId}">
                  <i class="fa fa-star${isFeatured ? '' : '-o'}"></i> ${isFeatured ? 'Featured' : 'Set Featured'}
                </button>
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
      
      // Set image as featured
      $(document).on('click', '.image-set-featured', function() {
        const imageId = $(this).data('image-id');
        const $item = $('[data-image-id="' + imageId + '"]');
        const wasFeatured = $item.hasClass('is-featured');
        
        // Remove featured from all images
        $('.uploaded-image-item').removeClass('is-featured');
        $('.featured-badge').remove();
        $('.image-set-featured').removeClass('btn-warning').addClass('btn-default')
          .html('<i class="fa fa-star-o"></i> Set Featured');
        
        // Set this image as featured if it wasn't already
        if (!wasFeatured) {
          $item.addClass('is-featured');
          $item.prepend('<div class="featured-badge"><i class="fa fa-star"></i> Featured</div>');
          $(this).removeClass('btn-default').addClass('btn-warning')
            .html('<i class="fa fa-star"></i> Featured');
        }
        
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
            caption: $item.find('.image-caption').val(),
            featured: $item.hasClass('is-featured')
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
      
      // Confirmation for delete button
      $('[data-confirm]').on('click', function(e) {
        if (!confirm($(this).data('confirm'))) {
          e.preventDefault();
          return false;
        }
      });

      // ========================================
      // BASIC FIELDS QUILL EDITORS
      // ========================================

      // Initialize Quill editors for basic fields (Abstract, Research Question, Study Area)
      waitForQuill(function() {
        // Build modules config with ImageResize if available
        var basicToolbar = [
          [{ 'header': [2, 3, false] }],
          ['bold', 'italic', 'underline'],
          [{ 'list': 'ordered'}, { 'list': 'bullet' }],
          ['link', 'image'],
          ['clean']
        ];
        var basicModules = { toolbar: basicToolbar };
        if (typeof ImageResize !== 'undefined') {
          basicModules.imageResize = { displaySize: true };
        }
        
        var basicFieldsQuillConfig = {
          theme: 'snow',
          modules: basicModules
        };

        // Abstract editor
        if ($('#abstract-editor').length) {
          var abstractEditor = new Quill('#abstract-editor', $.extend({}, basicFieldsQuillConfig, {
            placeholder: 'Brief summary of your data story...'
          }));
          var $abstractTextarea = $('#abstract');
          if ($abstractTextarea.val()) {
            abstractEditor.clipboard.dangerouslyPasteHTML($abstractTextarea.val());
          }
          abstractEditor.on('text-change', function() {
            $abstractTextarea.val(abstractEditor.root.innerHTML);
          });
        }

        // Research Question editor
        if ($('#research_question-editor').length) {
          var researchQuestionEditor = new Quill('#research_question-editor', $.extend({}, basicFieldsQuillConfig, {
            placeholder: 'What is the main research question addressed by this story?'
          }));
          var $researchQuestionTextarea = $('#research_question');
          if ($researchQuestionTextarea.val()) {
            researchQuestionEditor.clipboard.dangerouslyPasteHTML($researchQuestionTextarea.val());
          }
          researchQuestionEditor.on('text-change', function() {
            $researchQuestionTextarea.val(researchQuestionEditor.root.innerHTML);
          });
        }

        // Study Area editor
        if ($('#study_area-editor').length) {
          var studyAreaEditor = new Quill('#study_area-editor', $.extend({}, basicFieldsQuillConfig, {
            placeholder: 'Describe the geographic study area...'
          }));
          var $studyAreaTextarea = $('#study_area');
          if ($studyAreaTextarea.val()) {
            studyAreaEditor.clipboard.dangerouslyPasteHTML($studyAreaTextarea.val());
          }
          studyAreaEditor.on('text-change', function() {
            $studyAreaTextarea.val(studyAreaEditor.root.innerHTML);
          });
        }

        // Update hidden fields before form submit (for basic fields)
        $('.data-stories-form, form.data-stories-form').on('submit', function() {
          if (typeof abstractEditor !== 'undefined') {
            $('#abstract').val(abstractEditor.root.innerHTML);
          }
          if (typeof researchQuestionEditor !== 'undefined') {
            $('#research_question').val(researchQuestionEditor.root.innerHTML);
          }
          if (typeof studyAreaEditor !== 'undefined') {
            $('#study_area').val(studyAreaEditor.root.innerHTML);
          }
        });

        console.log('Basic fields Quill editors initialized');
      });

      // ========================================
      // PAPER DOI FUNCTIONALITY
      // ========================================
      
      // Show/hide fetch citation button based on DOI input
      $('#paper_doi').on('input', function() {
        const doiValue = $(this).val().trim();
        const fetchGroup = $('#fetch-citation-group');
        
        if (doiValue && doiValue.match(/^10\./)) {
          fetchGroup.show();
        } else {
          fetchGroup.hide();
        }
      });
      
      // Trigger on page load in case DOI is already filled
      $('#paper_doi').trigger('input');
      
      // Fetch citation from CrossRef API
      $('#fetch-citation-btn').on('click', function() {
        const $btn = $(this);
        const $citationField = $('#paper_citation');
        const doi = $('#paper_doi').val().trim();
        
        if (!doi) {
          alert('Please enter a DOI first');
          return;
        }
        
        // Show loading state
        const originalText = $btn.html();
        $btn.html('<i class="fa fa-spinner fa-spin"></i> Fetching...').prop('disabled', true);
        
        // Call CrossRef API
        const crossrefUrl = `https://api.crossref.org/works/${doi}`;
        
        fetch(crossrefUrl, {
          headers: {
            'Accept': 'application/json'
          }
        })
        .then(response => {
          if (!response.ok) {
            throw new Error('DOI not found or network error');
          }
          return response.json();
        })
        .then(data => {
          const work = data.message;
          
          // Format citation
          let citation = '';
          
          // Authors
          if (work.author && work.author.length > 0) {
            const authors = work.author.map(author => {
              if (author.family && author.given) {
                return `${author.family}, ${author.given.charAt(0)}.`;
              } else if (author.family) {
                return author.family;
              }
              return '';
            }).filter(a => a).join(', ');
            citation += authors;
          }
          
          // Year
          if (work.published && work.published['date-parts'] && work.published['date-parts'][0]) {
            const year = work.published['date-parts'][0][0];
            citation += ` (${year})`;
          }
          
          // Title
          if (work.title && work.title[0]) {
            citation += `. ${work.title[0]}`;
          }
          
          // Journal
          if (work['container-title'] && work['container-title'][0]) {
            citation += `. ${work['container-title'][0]}`;
          }
          
          // Volume and Issue
          if (work.volume) {
            citation += `, ${work.volume}`;
            if (work.issue) {
              citation += `(${work.issue})`;
            }
          }
          
          // Pages
          if (work.page) {
            citation += `, ${work.page}`;
          }
          
          // DOI
          citation += `. https://doi.org/${doi}`;
          
          // Set the citation
          $citationField.val(citation);
          
          // Show success message
          $citationField.after('<div class="alert alert-success" style="margin-top: 0.5rem;"><i class="fa fa-check"></i> Citation fetched successfully!</div>');
          setTimeout(function() {
            $citationField.next('.alert-success').fadeOut();
          }, 3000);
        })
        .catch(error => {
          console.error('Error fetching citation:', error);
          alert('Could not fetch citation. Please enter it manually.');
        })
        .finally(() => {
          // Restore button
          $btn.html(originalText).prop('disabled', false);
        });
      });

      console.log('Data Stories editor initialized successfully');
    });
  });
})();
