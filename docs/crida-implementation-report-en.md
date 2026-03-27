# CRIDA Implementation Report

Repository reviewed: `ckanext-pages` snapshot inspected on March 27, 2026.

## Executive Summary

In this repository, CRIDA is implemented as a specialized content vertical inside the generic `ckanext-pages` CKAN extension. It is not a separate service and it does not introduce a dedicated CRIDA database table. Instead, it relies on the shared `Page` model, a dedicated `page_type` value (`crida-case-study`), CKAN actions and auth functions, Flask routes, Jinja templates, JavaScript assets, and a local data seeding pipeline.

The result is a hybrid CMS-plus-catalog feature set. Editors can create case studies, administrators can moderate them, public users can browse and read approved entries, and external consumers can retrieve approved records through JSON and GeoJSON endpoints.

## Core Architecture

CRIDA is distributed across the same extension layers used by the rest of the project:

- `ckanext/pages/blueprint.py` registers the CRIDA routes.
- `ckanext/pages/utils.py` contains most route-facing utility logic for rendering, moderation, reseeding, and HTTP API responses.
- `ckanext/pages/actions.py` defines public CKAN actions for listing, showing, and exporting CRIDA case studies as GeoJSON.
- `ckanext/pages/auth.py` defines the corresponding authorization functions.
- `ckanext/pages/logic/schema.py` validates CRIDA-specific fields.
- `ckanext/pages/plugin.py` registers helpers, actions, auth functions, and CRIDA category metadata used by the UI.
- `ckanext/pages/theme/templates_main/ckanext_pages/` contains the CRIDA templates.
- `ckanext/pages/public/js/` and `ckanext/pages/assets/css/` contain the CRIDA frontend behavior and styling.

From an architectural perspective, CRIDA should be understood as a vertical built on top of the generic pages framework, not as an isolated subsystem.

## Routing and User-Facing Surfaces

The CRIDA routes are registered under the `/crida` prefix. The main entry points observed in the repository are:

- `/crida`: initiative hub page.
- `/crida/case-studies`: case study catalog.
- `/crida/case-studies/<page>`: case study detail page.
- `/crida/case-studies_edit` and `/crida/case-studies_edit/<page>`: create/edit form.
- `/crida/admin`: moderation dashboard.
- `/crida/api/case-studies`: JSON API for case-study cards and filters.
- `/crida/api/geojson`: public GeoJSON API for map consumers.

The hub page is broader than the case-study catalog. It aggregates CKAN group data for the `crida` group, including datasets and members, and it also pulls related water news, events, and publications through shared initiative helpers. This means CRIDA works both as a content collection and as an initiative landing page.

## Data Model and Persistence

CRIDA uses the shared `Page` model declared in `ckanext/pages/db.py`. The base table is `ckanext_pages`, which stores generic page attributes such as title, slug, content, visibility, page type, workflow state, timestamps, and revision history.

The most important point is that CRIDA-specific fields are not modeled as their own relational table. Instead:

- core page workflow fields such as `private`, `submission_status`, `submitted_at`, `reviewed_at`, and `reviewed_by` live as dedicated columns on `ckanext_pages`;
- CRIDA-specific content fields are validated through the pages schema and then serialized into the shared `extras` JSON payload;
- revision history is stored in the `revisions` JSONB column.

Observed CRIDA-specific fields include:

- `latitude`, `longitude`, and `coord_note`
- `crida_status`
- `themes`
- `partners`
- `crida_context`
- `crida_actions`
- `crida_outcomes`
- `highlights`
- `image_credit`
- `case_study_url`
- `external_link`
- `related_datasets_json`
- `related_documents_json`
- classification fields such as `sector`, `crida_stage`, `region`, `scale`, `climate_challenge`, and `solution_type`

On save, `ckanext_pages_update` merges schema-approved extra fields into the `extras` JSON object, preserves pre-existing extras not present in the current form payload, and appends a new revision entry. This gives CRIDA the same persistence and audit behavior as the rest of the extension.

## Seed and Data Enrichment Pipeline

One of the most important implementation features is the seed pipeline in `ckanext/pages/commands/seed_crida.py`.

The command reads and merges several local data sources from `ckanext/pages/data/`:

- `crida_lat_lon`: a geolocated base dataset with 27 case-study entries.
- `crida.json`: a narrative dataset with 18 entries containing fields such as context, actions, and outcomes.
- `crida_enriched.json`: 19 enriched records with scraped or expanded UNESCO content.

The merge strategy is layered:

1. `crida_lat_lon` is loaded first and becomes the base record set.
2. `crida.json` is merged by title using exact matching, explicit aliases, and a fuzzy word-overlap fallback.
3. unmatched `crida.json` titles are converted into new case-study records.
4. `crida_enriched.json` is then applied as the highest-priority enrichment source, replacing summary/context/actions/outcomes when the enriched content is more complete.

