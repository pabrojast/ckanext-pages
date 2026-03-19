/**
 * CRIDA - Climate Risk Informed Decision Analysis
 * Frontend JavaScript for map display and case study interaction
 */

(function($) {
  'use strict';

  var CRIDA = {
    map: null,
    markers: [],
    geojsonData: null,

    init: function() {
      this.initMap();
      this.bindFilterEvents();
      this.bindCardHoverEvents();
    },

    /**
     * Initialize the Leaflet map with GeoJSON case study points.
     */
    initMap: function() {
      var $mapContainer = $('#crida-map');
      if (!$mapContainer.length) return;

      var geojsonStr = $mapContainer.data('geojson');
      if (!geojsonStr) return;

      try {
        this.geojsonData = typeof geojsonStr === 'string'
          ? JSON.parse(geojsonStr)
          : geojsonStr;
      } catch (e) {
        console.error('CRIDA: Failed to parse GeoJSON:', e);
        return;
      }

      // Check if Leaflet is available
      if (typeof L === 'undefined') {
        console.warn('CRIDA: Leaflet not loaded, trying iframe fallback');
        this.initIframeMap($mapContainer);
        return;
      }

      this.map = L.map('crida-map', {
        scrollWheelZoom: false,
        zoomControl: true,
      }).setView([20, 0], 2);

      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap contributors',
        maxZoom: 18,
      }).addTo(this.map);

      this.addGeoJSONLayer(this.geojsonData);
    },

    /**
     * Fallback: render map as an iframe pointing to the GeoJSON API.
     */
    initIframeMap: function($container) {
      var terriaBase = $container.data('terria-base') || '';
      if (!terriaBase) {
        $container.html(
          '<div style="display:flex;align-items:center;justify-content:center;height:100%;' +
          'background:#f0f4f8;color:#666;font-size:0.9rem;">' +
          '<i class="fa fa-map-marker" style="font-size:2rem;margin-right:0.8rem;color:#0072BC;"></i>' +
          'Interactive map — configure Terria base URL to enable</div>'
        );
        return;
      }

      var geojsonUrl = window.location.origin + '/crida/api/geojson';
      var terriaUrl = terriaBase + '#share=' + encodeURIComponent(JSON.stringify({
        initSources: [{
          catalog: [{
            type: 'geojson',
            name: 'CRIDA Case Studies',
            url: geojsonUrl,
          }],
        }],
      }));

      $container.html(
        '<iframe src="' + terriaUrl + '" allow="geolocation" ' +
        'loading="lazy" title="CRIDA Case Studies Map" ' +
        'style="width:100%;height:100%;border:none;"></iframe>'
      );
    },

    /**
     * Add GeoJSON features to the Leaflet map.
     */
    addGeoJSONLayer: function(geojson) {
      var self = this;

      var statusColors = {
        'Finished': '#00A651',
        'Ongoing': '#0072BC',
        'Planned': '#F7941D',
      };

      L.geoJSON(geojson, {
        pointToLayer: function(feature, latlng) {
          var status = feature.properties.status || '';
          var color = statusColors[status] || '#6c757d';

          var marker = L.circleMarker(latlng, {
            radius: 8,
            fillColor: color,
            color: '#fff',
            weight: 2,
            opacity: 1,
            fillOpacity: 0.85,
          });

          self.markers.push({
            marker: marker,
            feature: feature,
          });

          return marker;
        },

        onEachFeature: function(feature, layer) {
          var props = feature.properties;
          var themes = (props.themes || []).map(function(t) {
            return '<span class="crida-theme-tag"><i class="fa fa-tag"></i> ' + t + '</span>';
          }).join(' ');

          var popupHtml =
            '<div class="crida-popup">' +
              '<h4 style="margin:0 0 0.4rem;font-size:0.95rem;">' +
                '<a href="' + (props.url || '#') + '" style="color:#0072BC;">' +
                  (props.title || 'Untitled') +
                '</a>' +
              '</h4>' +
              '<div style="margin-bottom:0.4rem;">' +
                '<span class="crida-status-badge crida-status-' +
                  (status || 'default').toLowerCase() + '">' +
                  (props.status || '') +
                '</span>' +
                ' <span style="color:#666;font-size:0.82rem;">' +
                  '<i class="fa fa-globe"></i> ' + (props.country || '') +
                '</span>' +
              '</div>' +
              (props.summary
                ? '<p style="font-size:0.82rem;color:#555;margin:0 0 0.4rem;line-height:1.4;">' +
                    props.summary.substring(0, 150) +
                    (props.summary.length > 150 ? '...' : '') +
                  '</p>'
                : ''
              ) +
              (themes
                ? '<div style="margin-top:0.4rem;">' + themes + '</div>'
                : ''
              ) +
            '</div>';

          layer.bindPopup(popupHtml, {
            maxWidth: 320,
            className: 'crida-map-popup',
          });
        },
      }).addTo(this.map);

      // Fit bounds if features exist
      if (geojson.features && geojson.features.length > 0) {
        var bounds = L.geoJSON(geojson).getBounds();
        this.map.fitBounds(bounds, { padding: [30, 30], maxZoom: 5 });
      }
    },

    /**
     * Bind filter events for the list page.
     */
    bindFilterEvents: function() {
      var self = this;

      $('#crida-filter-country, #crida-filter-theme, #crida-filter-status').on('change', function() {
        self.applyFilters();
      });

      $('#crida-filter-search').on('keyup', function() {
        clearTimeout(self._searchTimeout);
        self._searchTimeout = setTimeout(function() {
          self.applyFilters();
        }, 300);
      });

      // Clear filters button
      $('#crida-clear-filters').on('click', function(e) {
        e.preventDefault();
        $('#crida-filter-country').val('');
        $('#crida-filter-theme').val('');
        $('#crida-filter-status').val('');
        $('#crida-filter-search').val('');
        self.applyFilters();
      });
    },

    /**
     * Apply filters to the visible cards.
     */
    applyFilters: function() {
      var country = ($('#crida-filter-country').val() || '').toLowerCase();
      var theme = ($('#crida-filter-theme').val() || '').toLowerCase();
      var status = ($('#crida-filter-status').val() || '').toLowerCase();
      var search = ($('#crida-filter-search').val() || '').toLowerCase();

      var visibleCount = 0;

      $('.crida-card').each(function() {
        var $card = $(this);
        var cardCountry = ($card.data('country') || '').toString().toLowerCase();
        var cardThemes = ($card.data('themes') || '').toString().toLowerCase();
        var cardStatus = ($card.data('status') || '').toString().toLowerCase();
        var cardTitle = ($card.data('title') || '').toString().toLowerCase();

        var show = true;

        if (country && cardCountry.indexOf(country) === -1) show = false;
        if (theme && cardThemes.indexOf(theme) === -1) show = false;
        if (status && cardStatus !== status) show = false;
        if (search && cardTitle.indexOf(search) === -1 && cardCountry.indexOf(search) === -1) show = false;

        $card.toggle(show);
        if (show) visibleCount++;
      });

      // Update count
      $('#crida-results-count').text(visibleCount);

      // Show/hide empty state
      if (visibleCount === 0) {
        $('#crida-empty-filter-state').show();
      } else {
        $('#crida-empty-filter-state').hide();
      }
    },

    /**
     * Add hover effects to cards that highlight corresponding map markers.
     */
    bindCardHoverEvents: function() {
      var self = this;

      $('.crida-card').on('mouseenter', function() {
        var name = $(this).data('name');
        if (!name || !self.markers.length) return;

        self.markers.forEach(function(m) {
          var url = m.feature.properties.url || '';
          if (url.indexOf(name) !== -1) {
            m.marker.setStyle({ radius: 12, weight: 3, fillOpacity: 1 });
          }
        });
      }).on('mouseleave', function() {
        self.markers.forEach(function(m) {
          m.marker.setStyle({ radius: 8, weight: 2, fillOpacity: 0.85 });
        });
      });
    },
  };

  $(document).ready(function() {
    if ($('.crida-page').length || $('#crida-map').length) {
      CRIDA.init();
    }
  });

})(jQuery);
