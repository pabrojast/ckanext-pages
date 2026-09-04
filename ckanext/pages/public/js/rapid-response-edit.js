/**
 * Rapid Response Edit Form JavaScript
 * Enhanced form functionality for rapid response page editing
 */

(function() {
  // User-provided values interpolated into HTML template strings must be
  // escaped: a quote in a map title would truncate the attribute on re-edit.
  function escapeHtml(str) {
    return String(str == null ? '' : str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  // Enhanced jQuery availability check with fallback handling
  function waitForJQuery(callback, attempts) {
    attempts = attempts || 0;
    
    // Check for both jQuery and $ availability
    if (typeof jQuery !== 'undefined' && typeof $ !== 'undefined') {
      try {
        // Test basic jQuery functionality
        if (typeof $().jquery !== 'undefined') {
          callback($);
          return;
        }
      } catch (e) {
        console.warn('jQuery test failed:', e);
      }
    }
    
    // If jQuery object exists but $ doesn't, create the alias
    if (typeof jQuery !== 'undefined' && typeof $ === 'undefined') {
      window.$ = jQuery;
      callback(jQuery);
      return;
    }
    
    // Max attempts to prevent infinite loops
    if (attempts > 200) { // 10 seconds max
      console.error('jQuery failed to load after 10 seconds');
      return;
    }
    
    setTimeout(function() {
      waitForJQuery(callback, attempts + 1);
    }, 50);
  }
  
  waitForJQuery(function($) {
  // Ensure DOM is ready before executing any jQuery operations
  $(document).ready(function() {
    
  // Utility function to format date for HTML date input
  function formatDateForInput(dateStr) {
    if (!dateStr) return '';
    // If it's already in YYYY-MM-DD format, return as is
    if (dateStr.match(/^\d{4}-\d{2}-\d{2}$/)) {
      return dateStr;
    }
    // If it's in ISO format (YYYY-MM-DDTHH:MM:SS), extract just the date part
    if (dateStr.includes('T')) {
      return dateStr.split('T')[0];
    }
    // If it's in other formats, try to parse and format
    try {
      const date = new Date(dateStr);
      if (!isNaN(date.getTime())) {
        return date.toISOString().split('T')[0];
      }
    } catch (e) {
      console.warn('Could not parse date:', dateStr);
    }
    return '';
  }
  
  // Key Information Management
  let customKeyInfoCounter = 0;
  
  // Function to update the hidden key_info field with structured data
  function updateKeyInfoData() {
    const keyInfoLines = [];
    
    // Event Timeline
    const eventStart = $('#key-event-start').val();
    const activation = $('#key-activation').val();
    
    if (eventStart) {
      keyInfoLines.push('Event Start: ' + new Date(eventStart).toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' }));
    }
    if (activation) {
      keyInfoLines.push('Activation: ' + new Date(activation).toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' }));
    }
    
    // UNESCO Sites (add subtitle header)
    const worldHeritage = $('#key-world-heritage').val();
    const biosphere = $('#key-biosphere').val();
    const geoparks = $('#key-geoparks').val();
    
    if (worldHeritage || biosphere || geoparks) {
      keyInfoLines.push('UNESCO Designated Sites Affected');
      if (worldHeritage) keyInfoLines.push('World Heritage Sites: ' + worldHeritage);
      if (biosphere) keyInfoLines.push('Biosphere Reserves: ' + biosphere);
      if (geoparks) keyInfoLines.push('Geoparks: ' + geoparks);
    }
    
    // Estimated Impact (add subtitle header)
    const peopleAffected = $('#key-people-affected').val();
    const casualties = $('#key-casualties').val();
    const damageUsd = $('#key-damage-usd').val();
    const citiesAffected = $('#key-cities-affected').val();
    
    if (peopleAffected || casualties || damageUsd || citiesAffected) {
      keyInfoLines.push('Estimated Impact');
      if (peopleAffected) keyInfoLines.push('Estimated number of people affected: ' + peopleAffected);
      if (casualties) keyInfoLines.push('Estimated number of casualties: ' + casualties);
      if (damageUsd) keyInfoLines.push('Estimated Damage (USD): ' + damageUsd);
      if (citiesAffected) keyInfoLines.push('Cities Affected: ' + citiesAffected);
    }
    
    // Custom fields
    $('.custom-key-info-field').each(function() {
      const label = $(this).find('.custom-key-label').val();
      const value = $(this).find('.custom-key-value').val();
      if (label && value) {
        keyInfoLines.push(label + ': ' + value);
      }
    });
    
    $('#field-key-info').val(keyInfoLines.join('\n'));
  }
  
  // Function to add custom key info field
  function addCustomKeyInfoField(label = '', value = '') {
    customKeyInfoCounter++;
    const labelPlaceholder = $('#add-custom-key-info').data('label-placeholder') || 'Field Label (e.g., Contact Person)';
    const valuePlaceholder = $('#add-custom-key-info').data('value-placeholder') || 'Field Value (e.g., John Smith, Emergency Coordinator)';
    
    const fieldHtml = `
      <div class="custom-key-info-field" data-id="${customKeyInfoCounter}">
        <div class="row">
          <div class="col-md-4 col-sm-12">
            <div class="form-group">
              <label class="sr-only">Field Label</label>
              <input type="text" class="custom-key-label rr-form-control" 
                     placeholder="${labelPlaceholder}" 
                     value="${label}"
                     title="Enter a descriptive label for this field">
            </div>
          </div>
          <div class="col-md-7 col-sm-12">
            <div class="form-group">
              <label class="sr-only">Field Value</label>
              <input type="text" class="custom-key-value rr-form-control" 
                     placeholder="${valuePlaceholder}" 
                     value="${value}"
                     title="Enter the value or content for this field">
            </div>
          </div>
          <div class="col-md-1 col-sm-12">
            <div class="form-group">
              <button type="button" class="btn btn-danger btn-sm remove-custom-field" 
                      title="Remove this field">
                <i class="fa fa-times"></i>
                <span class="sr-only">Remove field</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    `;
    $('#custom-key-info-fields').append(fieldHtml);
    
    // Focus on the label field of the newly added field
    $(`#custom-key-info-fields .custom-key-info-field[data-id="${customKeyInfoCounter}"] .custom-key-label`).focus();
    
    updateKeyInfoData();
  }
  
  // Load existing custom fields from key_info data
  function loadExistingCustomFields() {
    const keyInfoData = $('#field-key-info').val();
    if (keyInfoData) {
      const lines = keyInfoData.split('\n');
      const standardFields = [
        'Event Start', 'Activation', 'UNESCO Designated Sites Affected',
        'World Heritage Sites', 'Biosphere Reserves', 'Geoparks',
        'Estimated Impact', 'Estimated number of people affected',
        'Estimated number of casualties', 'Estimated Damage (USD)', 'Cities Affected'
      ];
      
      lines.forEach(line => {
        if (line.trim() && line.includes(':')) {
          const parts = line.split(':', 1);
          const label = parts[0].trim();
          const value = line.substring(line.indexOf(':') + 1).trim();
          
          // Check if this is not a standard field and not a subtitle
          if (!standardFields.includes(label) && 
              !['UNESCO Designated Sites Affected', 'Estimated Impact'].includes(line.trim())) {
            addCustomKeyInfoField(label, value);
          }
        }
      });
    }
  }
  
  // Event listeners for key info fields
  $(document).on('input change', '#key-event-start, #key-activation, #key-world-heritage, #key-biosphere, #key-geoparks, #key-people-affected, #key-casualties, #key-damage-usd, #key-cities-affected', updateKeyInfoData);
  
  $(document).on('input change', '.custom-key-label, .custom-key-value', updateKeyInfoData);
  
  $('#add-custom-key-info').click(function() {
    addCustomKeyInfoField();
  });
  
  $(document).on('click', '.remove-custom-field', function() {
    $(this).closest('.custom-key-info-field').remove();
    updateKeyInfoData();
  });

  // Timeline Events Management
  let timelineEventCounter = 0;
  let selectedCountries = [];
  
  // Countries list (based on rapid-response_list.html)
  const countriesList = [
    'Afghanistan', 'Albania', 'Algeria', 'Andorra', 'Angola', 'Antigua and Barbuda', 'Argentina', 'Armenia', 'Australia', 'Austria', 'Azerbaijan',
    'Bahamas', 'Bahrain', 'Bangladesh', 'Barbados', 'Belarus', 'Belgium', 'Belize', 'Benin', 'Bhutan', 'Bolivia', 'Bosnia and Herzegovina', 'Botswana', 'Brazil', 'Brunei', 'Bulgaria', 'Burkina Faso', 'Burundi',
    'Cabo Verde', 'Cambodia', 'Cameroon', 'Canada', 'Central African Republic', 'Chad', 'Chile', 'China', 'Colombia', 'Comoros', 'Congo', 'Cook Islands', 'Costa Rica', "Côte d'Ivoire", 'Croatia', 'Cuba', 'Cyprus', 'Czech Republic',
    'Democratic Republic of the Congo', 'Denmark', 'Djibouti', 'Dominica', 'Dominican Republic', 'Ecuador', 'Egypt', 'El Salvador', 'Equatorial Guinea', 'Eritrea', 'Estonia', 'Eswatini', 'Ethiopia',
    'Fiji', 'Finland', 'France', 'Gabon', 'Gambia', 'Georgia', 'Germany', 'Ghana', 'Greece', 'Grenada', 'Guatemala', 'Guinea', 'Guinea-Bissau', 'Guyana',
    'Haiti', 'Honduras', 'Hungary', 'Iceland', 'India', 'Indonesia', 'Iran', 'Iraq', 'Ireland', 'Israel', 'Italy', 'Jamaica', 'Japan', 'Jordan',
    'Kazakhstan', 'Kenya', 'Kiribati', 'Kuwait', 'Kyrgyzstan', 'Laos', 'Latvia', 'Lebanon', 'Lesotho', 'Liberia', 'Libya', 'Lithuania', 'Luxembourg',
    'Madagascar', 'Malawi', 'Malaysia', 'Maldives', 'Mali', 'Malta', 'Marshall Islands', 'Mauritania', 'Mauritius', 'Mexico', 'Micronesia', 'Moldova', 'Monaco', 'Mongolia', 'Montenegro', 'Morocco', 'Mozambique', 'Myanmar',
    'Namibia', 'Nauru', 'Nepal', 'Netherlands', 'New Zealand', 'Nicaragua', 'Niger', 'Nigeria', 'Niue', 'North Korea', 'North Macedonia', 'Norway',
    'Oman', 'Pakistan', 'Palau', 'Palestine', 'Panama', 'Papua New Guinea', 'Paraguay', 'Peru', 'Philippines', 'Poland', 'Portugal', 'Qatar',
    'Romania', 'Russia', 'Rwanda', 'Saint Kitts and Nevis', 'Saint Lucia', 'Saint Vincent and the Grenadines', 'Samoa', 'San Marino', 'São Tomé and Príncipe', 'Saudi Arabia', 'Senegal', 'Serbia', 'Seychelles', 'Sierra Leone', 'Singapore', 'Slovakia', 'Slovenia', 'Solomon Islands', 'Somalia', 'South Africa', 'South Korea', 'South Sudan', 'Spain', 'Sri Lanka', 'Sudan', 'Suriname', 'Sweden', 'Switzerland', 'Syria',
    'Tajikistan', 'Tanzania', 'Thailand', 'Timor-Leste', 'Togo', 'Tonga', 'Trinidad and Tobago', 'Tunisia', 'Turkey', 'Turkmenistan', 'Tuvalu',
    'Uganda', 'Ukraine', 'United Arab Emirates', 'United Kingdom', 'United States', 'Uruguay', 'Uzbekistan', 'Vanuatu', 'Vatican City', 'Venezuela', 'Vietnam', 'Yemen', 'Zambia', 'Zimbabwe'
  ];
  
  // Load countries into select dropdown
  function loadCountries() {
    const $select = $('#country-select');
    $select.empty();
    $select.append('<option value="">Select a country...</option>');
    
    // Sort countries alphabetically and add to select
    countriesList.sort().forEach(function(country) {
      $select.append(`<option value="${country}">${country}</option>`);
    });
    
    // Load existing countries
    loadExistingCountries();
  }
  
  // Load existing countries from data
  function loadExistingCountries() {
    // Try new format first (JSON array)
    const countriesData = $('#countries-data').val();
    if (countriesData) {
      try {
        selectedCountries = JSON.parse(countriesData);
        selectedCountries.forEach(country => {
          addCountryToList(country);
        });
        updateBackwardCompatibility();
        return;
      } catch (e) {
        console.log('Could not parse countries JSON, trying legacy format');
      }
    }
    
    // Fallback to legacy format (comma-separated string)
    const legacyCountryData = $('input[name="country"]').val();
    if (legacyCountryData) {
      const countries = legacyCountryData.split(',').map(c => c.trim()).filter(c => c);
      selectedCountries = countries.map(country => ({
        name: country,
        display_name: country
      }));
      selectedCountries.forEach(country => {
        addCountryToList(country);
      });
      updateCountriesData();
    }
  }
  
  // Add country to the list
  function addCountryToList(country) {
    const countryId = `country-${country.name.replace(/\s+/g, '-').toLowerCase()}`;
    if ($(`#${countryId}`).length) {
      return; // Already added
    }
    
    const countryHtml = `
      <div class="country-item" id="${countryId}" data-country-name="${country.name}">
        <span class="country-name">${country.display_name || country.name}</span>
        <button type="button" class="btn btn-sm btn-danger remove-country" data-country-name="${country.name}">
          <i class="fa fa-times"></i>
        </button>
      </div>
    `;
    $('#selected-countries').append(countryHtml);
  }
  
  // Update countries data
  function updateCountriesData() {
    $('#countries-data').val(JSON.stringify(selectedCountries));
    updateBackwardCompatibility();
  }
  
  // Update backward compatibility field
  function updateBackwardCompatibility() {
    const countryNames = selectedCountries.map(c => c.name).join(', ');
    $('#country-backward-compat').val(countryNames);
    $('input[name="country"]').val(countryNames);
  }
  
  // Handle add country button
  $('#add-country').on('click', function() {
    const $select = $('#country-select');
    const countryName = $select.val();
    
    if (!countryName) {
      return;
    }
    
    // Check if already added
    if (selectedCountries.find(c => c.name === countryName)) {
      alert('This country has already been added');
      return;
    }
    
    const country = {
      name: countryName,
      display_name: countryName
    };
    
    selectedCountries.push(country);
    addCountryToList(country);
    updateCountriesData();
    
    // Reset select
    $select.val('');
  });
  
  // Handle remove country
  $(document).on('click', '.remove-country', function() {
    const countryName = $(this).data('country-name');
    const countryId = `country-${countryName.replace(/\s+/g, '-').toLowerCase()}`;
    $(`#${countryId}`).remove();
    selectedCountries = selectedCountries.filter(c => c.name !== countryName);
    updateCountriesData();
  });
  
  // Load existing timeline events
  function loadTimelineEvents() {
    const timelineData = $('#timeline-events-data').val();
    if (timelineData) {
      try {
        const events = JSON.parse(timelineData);
        events.forEach(event => {
          addTimelineEvent(event);
        });
      } catch (e) {
        console.error('Error parsing timeline data:', e);
      }
    }
  }
  
  // Add timeline event
  function addTimelineEvent(eventData = null) {
    timelineEventCounter++;
    const eventId = `timeline-event-${timelineEventCounter}`;
    
    const eventHtml = `
      <div class="timeline-event-item" data-event-id="${eventId}">
        <div class="timeline-header">
          <div class="timeline-event-number">${timelineEventCounter}</div>
          <button type="button" class="timeline-remove-btn" onclick="removeTimelineEvent('${eventId}')">
            <i class="fa fa-trash"></i> Remove
          </button>
        </div>
        <div class="timeline-event-fields">
          <div class="timeline-field-group">
            <label>Date</label>
            <input type="date" class="timeline-date" value="${eventData ? formatDateForInput(eventData.date) : ''}" placeholder="Event date">
          </div>
          <div class="timeline-field-group">
            <label>Event Description</label>
            <textarea class="timeline-description" placeholder="Describe what happened on this date...">${eventData ? eventData.description : ''}</textarea>
          </div>
          <div class="timeline-field-group">
            <label>Event Type</label>
            <select class="timeline-type">
              <option value="activation" ${eventData && eventData.type === 'activation' ? 'selected' : ''}>Activation</option>
              <option value="assessment" ${eventData && eventData.type === 'assessment' ? 'selected' : ''}>Assessment</option>
              <option value="response" ${eventData && eventData.type === 'response' ? 'selected' : ''}>Response</option>
              <option value="recovery" ${eventData && eventData.type === 'recovery' ? 'selected' : ''}>Recovery</option>
              <option value="update" ${eventData && eventData.type === 'update' ? 'selected' : ''}>Update</option>
              <option value="closure" ${eventData && eventData.type === 'closure' ? 'selected' : ''}>Closure</option>
            </select>
          </div>
        </div>
      </div>
    `;
    
    $('.timeline-events-list').append(eventHtml);
    updateTimelineData();
  }
  
  // Remove timeline event
  window.removeTimelineEvent = function(eventId) {
    $(`.timeline-event-item[data-event-id="${eventId}"]`).remove();
    updateTimelineEventNumbers();
    updateTimelineData();
  };
  
  // Update timeline event numbers
  function updateTimelineEventNumbers() {
    $('.timeline-event-item').each(function(index) {
      $(this).find('.timeline-event-number').text(index + 1);
    });
  }
  
  // Update timeline data
  function updateTimelineData() {
    const events = [];
    $('.timeline-event-item').each(function() {
      const $item = $(this);
      const event = {
        date: $item.find('.timeline-date').val(),
        description: $item.find('.timeline-description').val(),
        type: $item.find('.timeline-type').val()
      };
      if (event.date || event.description) {
        events.push(event);
      }
    });
    $('#timeline-events-data').val(JSON.stringify(events));
  }
  
  // Event Type Management
  $('#field-event-type').on('change', function() {
    const selectedOption = $(this).find('option:selected');
    const eventTypeId = selectedOption.data('event-id') || '';
    $('#field-event-type-id').val(eventTypeId);
  });
  
  // Initialize event type ID on page load
  try {
    const initialSelectedOption = $('#field-event-type').find('option:selected');
    if (initialSelectedOption.length && initialSelectedOption.data('event-id')) {
      $('#field-event-type-id').val(initialSelectedOption.data('event-id'));
    }
  } catch (e) {
    console.warn('Error initializing event type ID:', e);
  }

  // Event listeners
  $('#add-timeline-event').click(function() {
    addTimelineEvent();
  });
  
  $(document).on('change input', '.timeline-date, .timeline-description, .timeline-type', function() {
    updateTimelineData();
  });
  
  // Image Upload Management
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
      // Clear the input so the same file can be selected again
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
    try {
      $(this).removeClass('dragover');
    } catch (err) {
      console.warn('Error handling dragleave:', err);
    }
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
    const progressId = `progress-${Date.now()}`;
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
            $(`#${progressId} .progress-bar`).css('width', percentComplete + '%');
          }
        }, false);
        return xhr;
      },
      success: function(response) {
        $(`#${progressId}`).remove();
        if (response.uploaded === 1) {
          const imageData = {
            url: response.url,
            fileName: response.fileName,
            alt: file.name.replace(/\.[^/.]+$/, ""), // Remove extension for alt text
            caption: ''
          };
          uploadedImages.push(imageData);
          addUploadedImagePreview(imageData);
          updateUploadedImagesData();
        } else {
          alert('Error uploading image: ' + (response.error ? response.error.message : 'Unknown error'));
        }
        if (onComplete) onComplete();
      },
      error: function() {
        $(`#${progressId}`).remove();
        alert('Error uploading image. Please try again.');
        if (onComplete) onComplete();
      }
    });
  }
  
  // Add uploaded image preview
  function addUploadedImagePreview(imageData) {
    const imageId = `uploaded-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    const imageHtml = `
      <div class="uploaded-image-item" data-image-id="${imageId}">
        <img src="${imageData.url}" alt="${imageData.alt}" class="uploaded-image-preview">
        <div class="uploaded-image-info">
          <input type="text" class="image-alt" value="${imageData.alt}" placeholder="Alt text">
          <input type="text" class="image-caption" value="${imageData.caption}" placeholder="Caption (optional)">
          <div class="uploaded-image-actions">
            <button type="button" class="image-copy-url" onclick="copyImageUrl('${imageData.url}')">
              <i class="fa fa-copy"></i> Copy URL
            </button>
            <button type="button" class="image-remove" onclick="removeUploadedImage('${imageId}')">
              <i class="fa fa-trash"></i>
            </button>
          </div>
        </div>
      </div>
    `;
    $('#uploaded-images-preview').append(imageHtml);
  }
  
  // Copy image URL to clipboard
  window.copyImageUrl = function(url) {
    navigator.clipboard.writeText(url).then(function() {
      // Show temporary success message
      const btn = event.target.closest('.image-copy-url');
      const originalText = btn.innerHTML;
      btn.innerHTML = '<i class="fa fa-check"></i> Copied!';
      setTimeout(() => {
        btn.innerHTML = originalText;
      }, 2000);
    });
  };
  
  // Remove uploaded image
  window.removeUploadedImage = function(imageId) {
    $(`.uploaded-image-item[data-image-id="${imageId}"]`).remove();
    // Update uploadedImages array
    const $removedItem = $(`.uploaded-image-item[data-image-id="${imageId}"]`);
    const imageUrl = $removedItem.find('img').attr('src');
    uploadedImages = uploadedImages.filter(img => img.url !== imageUrl);
    updateUploadedImagesData();
  };
  
  // Update uploaded images data
  function updateUploadedImagesData() {
    // Update data from current DOM state
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
    
    // Also update image gallery data for easier template rendering
    const galleryData = uploadedImages.map(img => ({
      type: 'uploaded',
      url: img.url,
      alt: img.alt,
      caption: img.caption
    }));
    $('#image-gallery-data').val(JSON.stringify(galleryData));
  }
  
  // Update image data when alt text or caption changes
  $(document).on('change input', '.image-alt, .image-caption', function() {
    updateUploadedImagesData();
  });
  
  // Auto-generate URL slug from title
  $('#field-title').on('input', function() {
    if ($('#field-name').prop('readonly')) {
      var title = $(this).val().toLowerCase()
        .replace(/[^\w ]+/g,'')
        .replace(/ +/g,'-');
      $('#field-name').val(title);
    }
  });
  
  // Toggle URL field editing
  $('#edit-url-btn').on('click', function() {
    var $urlField = $('#field-name');
    var $btn = $(this);
    
    if ($urlField.prop('readonly')) {
      $urlField.prop('readonly', false).focus();
      $btn.html('<i class="fa fa-lock"></i>').attr('title', 'Lock auto-generation');
      $btn.removeClass('btn-default').addClass('btn-warning');
    } else {
      $urlField.prop('readonly', true);
      $btn.html('<i class="fa fa-edit"></i>').attr('title', 'Edit URL manually');
      $btn.removeClass('btn-warning').addClass('btn-default');
      // Re-generate from title
      var title = $('#field-title').val().toLowerCase()
        .replace(/[^\w ]+/g,'')
        .replace(/ +/g,'-');
      $urlField.val(title);
    }
  });
  
  // Form validation - REMOVED (merged with unified handler below)
  // Note: Form submission handling has been unified to prevent conflicts
  
  // WYSIWYG editor integration if available
  // Replace CKEditor with Quill
  function waitForQuill(callback) {
    if (typeof Quill !== 'undefined') {
      callback();
    } else {
      setTimeout(function(){ waitForQuill(callback); }, 50);
    }
  }

  // Spatial Data helpers: toggle preview and insert iframe snippet
  function sanitizePreviewHtml(html) {
    // Allow only iframes and basic block elements in preview to avoid script execution
    var temp = document.createElement('div');
    temp.innerHTML = html;
    // Remove script/style tags
    $(temp).find('script, style').remove();
    // Remove on* attributes
    $(temp).find('*').each(function(){
      $.each(this.attributes || [], function(){
        if (this && this.name && this.name.toLowerCase().startsWith('on')) {
          $(this.ownerElement).removeAttr(this.name);
        }
      });
    });
    return temp.innerHTML;
  }

  // Markdown detection and conversion for mixed Markdown + HTML content
  function isLikelyMarkdown(text) {
    if (!text) return false;
    var mdSignals = [
      /(^|\n)\s{0,3}#{1,6}\s+/,             // headings
      /\*\*[^\n]+\*\*|__[^\n]+__/,         // bold
      /(^|\n)\s{0,3}[-*+]\s+/,              // lists
      /\[[^\]]+\]\([^\)]+\)/,            // links
      /(^|\n)\s{0,3}>\s+/,                  // blockquote
    ];
    return mdSignals.some(function(rx){ return rx.test(text); });
  }

  function markdownToHtml(md) {
    if (!md) return '';
    try {
      if (window.marked && typeof window.marked.parse === 'function') {
        // Marked will pass-through raw HTML like iframes
        var html = window.marked.parse(md, { breaks: true, gfm: true, mangle: false, headerIds: false });
        return sanitizePreviewHtml(html);
      }
    } catch (e) { /* fallback below */ }
    // Fallback minimal conversion (headings, bold/italic, lists)
    var htmlFallback = md
      .replace(/\r\n/g, '\n')
      .replace(/(^|\n)######\s?(.+)(?=\n|$)/g, '$1<h6>$2</h6>')
      .replace(/(^|\n)#####\s?(.+)(?=\n|$)/g, '$1<h5>$2</h5>')
      .replace(/(^|\n)####\s?(.+)(?=\n|$)/g, '$1<h4>$2</h4>')
      .replace(/(^|\n)###\s?(.+)(?=\n|$)/g, '$1<h3>$2</h3>')
      .replace(/(^|\n)##\s?(.+)(?=\n|$)/g, '$1<h2>$2</h2>')
      .replace(/(^|\n)#\s?(.+)(?=\n|$)/g, '$1<h1>$2</h1>')
      .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
      .replace(/__([^_]+)__/g, '<strong>$1</strong>')
      .replace(/\*([^*]+)\*/g, '<em>$1</em>')
      .replace(/_([^_]+)_/g, '<em>$1</em>')
      .replace(/\n\n+/g, '</p><p>')
      .replace(/^/, '<p>')
      .replace(/$/, '</p>')
      ;
    return sanitizePreviewHtml(htmlFallback);
  }

  function extractMapStoriesInner(html) {
    try {
      var container = document.createElement('div');
      container.innerHTML = html;
      var inner = container.querySelector('.map-stories-content');
      if (inner) { return inner.innerHTML; }
      var rrBody = container.querySelector('.rr-module-maps .rr-content-body');
      if (rrBody) { return rrBody.innerHTML; }
    } catch (err) {}
    return null;
  }

  // Preview for map stories works from source textarea content
  $(document).on('click', '#toggle-map-preview', function(){
    var $container = $('#map-stories-preview-container');
    var $btn = $(this);
    if ($container.is(':visible')) {
      $container.hide();
      $btn.html('<i class="fa fa-eye"></i> Show Preview');
    } else {
      // If visual is visible, first sync to textarea
      if ($('#map-stories-visual').is(':visible') && window.quillEditors && window.quillEditors['map-stories-editor']) {
        try { $('#field-map-stories').val(window.quillEditors['map-stories-editor'].root.innerHTML); } catch(e) {}
      }
      var raw = $('#field-map-stories').val() || '';
      if (raw.indexOf('rapid-response-map-stories') !== -1 || raw.indexOf('map-stories-content') !== -1 || raw.indexOf('rr-module-maps') !== -1) {
        var extracted = extractMapStoriesInner(raw);
        if (extracted) { raw = extracted; }
      }
      $('#map-stories-preview').html(sanitizePreviewHtml(raw));
      $container.show();
      $btn.html('<i class="fa fa-eye-slash"></i> Hide Preview');
    }
  });

  $('#insert-iframe').on('click', function(){
    var tpl = '\n\n<iframe src="https://example.com" width="100%" height="420" frameborder="0" allowfullscreen></iframe>\n';
    var ta = document.getElementById('field-map-stories');
    if (!ta) return;
    var start = ta.selectionStart || 0;
    var end = ta.selectionEnd || 0;
    var val = ta.value;
    ta.value = val.substring(0, start) + tpl + val.substring(end);
    ta.focus();
    // Move cursor after inserted block
    var pos = start + tpl.length;
    ta.setSelectionRange(pos, pos);
  });

  // Iframe templates for common providers
  function insertAtCursor(textarea, snippet) {
    var ta = textarea; if (!ta) return;
    var start = ta.selectionStart || 0; var end = ta.selectionEnd || 0; var val = ta.value;
    ta.value = val.substring(0, start) + snippet + val.substring(end);
    ta.focus();
    var pos = start + snippet.length; ta.setSelectionRange(pos, pos);
  }

  $('#insert-iframe-arcgis').on('click', function(){
    var tpl = '\n\n<iframe src="https://www.arcgis.com/apps/mapviewer/index.html?webmap=YOUR_WEBMAP_ID" width="100%" height="600" style="border:none;" allowfullscreen></iframe>\n';
    insertAtCursor(document.getElementById('field-map-stories'), tpl);
  });

  $('#insert-iframe-copernicus').on('click', function(){
    var tpl = '\n\n<iframe src="https://emergency.copernicus.eu/EMSR/?some=params" width="100%" height="600" style="border:none;" allowfullscreen></iframe>\n';
    insertAtCursor(document.getElementById('field-map-stories'), tpl);
  });

  $('#insert-iframe-terria').on('click', function(){
    var tpl = '\n\n<iframe src="https://ihp-wins.unesco.org/terria/#share=YOUR_SHARE_ID" width="100%" height="600" style="border:none;" allowfullscreen mozallowfullscreen webkitallowfullscreen></iframe>\n';
    insertAtCursor(document.getElementById('field-map-stories'), tpl);
  });

  // Markdown helpers (Source mode)
  function surroundSelection(ta, before, after) {
    var start = ta.selectionStart || 0; var end = ta.selectionEnd || 0; var val = ta.value;
    var sel = val.substring(start, end);
    var res = before + sel + (after === undefined ? '' : after);
    ta.value = val.substring(0, start) + res + val.substring(end);
    var pos = start + res.length; ta.focus(); ta.setSelectionRange(pos, pos);
  }

  $('#fmt-h2').on('click', function(){ var ta=document.getElementById('field-map-stories'); if(!ta) return; surroundSelection(ta, '\n\n## ', '');});
  $('#fmt-h3').on('click', function(){ var ta=document.getElementById('field-map-stories'); if(!ta) return; surroundSelection(ta, '\n\n### ', '');});
  $('#fmt-ul').on('click', function(){ var ta=document.getElementById('field-map-stories'); if(!ta) return; surroundSelection(ta, '\n\n- ', '');});
  $('#fmt-ol').on('click', function(){ var ta=document.getElementById('field-map-stories'); if(!ta) return; surroundSelection(ta, '\n\n1. ', '');});
  $('#fmt-bold').on('click', function(){ var ta=document.getElementById('field-map-stories'); if(!ta) return; surroundSelection(ta, '**', '**');});
  $('#fmt-italic').on('click', function(){ var ta=document.getElementById('field-map-stories'); if(!ta) return; surroundSelection(ta, '*', '*');});
  $('#fmt-link').on('click', function(){ var ta=document.getElementById('field-map-stories'); if(!ta) return; surroundSelection(ta, '[text](', ')');});
  $('#fmt-image').on('click', function(){ var ta=document.getElementById('field-map-stories'); if(!ta) return; surroundSelection(ta, '![](https://example.com/image.jpg)', '');});

  // Paste as Markdown: clean pasted HTML and leave only Markdown
  $('#paste-markdown').on('click', function(){
    var ta = document.getElementById('field-map-stories'); if (!ta) return;
    navigator.clipboard.readText().then(function(txt){
      if (!txt) return;
      // If clipboard brings HTML (page blocks), just paste as is; Marked will understand it
      ta.value += (ta.value ? '\n\n' : '') + txt;
      ta.focus(); ta.setSelectionRange(ta.value.length, ta.value.length);
    });
  });

  // Convert Markdown → HTML directly in Source (useful for reviewing in Visual)
  $('#convert-markdown').on('click', function(){
    var ta = document.getElementById('field-map-stories'); if (!ta) return;
    var md = ta.value || '';
    if (isLikelyMarkdown(md)) { ta.value = markdownToHtml(md); }
  });

  // On load: process textarea content but keep it hidden by default
  (function(){
    var $ta = $('#field-map-stories');
    if ($ta.length) {
      // Keep textarea hidden by default
      $ta.css({ display: 'none' });
      
      var val = $ta.val() || '';
      // If looks like Markdown, convert to HTML immediately so editor visual shows well
      if (isLikelyMarkdown(val)) {
        var converted = markdownToHtml(val);
        if (converted) { $ta.val(converted); }
      }
      if (val.indexOf('rapid-response-map-stories') !== -1 || val.indexOf('map-stories-content') !== -1 || val.indexOf('rr-module-maps') !== -1) {
        var extracted = extractMapStoriesInner(val);
        if (extracted && extracted.trim()) {
          $ta.val(extracted.trim());
          if (!$('#map-stories-clean-notice').length) {
            $('<div id="map-stories-clean-notice" class="help-text" style="margin-top:6px;"><i class="fa fa-info-circle"></i> We detected wrapped page markup and cleaned it. You can paste only your section text and iframes here.</div>').insertAfter($ta);
          }
        }
      }
    }
  })();

  function initializeQuillEditors() {
    var quillEditors = {};
    var fullToolbar = [
      [{ 'header': [1, 2, 3, false] }],
      ['bold', 'italic', 'underline', 'strike'],
      [{ 'color': [] }, { 'background': [] }],
      [{ 'list': 'ordered' }, { 'list': 'bullet' }],
      [{ 'indent': '-1' }, { 'indent': '+1' }],
      ['blockquote', 'code-block'],
      ['link', 'image', 'video'],
      ['clean'],
      [{ 'align': [] }]
    ];
    var compactToolbar = [
      [{ 'header': [2, 3, false] }],
      ['bold', 'italic', 'underline'],
      [{ 'list': 'ordered' }, { 'list': 'bullet' }],
      ['link', 'image'],
      ['clean']
    ];

    // Register ImageResize module if available
    if (typeof ImageResize !== 'undefined') {
      Quill.register('modules/imageResize', ImageResize.default || ImageResize);
    }

    var editorConfigs = {
      'content-editor': { textareaId: 'field-content', toolbar: fullToolbar, placeholder: 'Detailed description of the emergency event, when and where it occurred, and its overall impact...' },
      'impact-assessment-editor': { textareaId: 'field-impact-assessment', toolbar: compactToolbar, placeholder: 'Describe the damage to heritage sites, communities affected, and ongoing concerns...' },
      'response-activities-editor': { textareaId: 'field-response-activities', toolbar: compactToolbar, placeholder: 'Detail the immediate response efforts, agencies involved, and current status...' },
      'excerpt-editor': { textareaId: 'field-excerpt', toolbar: [['bold','italic','underline'], [{ 'list': 'ordered' }, { 'list': 'bullet' }], ['link'], ['clean']], placeholder: 'Brief summary of the disaster and response efforts...' }
    };

    Object.keys(editorConfigs).forEach(function(editorId){
      var cfg = editorConfigs[editorId];
      var editorEl = document.getElementById(editorId);
      var textarea = document.getElementById(cfg.textareaId);
      if (!editorEl || !textarea) return;
      
      // Build modules config with ImageResize if available
      var modulesConfig = { toolbar: cfg.toolbar, history: { delay: 1000, maxStack: 50 } };
      if (typeof ImageResize !== 'undefined') {
        modulesConfig.imageResize = { displaySize: true };
      }
      
      var quill = new Quill('#' + editorId, { theme: 'snow', modules: modulesConfig, placeholder: cfg.placeholder });
      if (textarea.value) {
        try { quill.clipboard.dangerouslyPasteHTML(textarea.value); } catch(e) { quill.setText(textarea.value); }
      }
      quill.on('text-change', function(){ textarea.value = quill.root.innerHTML; $(textarea).trigger('change'); });
      $(editorEl).attr('role','textbox').attr('aria-label', cfg.placeholder);
      quillEditors[editorId] = quill;
    });

    window.quillEditors = quillEditors;
    window.syncAllQuillEditors = function(){
      if (!window.quillEditors) return;
      Object.keys(window.quillEditors).forEach(function(editorId){
        var quill = window.quillEditors[editorId];
        var cfg = editorConfigs[editorId];
        var textarea = document.getElementById(cfg.textareaId);
        if (quill && textarea) { textarea.value = quill.root.innerHTML; $(textarea).trigger('change'); }
      });
    };

    // Hide source textareas
    setTimeout(function(){
      Object.keys(editorConfigs).forEach(function(editorId){
        var cfg = editorConfigs[editorId];
        var textarea = document.getElementById(cfg.textareaId);
        if (textarea) {
          $(textarea).css({ 'display':'none', 'visibility':'hidden', 'position':'absolute', 'left':'-9999px', 'top':'-9999px', 'width':'1px', 'height':'1px', 'opacity':'0', 'z-index':'-9999' });
        }
      });
    }, 200);

    // Map Stories: Visual editor with iframe support via raw HTML conversion
    (function initMapStoriesEditor(){
      var editorEl = document.getElementById('map-stories-editor');
      var textarea = document.getElementById('field-map-stories');
      if (!editorEl || !textarea) return;
      var mapQuill = new Quill('#map-stories-editor', { theme: 'snow', modules: { toolbar: fullToolbar, history: { delay: 1000, maxStack: 50 } }, placeholder: 'Write your text and paste iframes. Use the Source tab if something is stripped.' });
      // Set initial content from textarea
      if (textarea.value) {
        var initial = textarea.value;
        // If it looks like Markdown, convert to HTML before loading, preserving any raw iframes
        if (isLikelyMarkdown(initial)) {
          initial = markdownToHtml(initial);
        }
        try { mapQuill.clipboard.dangerouslyPasteHTML(initial); } catch(e) { mapQuill.setText(initial); }
      }
      // Sync to textarea: prefer getHTML fallbacks to preserve iframes
      function syncMapStories(){
        var html = mapQuill.root.innerHTML;
        // If Quill stripped iframes, they won't be present; keep user's source if source mode active
        textarea.value = html;
        $(textarea).trigger('change');
      }
      mapQuill.on('text-change', syncMapStories);

      // Toggle source/visual
      $('#map-stories-toggle-source').on('click', function(){
        var visual = $('#map-stories-visual');
        var source = $('#map-stories-source');
        if (source.is(':visible')) {
          // Source -> Visual
          var raw = $('#field-map-stories').val() || '';
          if (isLikelyMarkdown(raw)) { raw = markdownToHtml(raw); }
          try { mapQuill.clipboard.dangerouslyPasteHTML(raw); } catch(e) { mapQuill.setText(raw); }
          source.hide();
          visual.show();
          $(this).html('<i class="fa fa-code"></i> Source (Markdown/HTML)');
        } else {
          // Visual -> Source
          syncMapStories();
          visual.hide();
          source.show();
          $(this).html('<i class="fa fa-eye"></i> Visual Editor');
        }
      });
    })();
  }
  
  // Confirmation for delete button
  $('[data-confirm]').on('click', function(e) {
    if (!confirm($(this).data('confirm'))) {
      e.preventDefault();
      return false;
    }
  });
  
    // Ensure title field is editable on load
  $('#field-title').prop('readonly', false).prop('disabled', false);
  
  // Set default author if field is empty
  if (!$('#field-author').val() || $('#field-author').val().trim() === '') {
    $('#field-author').val('IHP-WINS');
  }
  
  // Debug info
  console.log('Title field properties:', {
    readonly: $('#field-title').prop('readonly'),
    disabled: $('#field-title').prop('disabled'),
    value: $('#field-title').val()
  });
  
  console.log('Author field value:', $('#field-author').val());
  
  // Debug date field
  const publishDateValue = $('#field-publish-date').val();
  if (publishDateValue) {
    console.log('Publish date field value:', publishDateValue);
  }

  // ========================================
  // MODULAR CONTENT BLOCKS SYSTEMS
  // ========================================
  
  // Impact Assessment Blocks System
  let impactBlocks = [];
  let impactBlockCounter = 0;
  let impactQuillEditors = {};
  
  // Response Activities Blocks System
  let responseBlocks = [];
  let responseBlockCounter = 0;
  let responseQuillEditors = {};
  
  // Additional Information Blocks System (formerly Spatial Data)
  let additionalBlocks = [];
  let additionalBlockCounter = 0;
  let additionalQuillEditors = {};
  
  // Recovery Phase Blocks System
  let recoveryBlocks = [];
  let recoveryBlockCounter = 0;
  let recoveryQuillEditors = {};
  
  // Resilience Phase Blocks System
  let resilienceBlocks = [];
  let resilienceBlockCounter = 0;
  let resilienceQuillEditors = {};

  // Initialize Impact Assessment Blocks System
  function initializeImpactAssessmentBlocks() {
    loadExistingImpactContent();
    
    $('#add-impact-text-block').on('click', function() {
      addImpactTextBlock();
    });
    
    $('#add-impact-iframe-block').on('click', function() {
      addImpactIframeBlock();
    });
  }
  
  // Initialize Response Activities Blocks System
  function initializeResponseActivitiesBlocks() {
    loadExistingResponseContent();
    
    $('#add-response-text-block').on('click', function() {
      addResponseTextBlock();
    });
    
    $('#add-response-iframe-block').on('click', function() {
      addResponseIframeBlock();
    });
  }
  
  // Initialize Additional Information Blocks System (formerly Spatial)
  function initializeAdditionalInformationBlocks() {
    loadExistingAdditionalContent();
    
    $('#add-additional-text-block').on('click', function() {
      addAdditionalTextBlock();
    });
    
    $('#add-additional-iframe-block').on('click', function() {
      addAdditionalIframeBlock();
    });
  }
  
  // Initialize Recovery Phase Blocks System
  function initializeRecoveryPhaseBlocks() {
    loadExistingRecoveryContent();
    
    $('#add-recovery-text-block').on('click', function() {
      addRecoveryTextBlock();
    });
    
    $('#add-recovery-iframe-block').on('click', function() {
      addRecoveryIframeBlock();
    });
  }
  
  // Initialize Resilience Phase Blocks System
  function initializeResiliencePhaseBlocks() {
    loadExistingResilienceContent();
    
    $('#add-resilience-text-block').on('click', function() {
      addResilienceTextBlock();
    });
    
    $('#add-resilience-iframe-block').on('click', function() {
      addResilienceIframeBlock();
    });
  }

  // Load existing content functions for each block system
  function loadExistingImpactContent() {
    const blocksMetadata = $('#impact-assessment-blocks-metadata').val();
    loadContentBlocks(blocksMetadata, 'impact', impactBlocks, '#impact-assessment-content-blocks', '#field-impact-assessment');
    updateImpactBlocksDisplay();
  }
  
  function loadExistingResponseContent() {
    const blocksMetadata = $('#response-activities-blocks-metadata').val();
    loadContentBlocks(blocksMetadata, 'response', responseBlocks, '#response-activities-content-blocks', '#field-response-activities');
    updateResponseBlocksDisplay();
  }
  
  function loadExistingAdditionalContent() {
    const blocksMetadata = $('#additional-info-blocks-metadata').val();
    loadContentBlocks(blocksMetadata, 'additional', additionalBlocks, '#additional-information-content-blocks', '#field-map-stories');
    updateAdditionalBlocksDisplay();
  }
  
  function loadExistingRecoveryContent() {
    const blocksMetadata = $('#recovery-phase-blocks-metadata').val();
    loadContentBlocks(blocksMetadata, 'recovery', recoveryBlocks, '#recovery-phase-content-blocks', '#field-recovery-phase');
    updateRecoveryBlocksDisplay();
  }
  
  function loadExistingResilienceContent() {
    const blocksMetadata = $('#resilience-phase-blocks-metadata').val();
    loadContentBlocks(blocksMetadata, 'resilience', resilienceBlocks, '#resilience-phase-content-blocks', '#field-resilience-phase');
    updateResilienceBlocksDisplay();
  }
  
  // Generic function to load content blocks
  function loadContentBlocks(blocksMetadata, blockType, blocksArray, containerSelector, fallbackFieldSelector) {
    if (blocksMetadata && blocksMetadata.trim()) {
      try {
        const blocks = JSON.parse(blocksMetadata);
        
        // Clear existing blocks
        blocksArray.length = 0;
        $(containerSelector).empty();
        
        // Recreate blocks from metadata
        blocks.forEach(blockData => {
          if (blockData.type === 'text') {
            let blockId;
            if (blockType === 'impact') {
              blockId = blockData.id || (blockType + '-block-' + (++impactBlockCounter));
            } else if (blockType === 'response') {
              blockId = blockData.id || (blockType + '-block-' + (++responseBlockCounter));
            } else if (blockType === 'additional') {
              blockId = blockData.id || (blockType + '-block-' + (++additionalBlockCounter));
            } else if (blockType === 'recovery') {
              blockId = blockData.id || (blockType + '-block-' + (++recoveryBlockCounter));
            } else if (blockType === 'resilience') {
              blockId = blockData.id || (blockType + '-block-' + (++resilienceBlockCounter));
            }
            
            const block = {
              id: blockId,
              type: 'text',
              content: blockData.content || ''
            };
            
            blocksArray.push(block);
            renderContentTextBlock(block, blockType, containerSelector);
            
          } else if (blockData.type === 'iframe') {
            let blockId;
            if (blockType === 'impact') {
              blockId = blockData.id || (blockType + '-block-' + (++impactBlockCounter));
            } else if (blockType === 'response') {
              blockId = blockData.id || (blockType + '-block-' + (++responseBlockCounter));
            } else if (blockType === 'additional') {
              blockId = blockData.id || (blockType + '-block-' + (++additionalBlockCounter));
            } else if (blockType === 'recovery') {
              blockId = blockData.id || (blockType + '-block-' + (++recoveryBlockCounter));
            } else if (blockType === 'resilience') {
              blockId = blockData.id || (blockType + '-block-' + (++resilienceBlockCounter));
            }
            
            const block = {
              id: blockId,
              type: 'iframe',
              title: blockData.title || '',
              url: blockData.url || '',
              width: blockData.width || '100%',
              height: blockData.height || '600'
            };
            
            blocksArray.push(block);
            renderContentIframeBlock(block, blockType, containerSelector);
          }
        });
        
        // Update counter to avoid conflicts
        if (blockType === 'impact') {
          impactBlockCounter = Math.max(impactBlockCounter, blocks.length);
        } else if (blockType === 'response') {
          responseBlockCounter = Math.max(responseBlockCounter, blocks.length);
        } else if (blockType === 'additional') {
          additionalBlockCounter = Math.max(additionalBlockCounter, blocks.length);
        } else if (blockType === 'recovery') {
          recoveryBlockCounter = Math.max(recoveryBlockCounter, blocks.length);
        } else if (blockType === 'resilience') {
          resilienceBlockCounter = Math.max(resilienceBlockCounter, blocks.length);
        }
        
      } catch (e) {
        console.warn(`Error parsing ${blockType} blocks metadata, falling back to HTML content:`, e);
        loadFromHTMLContentFallback(blockType, blocksArray, containerSelector, fallbackFieldSelector);
      }
    } else {
      // Fallback to existing HTML content
      loadFromHTMLContentFallback(blockType, blocksArray, containerSelector, fallbackFieldSelector);
    }
  }
  
  // Fallback function to load from HTML content (legacy behavior)
  function loadFromHTMLContentFallback(blockType, blocksArray, containerSelector, fallbackFieldSelector) {
    const existingContent = $(fallbackFieldSelector).val();
    if (existingContent && existingContent.trim()) {
      // Create a single text block with existing content
      if (blockType === 'impact') {
        addImpactTextBlock(existingContent);
      } else if (blockType === 'response') {
        addResponseTextBlock(existingContent);
      } else if (blockType === 'additional') {
        addAdditionalTextBlock(existingContent);
      } else if (blockType === 'recovery') {
        addRecoveryTextBlock(existingContent);
      } else if (blockType === 'resilience') {
        addResilienceTextBlock(existingContent);
      }
    }
  }

  // Impact Assessment Block Functions
  function addImpactTextBlock(content = '') {
    const blockId = 'impact-block-' + (++impactBlockCounter);
    const block = {
      id: blockId,
      type: 'text',
      content: content
    };
    
    impactBlocks.push(block);
    renderContentTextBlock(block, 'impact', '#impact-assessment-content-blocks');
    updateImpactBlocksDisplay();
    focusOnNewEditor(blockId, impactQuillEditors);
  }

  function addImpactIframeBlock(iframeData = null) {
    const blockId = 'impact-block-' + (++impactBlockCounter);
    const block = {
      id: blockId,
      type: 'iframe',
      url: '',
      width: '100%',
      height: '600',
      title: 'Interactive Content',
      ...iframeData
    };
    
    impactBlocks.push(block);
    renderContentIframeBlock(block, 'impact', '#impact-assessment-content-blocks');
    updateImpactBlocksDisplay();
  }
  
  // Response Activities Block Functions
  function addResponseTextBlock(content = '') {
    const blockId = 'response-block-' + (++responseBlockCounter);
    const block = {
      id: blockId,
      type: 'text',
      content: content
    };
    
    responseBlocks.push(block);
    renderContentTextBlock(block, 'response', '#response-activities-content-blocks');
    updateResponseBlocksDisplay();
    focusOnNewEditor(blockId, responseQuillEditors);
  }

  function addResponseIframeBlock(iframeData = null) {
    const blockId = 'response-block-' + (++responseBlockCounter);
    const block = {
      id: blockId,
      type: 'iframe',
      url: '',
      width: '100%',
      height: '600',
      title: 'Interactive Content',
      ...iframeData
    };
    
    responseBlocks.push(block);
    renderContentIframeBlock(block, 'response', '#response-activities-content-blocks');
    updateResponseBlocksDisplay();
  }
  
  // Additional Information Block Functions
  function addAdditionalTextBlock(content = '') {
    const blockId = 'additional-block-' + (++additionalBlockCounter);
    const block = {
      id: blockId,
      type: 'text',
      content: content
    };

    additionalBlocks.push(block);
    renderContentTextBlock(block, 'additional', '#additional-information-content-blocks');
    updateAdditionalBlocksDisplay();
    focusOnNewEditor(blockId, additionalQuillEditors);
  }

  function addAdditionalIframeBlock(iframeData = null) {
    const blockId = 'additional-block-' + (++additionalBlockCounter);
    const block = {
      id: blockId,
      type: 'iframe',
      url: '',
      width: '100%',
      height: '600',
      title: 'Interactive Content',
      ...iframeData
    };

    additionalBlocks.push(block);
    renderContentIframeBlock(block, 'additional', '#additional-information-content-blocks');
    updateAdditionalBlocksDisplay();
  }

  // Recovery Phase Block Functions
  function addRecoveryTextBlock(content = '') {
    const blockId = 'recovery-block-' + (++recoveryBlockCounter);
    const block = {
      id: blockId,
      type: 'text',
      content: content
    };

    recoveryBlocks.push(block);
    renderContentTextBlock(block, 'recovery', '#recovery-phase-content-blocks');
    updateRecoveryBlocksDisplay();
    focusOnNewEditor(blockId, recoveryQuillEditors);
  }

  function addRecoveryIframeBlock(iframeData = null) {
    const blockId = 'recovery-block-' + (++recoveryBlockCounter);
    const block = {
      id: blockId,
      type: 'iframe',
      url: '',
      width: '100%',
      height: '600',
      title: 'Interactive Content',
      ...iframeData
    };

    recoveryBlocks.push(block);
    renderContentIframeBlock(block, 'recovery', '#recovery-phase-content-blocks');
    updateRecoveryBlocksDisplay();
  }

  // Resilience Phase Block Functions
  function addResilienceTextBlock(content = '') {
    const blockId = 'resilience-block-' + (++resilienceBlockCounter);
    const block = {
      id: blockId,
      type: 'text',
      content: content
    };

    resilienceBlocks.push(block);
    renderContentTextBlock(block, 'resilience', '#resilience-phase-content-blocks');
    updateResilienceBlocksDisplay();
    focusOnNewEditor(blockId, resilienceQuillEditors);
  }

  function addResilienceIframeBlock(iframeData = null) {
    const blockId = 'resilience-block-' + (++resilienceBlockCounter);
    const block = {
      id: blockId,
      type: 'iframe',
      url: '',
      width: '100%',
      height: '600',
      title: 'Interactive Content',
      ...iframeData
    };

    resilienceBlocks.push(block);
    renderContentIframeBlock(block, 'resilience', '#resilience-phase-content-blocks');
    updateResilienceBlocksDisplay();
  }

  // Helper function to focus on new editor
  function focusOnNewEditor(blockId, editorsObject) {
    setTimeout(function() {
      const quill = editorsObject[blockId + '-editor'];
      if (quill) {
        quill.focus();
      }
    }, 100);
  }

  // Generic function to render text blocks
  function renderContentTextBlock(block, blockType, containerSelector) {
    const html = `
      <div class="content-block" data-block-id="${block.id}">
        <div class="content-block-header">
          <h5 class="content-block-title">
            <i class="fa fa-text-width"></i>
            Text Content
          </h5>
          <div class="content-block-controls">
            <button type="button" class="btn btn-sm btn-default move-up" title="Move Up">
              <i class="fa fa-chevron-up"></i>
            </button>
            <button type="button" class="btn btn-sm btn-default move-down" title="Move Down">
              <i class="fa fa-chevron-down"></i>
            </button>
            <button type="button" class="btn btn-sm btn-danger delete-block" title="Delete">
              <i class="fa fa-trash"></i>
            </button>
          </div>
        </div>
        <div class="content-block-body">
          <div class="text-block-editor" id="${block.id}-editor"></div>
        </div>
      </div>
    `;
    
    $(containerSelector).append(html);
    
    // Initialize Quill editor for this block
    initializeBlockTextEditor(block, blockType);
    
    // Add event listeners
    addBlockEventListeners(block.id, blockType);
  }

  // Generic function to render iframe blocks
  function renderContentIframeBlock(block, blockType, containerSelector) {
    const html = `
      <div class="content-block" data-block-id="${block.id}">
        <div class="content-block-header">
          <h5 class="content-block-title">
            <i class="fa fa-map"></i>
            Interactive Content (Maps, Videos, etc.)
          </h5>
          <div class="content-block-controls">
            <button type="button" class="btn btn-sm btn-default move-up" title="Move Up">
              <i class="fa fa-chevron-up"></i>
            </button>
            <button type="button" class="btn btn-sm btn-default move-down" title="Move Down">
              <i class="fa fa-chevron-down"></i>
            </button>
            <button type="button" class="btn btn-sm btn-danger delete-block" title="Delete">
              <i class="fa fa-trash"></i>
            </button>
          </div>
        </div>
        <div class="content-block-body">
          <div class="iframe-block-form">
            <div class="form-group">
              <label>Title</label>
              <input type="text" class="form-control iframe-title" value="${escapeHtml(block.title)}" placeholder="Enter a title for this content">
            </div>
            <div class="form-group">
              <label>Content URL or Embed Code</label>
              <textarea class="form-control iframe-url" rows="3" placeholder="Enter iframe URL, YouTube URL, or paste embed code (iframe/embed tags)">${escapeHtml(block.url)}</textarea>
              <small class="form-text text-muted">
                Examples:<br>
                • Map: https://ihp-wins.unesco.org/terria/#share/abc123<br>
                • YouTube: https://www.youtube.com/watch?v=VIDEO_ID<br>
                • Embed code: &lt;iframe src="..." &gt;&lt;/iframe&gt;
              </small>
            </div>
            <div class="row">
              <div class="col-sm-6">
                <div class="form-group">
                  <label>Width</label>
                  <input type="text" class="form-control iframe-width" value="${block.width}" placeholder="100%">
                </div>
              </div>
              <div class="col-sm-6">
                <div class="form-group">
                  <label>Height (px)</label>
                  <input type="number" class="form-control iframe-height" value="${block.height}" placeholder="600">
                </div>
              </div>
            </div>
            <div class="form-group">
              <button type="button" class="btn btn-sm btn-info preview-iframe">
                <i class="fa fa-eye"></i> Preview
              </button>
            </div>
            <div class="iframe-preview" style="display: none;">
              <!-- Preview will be inserted here -->
            </div>
          </div>
        </div>
      </div>
    `;
    
    $(containerSelector).append(html);
    
    // Add event listeners
    addIframeBlockEventListeners(block.id, blockType);
    addBlockEventListeners(block.id, blockType);
  }

  function initializeBlockTextEditor(block, blockType) {
    const editorId = block.id + '-editor';
    const editorEl = document.getElementById(editorId);
    
    if (!editorEl) return;
    
    // Wait for Quill to be available
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
      
      const quill = new Quill('#' + editorId, {
        theme: 'snow',
        modules: modulesConfig,
        placeholder: 'Enter your text content here...'
      });
      
      // Set initial content
      if (block.content) {
        quill.clipboard.dangerouslyPasteHTML(block.content);
      }
      
      // Update block data on change based on block type
      quill.on('text-change', function() {
        block.content = quill.root.innerHTML;
        if (blockType === 'impact') {
          updateImpactContentField();
        } else if (blockType === 'response') {
          updateResponseContentField();
        } else if (blockType === 'additional') {
          updateAdditionalContentField();
        } else if (blockType === 'recovery') {
          updateRecoveryContentField();
        } else if (blockType === 'resilience') {
          updateResilienceContentField();
        }
      });

      // Store in appropriate editors object
      if (blockType === 'impact') {
        impactQuillEditors[editorId] = quill;
      } else if (blockType === 'response') {
        responseQuillEditors[editorId] = quill;
      } else if (blockType === 'additional') {
        additionalQuillEditors[editorId] = quill;
      } else if (blockType === 'recovery') {
        recoveryQuillEditors[editorId] = quill;
      } else if (blockType === 'resilience') {
        resilienceQuillEditors[editorId] = quill;
      }
    });
  }

  function addBlockEventListeners(blockId, blockType) {
    const blockEl = $(`[data-block-id="${blockId}"]`);
    
    // Move up
    blockEl.find('.move-up').on('click', function() {
      moveBlock(blockId, 'up', blockType);
    });
    
    // Move down
    blockEl.find('.move-down').on('click', function() {
      moveBlock(blockId, 'down', blockType);
    });
    
    // Delete
    blockEl.find('.delete-block').on('click', function() {
      if (confirm('Are you sure you want to delete this block?')) {
        deleteBlock(blockId, blockType);
      }
    });
  }

  function addIframeBlockEventListeners(blockId, blockType) {
    const blockEl = $(`[data-block-id="${blockId}"]`);
    
    // Find block in appropriate array
    let block, blocksArray;
    if (blockType === 'impact') {
      blocksArray = impactBlocks;
    } else if (blockType === 'response') {
      blocksArray = responseBlocks;
    } else if (blockType === 'additional') {
      blocksArray = additionalBlocks;
    } else if (blockType === 'recovery') {
      blocksArray = recoveryBlocks;
    } else if (blockType === 'resilience') {
      blocksArray = resilienceBlocks;
    }

    block = blocksArray.find(b => b.id === blockId);
    if (!block) return;
    
    // Form inputs
    blockEl.find('.iframe-title').on('input', function() {
      block.title = $(this).val();
      updateContentFieldByType(blockType);
    });
    
    blockEl.find('.iframe-url').on('input', function() {
      block.url = $(this).val();
      updateContentFieldByType(blockType);
    });
    
    blockEl.find('.iframe-width').on('input', function() {
      block.width = $(this).val();
      updateContentFieldByType(blockType);
    });
    
    blockEl.find('.iframe-height').on('input', function() {
      block.height = $(this).val();
      updateContentFieldByType(blockType);
    });
    
    // Preview button
    blockEl.find('.preview-iframe').on('click', function() {
      const previewEl = blockEl.find('.iframe-preview');
      if (previewEl.is(':visible')) {
        previewEl.hide();
      } else {
        if (block.url) {
          const processedContent = processContentForEmbed(block.url, '100%', '300');
          previewEl.html(processedContent).show();
        } else {
          alert('Please enter a URL or embed code first');
        }
      }
    });
  }

  // Process content for embed - handles YouTube URLs, direct embeds, and regular URLs
  function processContentForEmbed(content, width = '100%', height = '600') {
    if (!content || !content.trim()) return '';
    
    content = content.trim();
    
    // Check if it's already an embed code (contains iframe or embed tags)
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

  function moveBlock(blockId, direction, blockType) {
    let blocksArray, containerSelector;

    if (blockType === 'impact') {
      blocksArray = impactBlocks;
      containerSelector = '#impact-assessment-content-blocks';
    } else if (blockType === 'response') {
      blocksArray = responseBlocks;
      containerSelector = '#response-activities-content-blocks';
    } else if (blockType === 'additional') {
      blocksArray = additionalBlocks;
      containerSelector = '#additional-information-content-blocks';
    } else if (blockType === 'recovery') {
      blocksArray = recoveryBlocks;
      containerSelector = '#recovery-phase-content-blocks';
    } else if (blockType === 'resilience') {
      blocksArray = resilienceBlocks;
      containerSelector = '#resilience-phase-content-blocks';
    }

    const blockIndex = blocksArray.findIndex(b => b.id === blockId);
    if (blockIndex === -1) return;
    
    const newIndex = direction === 'up' ? blockIndex - 1 : blockIndex + 1;
    if (newIndex < 0 || newIndex >= blocksArray.length) return;
    
    // Swap blocks
    [blocksArray[blockIndex], blocksArray[newIndex]] = [blocksArray[newIndex], blocksArray[blockIndex]];
    
    // Re-render all blocks
    renderAllBlocks(blockType, containerSelector);
    updateContentFieldByType(blockType);
  }

  function deleteBlock(blockId, blockType) {
    let blocksArray, editorsObject;

    if (blockType === 'impact') {
      blocksArray = impactBlocks;
      editorsObject = impactQuillEditors;
    } else if (blockType === 'response') {
      blocksArray = responseBlocks;
      editorsObject = responseQuillEditors;
    } else if (blockType === 'additional') {
      blocksArray = additionalBlocks;
      editorsObject = additionalQuillEditors;
    } else if (blockType === 'recovery') {
      blocksArray = recoveryBlocks;
      editorsObject = recoveryQuillEditors;
    } else if (blockType === 'resilience') {
      blocksArray = resilienceBlocks;
      editorsObject = resilienceQuillEditors;
    }

    // Remove from array
    const blockIndex = blocksArray.findIndex(b => b.id === blockId);
    if (blockIndex !== -1) {
      blocksArray.splice(blockIndex, 1);
    }
    
    // Remove from DOM
    $(`[data-block-id="${blockId}"]`).remove();
    
    // Clean up editor
    const editorId = blockId + '-editor';
    if (editorsObject[editorId]) {
      delete editorsObject[editorId];
    }
    
    updateBlocksDisplayByType(blockType);
    updateContentFieldByType(blockType);
  }

  function renderAllBlocks(blockType, containerSelector) {
    let blocksArray;

    if (blockType === 'impact') {
      blocksArray = impactBlocks;
    } else if (blockType === 'response') {
      blocksArray = responseBlocks;
    } else if (blockType === 'additional') {
      blocksArray = additionalBlocks;
    } else if (blockType === 'recovery') {
      blocksArray = recoveryBlocks;
    } else if (blockType === 'resilience') {
      blocksArray = resilienceBlocks;
    }

    $(containerSelector).empty();
    blocksArray.forEach(block => {
      if (block.type === 'text') {
        renderContentTextBlock(block, blockType, containerSelector);
      } else if (block.type === 'iframe') {
        renderContentIframeBlock(block, blockType, containerSelector);
      }
    });
  }

  // Individual display update functions
  function updateImpactBlocksDisplay() {
    updateBlocksDisplayByType('impact', impactBlocks, '#impact-assessment-content-blocks');
  }
  
  function updateResponseBlocksDisplay() {
    updateBlocksDisplayByType('response', responseBlocks, '#response-activities-content-blocks');
  }
  
  function updateAdditionalBlocksDisplay() {
    updateBlocksDisplayByType('additional', additionalBlocks, '#additional-information-content-blocks');
  }

  function updateRecoveryBlocksDisplay() {
    updateBlocksDisplayByType('recovery', recoveryBlocks, '#recovery-phase-content-blocks');
  }

  function updateResilienceBlocksDisplay() {
    updateBlocksDisplayByType('resilience', resilienceBlocks, '#resilience-phase-content-blocks');
  }

  function updateBlocksDisplayByType(blockType, blocksArray, containerSelector) {
    if (!blocksArray || !containerSelector) {
      const typeMap = {
        impact:     [impactBlocks,     '#impact-assessment-content-blocks'],
        response:   [responseBlocks,   '#response-activities-content-blocks'],
        additional: [additionalBlocks, '#additional-information-content-blocks'],
        recovery:   [recoveryBlocks,   '#recovery-phase-content-blocks'],
        resilience: [resilienceBlocks, '#resilience-phase-content-blocks']
      };
      if (!typeMap[blockType]) return;
      blocksArray = blocksArray || typeMap[blockType][0];
      containerSelector = containerSelector || typeMap[blockType][1];
    }
    const container = $(containerSelector);
    if (blocksArray.length === 0) {
      const emptyClass = blockType + '-blocks-empty';
      if (!container.find('.' + emptyClass).length) {
        container.append(`<div class="${emptyClass}">No content blocks yet. Use the buttons below to add text or iframe blocks.</div>`);
      }
    } else {
      container.find('.' + blockType + '-blocks-empty').remove();
    }
  }

  // Individual content field update functions
  function updateImpactContentField() {
    updateContentField(impactBlocks, '#field-impact-assessment', '#impact-assessment-blocks-metadata');
  }
  
  function updateResponseContentField() {
    updateContentField(responseBlocks, '#field-response-activities', '#response-activities-blocks-metadata');
  }
  
  function updateAdditionalContentField() {
    updateContentField(additionalBlocks, '#field-map-stories', '#additional-info-blocks-metadata');
  }

  function updateRecoveryContentField() {
    updateContentField(recoveryBlocks, '#field-recovery-phase', '#recovery-phase-blocks-metadata');
  }

  function updateResilienceContentField() {
    updateContentField(resilienceBlocks, '#field-resilience-phase', '#resilience-phase-blocks-metadata');
  }

  function updateContentFieldByType(blockType) {
    if (blockType === 'impact') {
      updateImpactContentField();
    } else if (blockType === 'response') {
      updateResponseContentField();
    } else if (blockType === 'additional') {
      updateAdditionalContentField();
    } else if (blockType === 'recovery') {
      updateRecoveryContentField();
    } else if (blockType === 'resilience') {
      updateResilienceContentField();
    }
  }
  
  function updateContentField(blocksArray, contentFieldSelector, metadataFieldSelector) {
    let finalContent = '';
    
    // Generate HTML content for display
    blocksArray.forEach((block, index) => {
      if (block.type === 'text' && block.content && block.content.trim()) {
        finalContent += block.content;
        if (index < blocksArray.length - 1) {
          finalContent += '\n\n';
        }
      } else if (block.type === 'iframe' && block.url) {
        const height = block.height || '600';
        const width = block.width || '100%';
        
        if (block.title && block.title.trim()) {
          finalContent += `<h3>${escapeHtml(block.title)}</h3>\n`;
        }
        
        finalContent += processContentForEmbed(block.url, width, height);
        
        if (index < blocksArray.length - 1) {
          finalContent += '\n\n';
        }
      }
    });
    
    // Save final HTML content
    $(contentFieldSelector).val(finalContent);
    
    // Save blocks metadata for future editing
    const blocksMetadata = blocksArray.map(block => ({
      id: block.id,
      type: block.type,
      content: block.content,
      title: block.title,
      url: block.url,
      width: block.width,
      height: block.height
    }));
    
    $(metadataFieldSelector).val(JSON.stringify(blocksMetadata));
  }

  // Initialize all systems
  loadTimelineEvents();
  loadUploadedImages();
  loadCountries();
  
  // Initialize Key Information structured fields
  loadExistingCustomFields();
  updateKeyInfoData();
  
  // Initialize Modular Block Systems
  initializeImpactAssessmentBlocks();
  initializeResponseActivitiesBlocks();
  initializeRecoveryPhaseBlocks();
  initializeResiliencePhaseBlocks();
  initializeAdditionalInformationBlocks();

  // Update form submission to handle all block systems
  $('#rapid-response-form').on('submit', function(e) {
    // Update block content fields first
    updateImpactContentField();
    updateResponseContentField();
    updateRecoveryContentField();
    updateResilienceContentField();
    updateAdditionalContentField();
    
    // Sync Quill editors before validation
    if (window.syncAllQuillEditors) { 
      window.syncAllQuillEditors(); 
    }
    
    // Perform validation
    var title = $('#field-title').val().trim();
    var name = $('#field-name').val().trim();
    
    if (!title) {
      alert('Please enter a disaster title');
      $('#field-title').focus();
      e.preventDefault();
      return false;
    }
    
    if (!name) {
      alert('Please enter a name');
      $('#field-name').focus();
      e.preventDefault();
      return false;
    }
    
    // Validate required content (Event Description)
    if (window.quillEditors && window.quillEditors['content-editor']) {
      var contentText = window.quillEditors['content-editor'].getText().trim();
      if (!contentText) {
        alert('Please enter the event description');
        try { 
          window.quillEditors['content-editor'].focus(); 
        } catch (err) {}
        e.preventDefault();
        return false;
      }
    }
    
    // Update data before submit
    updateTimelineData();
    updateUploadedImagesData();
    updateCountriesData();
    
    return true;
  });
  
  // Initialize generated HTML code toggle functionality for all block systems
  $('#toggle-generated-code').on('click', function() {
    var $button = $(this);
    var $container = $('#generated-code-container');
    var $display = $('#generated-code-display');
    var $icon = $button.find('i');
    
    if ($container.is(':visible')) {
      // Hide code
      $container.slideUp(300);
      $button.text(' Show Generated HTML Code');
      $icon.removeClass('fa-eye-slash').addClass('fa-code');
      $button.prepend($icon);
    } else {
      // Show code - get current content from textarea
      var generatedCode = $('#field-map-stories').val() || '';
      
      // Format the code for display
      if (generatedCode.trim()) {
        // Clean up the HTML formatting for better readability
        try {
          // Simple formatting - add line breaks and indentation
          var formattedCode = generatedCode
            .replace(/></g, '>\n<')
            .replace(/^\s+|\s+$/g, '')
            .split('\n')
            .map(function(line, index) {
              // Simple indentation based on nesting level
              var indent = '';
              var openTags = (line.match(/</g) || []).length;
              var closeTags = (line.match(/>/g) || []).length;
              if (line.indexOf('</') === -1 && openTags > 0) {
                indent = '  '.repeat(Math.max(0, index % 4));
              }
              return indent + line.trim();
            })
            .join('\n');
          
          $display.text(formattedCode);
        } catch (e) {
          $display.text(generatedCode);
        }
      } else {
        $display.text('No content has been generated yet. Add some content blocks above and they will be converted to HTML.');
      }
      
      $container.slideDown(300);
      $button.text(' Hide Generated HTML Code');
      $icon.removeClass('fa-code').addClass('fa-eye-slash');
      $button.prepend($icon);
    }
  });
  
  // Initialize toggle functionality for Impact Assessment blocks
  $('#toggle-impact-generated-code').on('click', function() {
    var $button = $(this);
    var $container = $('#impact-generated-code-container');
    var $display = $('#impact-generated-code-display');
    var $icon = $button.find('i');
    
    if ($container.is(':visible')) {
      $container.slideUp(300);
      $button.text(' Show Generated HTML Code');
      $icon.removeClass('fa-eye-slash').addClass('fa-code');
      $button.prepend($icon);
    } else {
      var generatedCode = $('#field-impact-assessment').val() || '';
      if (generatedCode.trim()) {
        $display.text(generatedCode);
      } else {
        $display.text('No content has been generated yet. Add some content blocks above and they will be converted to HTML.');
      }
      $container.slideDown(300);
      $button.text(' Hide Generated HTML Code');
      $icon.removeClass('fa-code').addClass('fa-eye-slash');
      $button.prepend($icon);
    }
  });
  
  // Initialize toggle functionality for Response Activities blocks
  $('#toggle-response-generated-code').on('click', function() {
    var $button = $(this);
    var $container = $('#response-generated-code-container');
    var $display = $('#response-generated-code-display');
    var $icon = $button.find('i');
    
    if ($container.is(':visible')) {
      $container.slideUp(300);
      $button.text(' Show Generated HTML Code');
      $icon.removeClass('fa-eye-slash').addClass('fa-code');
      $button.prepend($icon);
    } else {
      var generatedCode = $('#field-response-activities').val() || '';
      if (generatedCode.trim()) {
        $display.text(generatedCode);
      } else {
        $display.text('No content has been generated yet. Add some content blocks above and they will be converted to HTML.');
      }
      $container.slideDown(300);
      $button.text(' Hide Generated HTML Code');
      $icon.removeClass('fa-code').addClass('fa-eye-slash');
      $button.prepend($icon);
    }
  });
  
  // Initialize toggle functionality for Recovery Phase blocks
  $('#toggle-recovery-generated-code').on('click', function() {
    var $button = $(this);
    var $container = $('#recovery-generated-code-container');
    var $display = $('#recovery-generated-code-display');
    var $icon = $button.find('i');
    
    if ($container.is(':visible')) {
      $container.slideUp(300);
      $button.text(' Show Generated HTML Code');
      $icon.removeClass('fa-eye-slash').addClass('fa-code');
      $button.prepend($icon);
    } else {
      var generatedCode = $('#field-recovery-phase').val() || '';
      if (generatedCode.trim()) {
        $display.text(generatedCode);
      } else {
        $display.text('No content has been generated yet. Add some content blocks above and they will be converted to HTML.');
      }
      $container.slideDown(300);
      $button.text(' Hide Generated HTML Code');
      $icon.removeClass('fa-code').addClass('fa-eye-slash');
      $button.prepend($icon);
    }
  });
  
  // Initialize toggle functionality for Resilience Phase blocks
  $('#toggle-resilience-generated-code').on('click', function() {
    var $button = $(this);
    var $container = $('#resilience-generated-code-container');
    var $display = $('#resilience-generated-code-display');
    var $icon = $button.find('i');
    
    if ($container.is(':visible')) {
      $container.slideUp(300);
      $button.text(' Show Generated HTML Code');
      $icon.removeClass('fa-eye-slash').addClass('fa-code');
      $button.prepend($icon);
    } else {
      var generatedCode = $('#field-resilience-phase').val() || '';
      if (generatedCode.trim()) {
        $display.text(generatedCode);
      } else {
        $display.text('No content has been generated yet. Add some content blocks above and they will be converted to HTML.');
      }
      $container.slideDown(300);
      $button.text(' Hide Generated HTML Code');
      $icon.removeClass('fa-code').addClass('fa-eye-slash');
      $button.prepend($icon);
    }
  });
  
  // Load Quill and editors
  waitForQuill(initializeQuillEditors);
  
  }); // Close document.ready
  }); // Close waitForJQuery function
})(); // Close main function