The seed script also injects curated metadata from Python dictionaries:

- `COORDINATES` for approximate map positions.
- `IMAGE_MAP` for local header images under `ckanext/pages/public/images/crida/`.
- `CATEGORY_MAP` for sector, CRIDA stage, region, scale, climate challenge, and solution type classifications.

Each seeded record is transformed into a `ckanext_pages_update` payload with:

- `page_type='crida-case-study'`
- summary content mapped into `content` and `excerpt`
- JSON-encoded themes, partners, highlights, and category arrays
- coordinates and coordinate notes
- local image paths
- UNESCO and external reference URLs when present
- a fixed publish date of `2025-01-01`
- `submission_action='publish'`

The command supports `--dry-run` and `--update-existing`. It uses the CKAN site user plus `ignore_auth=True`, which allows bulk import without going through the normal editorial UI.

## Editorial Workflow and Moderation

The intended CRIDA workflow is a classic draft-submit-approve model with direct publish support for administrators.

At the action layer, `ckanext_pages_update` treats `crida-case-study` as part of the same workflow family as other moderated content types. The implemented behavior is:

- `draft`: save as private with `submission_status='draft'`
- `submit`: save as private with `submission_status='pending'` and populate `submitted_at`
- `publish`: save as public with `submission_status='approved'` and populate review metadata

The action layer also protects against privilege escalation: if a non-admin attempts to publish directly, the action logic downgrades the request to `submit`.

Moderation is handled in `ckanext/pages/utils.py` and exposed at `/crida/admin`. The admin dashboard:

- shows pending CRIDA case studies;
- allows explicit approve and reject actions;
- allows a forced reseed from local data files.

Approval makes the page public and marks it as approved. Rejection keeps it private and marks it as rejected so it can be edited and resubmitted later.

## Public Read APIs

CRIDA exposes both CKAN actions and plain HTTP endpoints.

### CKAN Actions

The plugin registers three CRIDA-specific public actions:

- `ckanext_crida_case_study_list`
- `ckanext_crida_case_study_show`
- `ckanext_crida_geojson`

These actions only expose public approved content. Anonymous access is explicitly allowed for the read endpoints in `auth.py`.

`ckanext_crida_case_study_list` supports:

- free-text search (`q`)
- country filtering
- theme filtering
- CRIDA status filtering
- ordering
- pagination via `limit` and `offset`

`ckanext_crida_geojson` converts approved case studies with valid coordinates into an EPSG:4326 `FeatureCollection`. Each feature includes country, title, status, themes, partners, summary text, detail URL, source links, image path, and coordinate note.

### HTTP Endpoints

The route-level JSON endpoints are implemented separately in `utils.py`:

- `/crida/api/case-studies` returns paginated JSON for card-style consumption and category filtering.
- `/crida/api/geojson` wraps the CKAN GeoJSON action and adds HTTP headers for caching and cross-origin access.

Observed caching policy:

- case studies JSON: `Cache-Control: public, max-age=60`
- GeoJSON: `Cache-Control: public, max-age=300`

The GeoJSON endpoint also sends `Access-Control-Allow-Origin: *`, which makes it easier to consume from external mapping clients.

## Frontend Implementation

The frontend is divided between server-rendered templates and progressive JavaScript enhancements.

### Main Templates

The main CRIDA templates observed in the repository are:

- `crida.html`: initiative hub page
- `crida-case-studies_list.html`: case-study catalog
- `crida-case-study.html`: detail page
- `crida-case-study_edit.html`: create/edit form
- `crida-admin-dashboard.html`: moderation dashboard

The detail page renders a richer narrative structure than generic pages. It breaks a case study into overview, context, actions taken, outcomes, highlights, related datasets, related documents, references, and a location panel.

### Edit Form Behavior

`ckanext/pages/public/js/crida-edit.js` enhances the CRIDA edit form with:

- latitude/longitude validation and a map preview via OpenStreetMap embed;
- theme checkbox management stored as JSON;
- partner tag input stored as JSON;
- dataset search against CKAN `package_search`;
- related document upload through `ckanext_pages_upload`;
- repeatable CRIDA highlights;
- classification checkbox synchronization;
- submission buttons for draft, submit, and publish actions.

This makes the CRIDA form one of the more structured editorial interfaces in the extension.

### Catalog and Map Behavior

`ckanext/pages/public/js/crida.js` adds:

- client-side filtering of rendered case-study cards;
- animated counters;
- card hover behavior intended to coordinate with map markers;
- Leaflet rendering for GeoJSON points;
- an iframe fallback intended for Terria integration when Leaflet is unavailable;
- a load-more flow driven by the case studies JSON API.

