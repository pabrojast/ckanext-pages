/**
 * Initialization script for Open Source Software Edit form
 * Sets up data attributes and initial values from server data
 */

(function() {
  'use strict';

  // Initialize data attributes from server data
  function initializeDataAttributes() {
    // Set organization current value if available
    const organizationField = document.getElementById('organization_id');
    if (organizationField) {
      const currentOrgId = '{{ data.get("organization_id", "") }}';
      if (currentOrgId) {
        organizationField.setAttribute('data-current-value', currentOrgId);
      }
    }

    // Set member states data if available
    const memberStatesData = document.getElementById('member-states-data');
    if (memberStatesData && !memberStatesData.value) {
      const memberStatesFromServer = '{{ data.get("member_states", "[]")|safe }}';
      if (memberStatesFromServer && memberStatesFromServer !== '[]') {
        memberStatesData.value = memberStatesFromServer;
      }
    }

    // Set uploaded images data if available
    const uploadedImagesData = document.getElementById('uploaded-images-data');
    if (uploadedImagesData && !uploadedImagesData.value) {
      const imagesFromServer = '{{ data.get("uploaded_images", "[]")|safe }}';
      if (imagesFromServer && imagesFromServer !== '[]') {
        uploadedImagesData.value = imagesFromServer;
      }
    }

    // Set image gallery data if available
    const imageGalleryData = document.getElementById('image-gallery-data');
    if (imageGalleryData && !imageGalleryData.value) {
      const galleryFromServer = '{{ data.get("image_gallery", "[]")|safe }}';
      if (galleryFromServer && galleryFromServer !== '[]') {
        imageGalleryData.value = galleryFromServer;
      }
    }
  }

  // Initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeDataAttributes);
  } else {
    initializeDataAttributes();
  }

})();
