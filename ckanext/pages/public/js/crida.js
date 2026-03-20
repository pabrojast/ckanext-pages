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
      try {
        this.initMap();
      } catch (e) {
        console.error('CRIDA: Map initialization failed:', e);
      }
      this.bindFilterEvents();
      this.bindCardHoverEvents();
      this.bindLoadMore();
    },

    initAnimatedCounters: function() {
      if (window.CRIDA_Counters) {
        window.CRIDA_Counters.initAnimatedCounters();
      }
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
                  (props.status || 'default').toLowerCase() + '">' +
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

      $('#crida-filter-country, #crida-filter-theme, #crida-filter-status, #crida-filter-sector, #crida-filter-solution, #crida-filter-challenge, #crida-filter-region, #crida-filter-scale, #crida-filter-stage').on('change', function() {
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
        $('#crida-filter-sector').val('');
        $('#crida-filter-solution').val('');
        $('#crida-filter-challenge').val('');
        $('#crida-filter-region').val('');
        $('#crida-filter-scale').val('');
        $('#crida-filter-stage').val('');
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
      var sector = ($('#crida-filter-sector').val() || '').toLowerCase();
      var solution = ($('#crida-filter-solution').val() || '').toLowerCase();
      var challenge = ($('#crida-filter-challenge').val() || '').toLowerCase();
      var region = ($('#crida-filter-region').val() || '').toLowerCase();
      var scale = ($('#crida-filter-scale').val() || '').toLowerCase();
      var stage = ($('#crida-filter-stage').val() || '').toLowerCase();

      var visibleCount = 0;

      $('.crida-card').each(function() {
        var $card = $(this);
        var cardCountry = ($card.data('country') || '').toString().toLowerCase();
        var cardThemes = ($card.data('themes') || '').toString().toLowerCase();
        var cardStatus = ($card.data('status') || '').toString().toLowerCase();
        var cardTitle = ($card.data('title') || '').toString().toLowerCase();
        var cardSector = ($card.data('sector') || '').toString().toLowerCase();
        var cardSolution = ($card.data('solution') || '').toString().toLowerCase();
        var cardChallenge = ($card.data('challenge') || '').toString().toLowerCase();
        var cardRegion = ($card.data('region') || '').toString().toLowerCase();
        var cardScale = ($card.data('scale') || '').toString().toLowerCase();
        var cardStage = ($card.data('stage') || '').toString().toLowerCase();

        var show = true;

        if (country && cardCountry.indexOf(country) === -1) show = false;
        if (theme && cardThemes.indexOf(theme) === -1) show = false;
        if (status && cardStatus !== status) show = false;
        if (search && cardTitle.indexOf(search) === -1 && cardCountry.indexOf(search) === -1) show = false;
        if (sector && cardSector.indexOf(sector) === -1) show = false;
        if (solution && cardSolution.indexOf(solution) === -1) show = false;
        if (challenge && cardChallenge.indexOf(challenge) === -1) show = false;
        if (region && cardRegion.indexOf(region) === -1) show = false;
        if (scale && cardScale.indexOf(scale) === -1) show = false;
        if (stage && cardStage.indexOf(stage) === -1) show = false;

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

      $(document).on('mouseenter', '.crida-card', function() {
        var name = $(this).data('name');
        if (!name || !self.markers.length) return;

        self.markers.forEach(function(m) {
          var url = m.feature.properties.url || '';
          if (url.indexOf(name) !== -1) {
            m.marker.setStyle({ radius: 12, weight: 3, fillOpacity: 1 });
          }
        });
      }).on('mouseleave', '.crida-card', function() {
        self.markers.forEach(function(m) {
          m.marker.setStyle({ radius: 8, weight: 2, fillOpacity: 0.85 });
        });
      });
    },

    /**
     * Build a card HTML string from a case study object returned by the API.
     */
    buildCardHtml: function(cs) {
      var themes = cs.themes || [];
      var statusClass = 'crida-status-' + (cs.crida_status || 'default').toLowerCase().replace(/\s+/g, '-');
      var summary = cs.excerpt || (cs.content ? cs.content.substring(0, 180) : '');

      var imageHtml;
      if (cs.header_image) {
        imageHtml = '<img src="' + cs.header_image + '" alt="' + (cs.title || '') + '" loading="lazy">';
      } else {
        imageHtml = '<div class="crida-card-placeholder"><i class="fa fa-map-marker"></i></div>';
      }

      var themeTags = '';
      for (var i = 0; i < Math.min(themes.length, 3); i++) {
        themeTags += '<span class="crida-theme-tag"><i class="fa fa-tag"></i> ' + themes[i] + '</span>';
      }

      return '<div class="crida-card" data-name="' + (cs.name || '') + '"' +
        ' data-country="' + (cs.country || '') + '"' +
        ' data-status="' + (cs.crida_status || '') + '"' +
        ' data-themes="' + themes.join(',') + '"' +
        ' data-title="' + (cs.title || '') + '" style="opacity:0;transform:translateY(20px);transition:opacity 0.4s,transform 0.4s;">' +
        '<div class="crida-card-image">' + imageHtml + '</div>' +
        '<div class="crida-card-body">' +
          '<div class="crida-card-header">' +
            '<span class="crida-card-country"><i class="fa fa-globe"></i> ' + (cs.country || '') + '</span>' +
            '<span class="crida-status-badge ' + statusClass + '">' + (cs.crida_status || 'N/A') + '</span>' +
          '</div>' +
          '<h3><a href="' + cs.url + '">' + (cs.title || '') + '</a></h3>' +
          '<p class="crida-card-summary">' + summary + '</p>' +
          '<div class="crida-card-footer">' +
            '<div class="crida-card-themes">' + themeTags + '</div>' +
            '<a href="' + cs.url + '" class="crida-btn-outline" style="padding:0.3rem 0.8rem;font-size:0.78rem;">' +
              'View <i class="fa fa-arrow-right"></i>' +
            '</a>' +
          '</div>' +
        '</div>' +
      '</div>';
    },

    /**
     * Bind "Load More" button click to fetch additional case studies via AJAX.
     */
    bindLoadMore: function() {
      var self = this;
      var $btn = $('#crida-load-more');
      if (!$btn.length) return;

      $btn.on('click', function(e) {
        e.preventDefault();
        var offset = parseInt($btn.data('offset'), 10) || 0;
        var total = parseInt($btn.data('total'), 10) || 0;
        var apiUrl = $btn.data('api-url');
        var limit = 6;

        $btn.prop('disabled', true);
        $('#crida-load-more-spinner').show();

        $.ajax({
          url: apiUrl,
          data: { offset: offset, limit: limit },
          dataType: 'json',
          success: function(data) {
            var $grid = $('#crida-case-studies-grid');
            var newCards = [];

            (data.results || []).forEach(function(cs) {
              var cardHtml = self.buildCardHtml(cs);
              var $card = $(cardHtml);
              $grid.append($card);
              newCards.push($card);
            });

            // Animate new cards in
            setTimeout(function() {
              newCards.forEach(function($card) {
                $card.css({ opacity: 1, transform: 'translateY(0)' });
              });
            }, 50);

            var newOffset = offset + (data.results || []).length;
            $btn.data('offset', newOffset);

            if (!data.has_more) {
              $('#crida-load-more-wrapper').fadeOut(300);
            } else {
              var remaining = total - newOffset;
              $btn.find('.crida-load-more-count').text('(' + remaining + ' remaining)');
              $btn.prop('disabled', false);
            }
          },
          error: function() {
            $btn.prop('disabled', false);
          },
          complete: function() {
            $('#crida-load-more-spinner').hide();
          }
        });
      });
    },
  };

  $(document).ready(function() {
    if ($('.crida-page').length || $('#crida-map').length) {
      CRIDA.init();
    }
    // Animated counters
    CRIDA.initAnimatedCounters();
  });

})(jQuery);

/* ============================================================
   Animated Counter System (IntersectionObserver + easeOutExpo)
   ============================================================ */
(function() {
  'use strict';

  function easeOutExpo(t) {
    return t === 1 ? 1 : 1 - Math.pow(2, -10 * t);
  }

  function animateCounter(el) {
    var target = parseInt(el.getAttribute('data-target'), 10);
    if (isNaN(target) || target <= 0) {
      el.textContent = '0';
      return;
    }
    var suffix = el.getAttribute('data-suffix') || '';
    var duration = 2000;
    var startTime = null;

    function step(timestamp) {
      if (!startTime) startTime = timestamp;
      var progress = Math.min((timestamp - startTime) / duration, 1);
      var value = Math.floor(easeOutExpo(progress) * target);
      el.textContent = value.toLocaleString() + suffix;
      if (progress < 1) {
        requestAnimationFrame(step);
      } else {
        el.textContent = target.toLocaleString() + suffix;
      }
    }

    el.textContent = '0';
    requestAnimationFrame(step);
  }

  if (typeof window.CRIDA_Counters === 'undefined') {
    window.CRIDA_Counters = {
      initAnimatedCounters: function() {
        var counters = document.querySelectorAll('.crida-stat-number[data-target]');
        if (!counters.length) return;

        if ('IntersectionObserver' in window) {
          var observer = new IntersectionObserver(function(entries) {
            entries.forEach(function(entry) {
              if (entry.isIntersecting && !entry.target.classList.contains('counted')) {
                entry.target.classList.add('counted');
                animateCounter(entry.target);
                observer.unobserve(entry.target);
              }
            });
          }, { threshold: 0.3 });

          counters.forEach(function(el) {
            el.textContent = '0';
            observer.observe(el);
          });
        } else {
          // Fallback: animate all immediately
          counters.forEach(function(el) { animateCounter(el); });
        }
      }
    };
  }

  // Auto-init when DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
      window.CRIDA_Counters.initAnimatedCounters();
    });
  } else {
    window.CRIDA_Counters.initAnimatedCounters();
  }
})();
