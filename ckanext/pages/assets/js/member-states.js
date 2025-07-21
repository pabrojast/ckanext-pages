/**
 * Member States Management Module
 * Handles loading and managing member states data
 */

(function() {
  'use strict';

  const MemberStates = {
    selectedMemberStates: [],

    init: function() {
      this.loadMemberStates();
      this.bindEvents();
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

    // Format member state name for display
    formatMemberStateName: function(name) {
      if (!name) return name;
      
      // Replace hyphens with spaces and capitalize each word
      return name
        .split('-')
        .map(word => {
          // Handle special cases for better formatting
          if (['of', 'and', 'the', 'de', 'da', 'du'].includes(word.toLowerCase())) {
            return word.toLowerCase();
          }
          // Capitalize first letter of each word
          return word.charAt(0).toUpperCase() + word.slice(1).toLowerCase();
        })
        .join(' ')
        .replace(/\s+/g, ' ') // Replace multiple spaces with single space
        .trim();
    },

    // Load member states from API
    loadMemberStates: function() {
      const self = this;
      const apiUrl = this.getApiUrl();
      
      $.ajax({
        url: apiUrl + 'group_show',
        data: { 
          id: 'member-states',
          include_groups: true
        },
        dataType: 'json',
        success: function(response) {
          if (response.success && response.result && response.result.groups) {
            self.populateMemberStatesSelect(response.result.groups);
            self.loadExistingMemberStates();
          }
        },
        error: function(xhr, status, error) {
          console.error('Error loading member states:', error);
          $('#member-state-select').html('<option value="">Error loading member states</option>');
        }
      });
    },

    // Populate member states select dropdown
    populateMemberStatesSelect: function(groups) {
      const self = this;
      const $select = $('#member-state-select');
      $select.empty();
      $select.append('<option value="">Select a member state...</option>');
      
      // Process and sort member states alphabetically by formatted display name
      const processedGroups = groups.map(group => {
        const formattedName = self.formatMemberStateName(group.name);
        return {
          ...group,
          formatted_display_name: formattedName
        };
      }).sort((a, b) => 
        a.formatted_display_name.localeCompare(b.formatted_display_name)
      );
      
      processedGroups.forEach(function(group) {
        $select.append(
          `<option value="${group.name}" data-name="${group.name}" data-display="${group.formatted_display_name}">${group.formatted_display_name}</option>`
        );
      });
    },

    // Load existing member states from hidden input
    loadExistingMemberStates: function() {
      const memberStatesData = $('#member-states-data').val();
      if (memberStatesData) {
        try {
          this.selectedMemberStates = JSON.parse(memberStatesData);
          const self = this;
          this.selectedMemberStates.forEach(state => {
            // Ensure display_name is properly formatted
            if (!state.display_name && state.name) {
              state.display_name = self.formatMemberStateName(state.name);
            }
            self.addMemberStateToList(state);
          });
        } catch (e) {
          console.error('Error parsing member states data:', e);
        }
      }
    },

    // Add member state to the visual list
    addMemberStateToList: function(state) {
      const stateId = `member-state-${state.name}`;
      if ($(`#${stateId}`).length) {
        return; // Already added
      }
      
      const stateHtml = `
        <div class="member-state-item" id="${stateId}" data-state-name="${state.name}">
          <span class="member-state-name">${state.display_name}</span>
          <button type="button" class="btn btn-sm btn-danger remove-member-state" data-state-name="${state.name}">
            <i class="fa fa-times"></i>
          </button>
        </div>
      `;
      $('#selected-member-states').append(stateHtml);
    },

    // Update member states hidden input data
    updateMemberStatesData: function() {
      $('#member-states-data').val(JSON.stringify(this.selectedMemberStates));
    },

    // Bind event handlers
    bindEvents: function() {
      const self = this;

      // Handle add member state button
      $('#add-member-state').on('click', function() {
        const $select = $('#member-state-select');
        const selectedOption = $select.find('option:selected');
        const stateName = selectedOption.val();
        
        if (!stateName) {
          return;
        }
        
        // Check if already added
        if (self.selectedMemberStates.find(s => s.name === stateName)) {
          alert('This member state has already been added');
          return;
        }
        
        const state = {
          id: stateName, // Keep id for compatibility
          name: stateName,
          display_name: selectedOption.data('display')
        };
        
        self.selectedMemberStates.push(state);
        self.addMemberStateToList(state);
        self.updateMemberStatesData();
        
        // Reset select
        $select.val('');
      });
      
      // Handle remove member state (using event delegation)
      $(document).on('click', '.remove-member-state', function() {
        const stateName = $(this).data('state-name');
        $(`#member-state-${stateName}`).remove();
        self.selectedMemberStates = self.selectedMemberStates.filter(s => s.name !== stateName);
        self.updateMemberStatesData();
      });
    }
  };

  // Expose globally
  window.MemberStates = MemberStates;

})();
