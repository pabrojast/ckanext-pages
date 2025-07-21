/**
 * Organization Loader Module
 * Handles loading and managing organization data from API
 */

(function() {
  'use strict';

  const OrganizationLoader = {
    
    init: function() {
      this.loadOrganizations();
    },

    // Get API URL dynamically based on current site
    getApiUrl: function() {
      if (window.OpenSourceSoftwareEdit && window.OpenSourceSoftwareEdit.getSiteApiUrl) {
        return window.OpenSourceSoftwareEdit.getSiteApiUrl();
      }
      
      // Fallback to current domain
      const currentDomain = window.location.hostname;
      const currentPort = window.location.port;
      const protocol = window.location.protocol;
      
      let apiUrl = protocol + '//' + currentDomain;
      if (currentPort && currentPort !== '80' && currentPort !== '443') {
        apiUrl += ':' + currentPort;
      }
      
      return apiUrl + '/api/3/action/';
    },

    // Load organizations from API
    loadOrganizations: function() {
      const self = this;
      const currentOrgId = $('#organization_id').data('current-value') || '';
      const apiUrl = this.getApiUrl();
      
      $.ajax({
        url: apiUrl + 'organization_list',
        data: { all_fields: true },
        dataType: 'json',
        success: function(response) {
          if (response.success && response.result) {
            self.populateOrganizationSelect(response.result, currentOrgId);
          }
        },
        error: function(xhr, status, error) {
          console.error('Error loading organizations:', error);
          $('#organization_id').html('<option value="">Error loading organizations</option>');
        }
      });
    },

    // Populate organization select dropdown
    populateOrganizationSelect: function(organizations, currentOrgId) {
      const $select = $('#organization_id');
      $select.empty();
      $select.append('<option value="">Select Organization</option>');
      
      organizations.forEach(function(org) {
        const selected = org.id === currentOrgId ? 'selected' : '';
        const displayName = org.display_name || org.title || org.name;
        $select.append(
          `<option value="${org.id}" ${selected}>${displayName} - ${org.name}</option>`
        );
      });

      // Trigger change event if there's a pre-selected value
      if (currentOrgId) {
        $select.trigger('change');
      }
    }
  };

  // Expose globally
  window.OrganizationLoader = OrganizationLoader;

})();