However, there is an important implementation observation here: the current templates in the repository do not contain a rendered `#crida-map` container or load-more markup. In other words, the JavaScript includes map and incremental-loading support, but the shipped templates appear to use only the server-rendered card catalog plus client-side filtering. The map-capable API surface exists, but the on-page integration is only partial in the inspected snapshot.

## Authorization Model

For public read access, the design is straightforward: anyone can use the list, show, and GeoJSON CRIDA actions.

For editing, the situation is more nuanced:

- `auth.py` defines `crida_case_study_update = water_content_edit`, which suggests the intended policy is "author or sysadmin, with organization membership for creation".
- the plugin registers that CRIDA-specific auth function.
- but the CRIDA edit routes ultimately rely on the generic `ckanext_pages_update` path, and the generic `pages_update_with_org_check` logic does not explicitly include `crida-case-study` in its new-content allowlist.

This creates a visible asymmetry between the intended CRIDA-specific auth model and the generic route/action wiring. If the business expectation is that non-admin users should submit CRIDA case studies through the default UI, this area deserves review.

## Testing Coverage

Observed backend tests for CRIDA are concentrated in `ckanext/pages/tests/test_crida.py`. They cover:

- creation, update, deletion, list, and show operations through the action layer;
- GeoJSON structure and coordinate handling;
- JSON storage for themes and partners;
- workflow expectations for submission and publish behavior;
- helper taxonomies and category metadata;
- coverage checks for the seed `CATEGORY_MAP`.

This means the action-level contract is reasonably protected. At the same time, the repository contains less explicit evidence for full route-level UI workflow testing, especially around CRIDA-specific authoring permissions and the form-to-workflow handoff.

## Implementation Caveats and Technical Debt

Several implementation details are important for maintainers:

### 1. Duplicate `crida_admin_reseed()` definitions

`ckanext/pages/utils.py` contains two functions with the same name, `crida_admin_reseed()`. In Python, the later definition wins, so only the second implementation is actually active at runtime. This is already noted in the project vault and should be treated as technical debt.

### 2. Dormant auto-seed helper

`_auto_seed_crida_if_empty()` exists in `utils.py`, but no in-repository call site was found during inspection. That suggests automatic seeding is currently dormant unless something outside this repository calls it.

### 3. Partial alignment between form workflow and action workflow

The CRIDA form template clearly exposes draft, submit, and publish buttons, but `utils.pages_edit()` does not treat `crida-case-study` the same way it treats some other moderated page types when preparing form payloads. As a result, part of the workflow logic is clearly implemented in `actions.py`, while the route/form layer is only partially aligned with it.

### 4. JSON-heavy storage model

Because CRIDA-specific attributes live in `extras`, many filters and lookups rely on serialized JSON rather than first-class relational columns. This is pragmatic and consistent with the extension architecture, but it also makes reporting, indexing, and advanced querying more fragile than a dedicated schema would.

### 5. Frontend capability exceeds current template wiring

The repository ships map-aware and load-more-aware JavaScript, plus a GeoJSON endpoint intended for map consumers, but the inspected templates do not render the required containers. This suggests either unfinished integration or code prepared for a deployment-specific template variant not present in this repository snapshot.

## Overall Assessment

The CRIDA implementation is best described as a well-developed vertical on top of the shared `ckanext-pages` CMS foundation. Its strongest parts are the data ingestion pipeline, structured case-study metadata, public API exposure, and the narrative detail page model. It also benefits from reusable CKAN mechanisms such as revisions, shared upload handling, and action/auth registration.

Its main weaknesses are not in the core data model, but in consistency between layers: some CRIDA-specific behavior is clearly intended at the template, auth, and JavaScript levels, yet route-level wiring still leans heavily on generic pages behavior. The feature is operational and coherent, but not completely tidy. A future cleanup would likely focus on removing duplicate utilities, aligning UI workflow behavior with the action layer, and deciding whether the map integration should be fully wired into the shipped templates.

## Key Files

- `ckanext/pages/blueprint.py`
- `ckanext/pages/utils.py`
- `ckanext/pages/actions.py`
- `ckanext/pages/auth.py`
- `ckanext/pages/plugin.py`
- `ckanext/pages/logic/schema.py`
- `ckanext/pages/db.py`
- `ckanext/pages/commands/seed_crida.py`
- `ckanext/pages/theme/templates_main/ckanext_pages/crida.html`
- `ckanext/pages/theme/templates_main/ckanext_pages/crida-case-studies_list.html`
- `ckanext/pages/theme/templates_main/ckanext_pages/crida-case-study.html`
- `ckanext/pages/theme/templates_main/ckanext_pages/crida-case-study_edit.html`
- `ckanext/pages/theme/templates_main/ckanext_pages/crida-admin-dashboard.html`
- `ckanext/pages/public/js/crida.js`
- `ckanext/pages/public/js/crida-edit.js`
- `ckanext/pages/tests/test_crida.py`
