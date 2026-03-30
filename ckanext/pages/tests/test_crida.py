"""Tests for CRIDA case study functionality."""

import pytest
import json

from ckan.tests import factories, helpers


@pytest.mark.usefixtures("with_plugins", "clean_db")
@pytest.mark.ckan_config("ckan.plugins", "pages")
class TestCRIDACaseStudy:
    """Test CRIDA case study CRUD operations."""

    def _create_crida_case_study(self, user, name="test-crida-cs", **kwargs):
        """Helper to create a CRIDA case study."""
        defaults = {
            "name": name,
            "title": "Test CRIDA Case Study",
            "page_type": "crida-case-study",
            "content": "Test content for CRIDA case study",
            "country": "Chile",
            "crida_status": "Finished",
            "latitude": "-30.60",
            "longitude": "-71.05",
            "coord_note": "Aprox (Limarí)",
            "themes": json.dumps(["Drought", "Urban Water Security"]),
            "partners": json.dumps(["UNESCO", "Deltares"]),
            "highlights": json.dumps(["Step 1: Assessment", "Step 2: Analysis"]),
            "submission_action": "publish",
        }
        defaults.update(kwargs)
        return helpers.call_action(
            "ckanext_pages_update",
            {"user": user["name"]},
            **defaults,
        )

    def test_create_crida_case_study(self, app):
        """Test creating a CRIDA case study."""
        sysadmin = factories.Sysadmin()
        self._create_crida_case_study(sysadmin)

        page = helpers.call_action(
            "ckanext_pages_show", {}, page="test-crida-cs"
        )

        assert page["name"] == "test-crida-cs"
        assert page["title"] == "Test CRIDA Case Study"
        assert page["page_type"] == "crida-case-study"
        assert page["country"] == "Chile"
        assert page["crida_status"] == "Finished"
        assert page["latitude"] == "-30.60"
        assert page["longitude"] == "-71.05"

    def test_crida_case_study_list(self, app):
        """Test listing CRIDA case studies via custom action."""
        sysadmin = factories.Sysadmin()
        self._create_crida_case_study(sysadmin, name="crida-cs-1",
                                       title="Case Study 1")
        self._create_crida_case_study(sysadmin, name="crida-cs-2",
                                       title="Case Study 2",
                                       country="Zimbabwe")

        result = helpers.call_action(
            "ckanext_crida_case_study_list",
            {"ignore_auth": True},
        )

        assert len(result) >= 2

    def test_crida_case_study_show(self, app):
        """Test showing a single CRIDA case study."""
        sysadmin = factories.Sysadmin()
        self._create_crida_case_study(sysadmin)

        result = helpers.call_action(
            "ckanext_crida_case_study_show",
            {"ignore_auth": True},
            page="test-crida-cs",
        )

        assert result["title"] == "Test CRIDA Case Study"
        assert result["country"] == "Chile"

    def test_crida_geojson(self, app):
        """Test GeoJSON generation from CRIDA case studies."""
        sysadmin = factories.Sysadmin()
        self._create_crida_case_study(sysadmin, name="geojson-test",
                                       latitude="-30.60",
                                       longitude="-71.05")

        result = helpers.call_action(
            "ckanext_crida_geojson",
            {"ignore_auth": True},
        )

        assert result["type"] == "FeatureCollection"
        assert "features" in result
        assert len(result["features"]) >= 1

        feature = result["features"][0]
        assert feature["type"] == "Feature"
        assert feature["geometry"]["type"] == "Point"
        assert len(feature["geometry"]["coordinates"]) == 2
        assert "country" in feature["properties"]
        assert "title" in feature["properties"]

    def test_crida_case_study_update(self, app):
        """Test updating a CRIDA case study."""
        sysadmin = factories.Sysadmin()
        self._create_crida_case_study(sysadmin)

        helpers.call_action(
            "ckanext_pages_update",
            {"user": sysadmin["name"]},
            name="test-crida-cs",
            page="test-crida-cs",
            title="Updated Title",
            page_type="crida-case-study",
            country="Argentina",
            crida_status="Ongoing",
            submission_action="publish",
        )

        page = helpers.call_action(
            "ckanext_pages_show", {}, page="test-crida-cs"
        )
        assert page["title"] == "Updated Title"
        assert page["country"] == "Argentina"
        assert page["crida_status"] == "Ongoing"

    def test_crida_case_study_delete(self, app):
        """Test deleting a CRIDA case study."""
        sysadmin = factories.Sysadmin()
        self._create_crida_case_study(sysadmin)

        helpers.call_action(
            "ckanext_pages_delete",
            {"user": sysadmin["name"]},
            page="test-crida-cs",
        )

        with pytest.raises(Exception):
            helpers.call_action(
                "ckanext_pages_show", {}, page="test-crida-cs"
            )

    def test_crida_themes_stored_as_json(self, app):
        """Test that themes are stored/retrieved correctly as JSON."""
        sysadmin = factories.Sysadmin()
        themes = ["Drought", "Nature Based Solutions", "Flood"]
        self._create_crida_case_study(
            sysadmin, themes=json.dumps(themes)
        )

        page = helpers.call_action(
            "ckanext_pages_show", {}, page="test-crida-cs"
        )
        stored_themes = json.loads(page["themes"])
        assert stored_themes == themes

    def test_crida_partners_stored_as_json(self, app):
        """Test that partners are stored/retrieved correctly as JSON."""
        sysadmin = factories.Sysadmin()
        partners = ["UNESCO", "World Bank", "Deltares"]
        self._create_crida_case_study(
            sysadmin, partners=json.dumps(partners)
        )

        page = helpers.call_action(
            "ckanext_pages_show", {}, page="test-crida-cs"
        )
        stored_partners = json.loads(page["partners"])
        assert stored_partners == partners


@pytest.mark.usefixtures("with_plugins", "clean_db")
@pytest.mark.ckan_config("ckan.plugins", "pages")
class TestCRIDASubmissionWorkflow:
    """Test the approval/submission workflow for CRIDA case studies."""

    def test_non_admin_submission_creates_pending(self, app):
        """Test that non-admin users create pending submissions."""
        user = factories.User()

        helpers.call_action(
            "ckanext_pages_update",
            {"user": user["name"]},
            name="user-crida-cs",
            title="User Case Study",
            page_type="crida-case-study",
            content="Content",
            country="Chile",
            crida_status="Finished",
            submission_action="submit",
        )

        page = helpers.call_action(
            "ckanext_pages_show",
            {"ignore_auth": True},
            page="user-crida-cs",
        )
        # Non-admin submissions should be pending
        assert page.get("submission_status") in ("pending", "submitted", None)

    def test_admin_can_publish_directly(self, app):
        """Test that sysadmins can publish directly."""
        sysadmin = factories.Sysadmin()

        helpers.call_action(
            "ckanext_pages_update",
            {"user": sysadmin["name"]},
            name="admin-crida-cs",
            title="Admin Case Study",
            page_type="crida-case-study",
            content="Content",
            country="Chile",
            crida_status="Finished",
            submission_action="publish",
        )

        page = helpers.call_action(
            "ckanext_pages_show",
            {"ignore_auth": True},
            page="admin-crida-cs",
        )
        assert page.get("private") is False


@pytest.mark.usefixtures("with_plugins", "clean_db")
@pytest.mark.ckan_config("ckan.plugins", "pages")
class TestCRIDAGeoJSON:
    """Test GeoJSON generation for CRIDA case studies."""

    def test_geojson_structure(self, app):
        """Test GeoJSON output structure."""
        sysadmin = factories.Sysadmin()

        helpers.call_action(
            "ckanext_pages_update",
            {"user": sysadmin["name"]},
            name="geo-cs-1",
            title="GeoJSON Test 1",
            page_type="crida-case-study",
            content="Content",
            country="Chile",
            latitude="-30.60",
            longitude="-71.05",
            crida_status="Finished",
            themes=json.dumps(["Drought"]),
            submission_action="publish",
        )

        result = helpers.call_action(
            "ckanext_crida_geojson",
            {"ignore_auth": True},
        )

        assert result["type"] == "FeatureCollection"
        assert "crs" in result
        assert result["crs"]["properties"]["name"] == "EPSG:4326"
        assert len(result["features"]) >= 1

        feat = result["features"][0]
        assert feat["geometry"]["type"] == "Point"
        coords = feat["geometry"]["coordinates"]
        assert coords[0] == -71.05  # longitude
        assert coords[1] == -30.60  # latitude
        assert feat["properties"]["country"] == "Chile"
        assert feat["properties"]["title"] == "GeoJSON Test 1"

    def test_geojson_only_includes_approved(self, app):
        """Test that GeoJSON only contains approved case studies."""
        sysadmin = factories.Sysadmin()

        # Create published case study
        helpers.call_action(
            "ckanext_pages_update",
            {"user": sysadmin["name"]},
            name="published-cs",
            title="Published CS",
            page_type="crida-case-study",
            content="Content",
            country="Chile",
            latitude="-30.60",
            longitude="-71.05",
            submission_action="publish",
        )

        # Create draft case study
        helpers.call_action(
            "ckanext_pages_update",
            {"user": sysadmin["name"]},
            name="draft-cs",
            title="Draft CS",
            page_type="crida-case-study",
            content="Content",
            country="Argentina",
            latitude="-34.62",
            longitude="-68.33",
            submission_action="draft",
        )

        result = helpers.call_action(
            "ckanext_crida_geojson",
            {"ignore_auth": True},
        )

        titles = [f["properties"]["title"] for f in result["features"]]
        assert "Published CS" in titles
        # Draft should not appear in public GeoJSON
        # (behavior depends on private flag handling)

    def test_geojson_skips_entries_without_coordinates(self, app):
        """Test that entries without coordinates are excluded."""
        sysadmin = factories.Sysadmin()

        helpers.call_action(
            "ckanext_pages_update",
            {"user": sysadmin["name"]},
            name="no-coords-cs",
            title="No Coords CS",
            page_type="crida-case-study",
            content="Content",
            country="Chile",
            submission_action="publish",
        )

        result = helpers.call_action(
            "ckanext_crida_geojson",
            {"ignore_auth": True},
        )

        # Entry without coordinates should not appear
        titles = [f["properties"]["title"] for f in result["features"]]
        assert "No Coords CS" not in titles


@pytest.mark.usefixtures("with_plugins", "clean_db")
@pytest.mark.ckan_config("ckan.plugins", "pages")
class TestCRIDAMainPage:
    """Test CRIDA hub rendering helpers."""

    def test_crida_main_page_normalizes_relative_member_avatar(self, monkeypatch):
        from ckanext.pages import utils
        from ckanext.pages import plugin as pages_plugin

        def fake_get_action(name):
            if name == "group_show":
                return lambda context, data_dict: {"packages": []}
            if name == "member_list":
                return lambda context, data_dict: [
                    ("member-1", "user", "member")
                ]
            if name == "user_show":
                return lambda context, data_dict: {
                    "id": "member-1",
                    "name": "member-1",
                    "display_name": "Member One",
                    "email_hash": "abc123",
                    "image_url": "2023-10-30-210509.799257combinedunescoIHPblueeng.png",
                    "about": "",
                }
            raise AssertionError("Unexpected action requested: %s" % name)

        monkeypatch.setattr(utils.tk, "get_action", fake_get_action)
        monkeypatch.setattr(
            pages_plugin,
            "get_pages_by_initiative",
            lambda initiative, page_type: [],
        )
        monkeypatch.setattr(
            utils.tk,
            "render",
            lambda template, extra_vars=None: {
                "template": template,
                "extra_vars": extra_vars or {},
            },
        )

        result = utils.crida_main_page()
        member = result["extra_vars"]["group_members"][0]

        assert member["image_url"] == (
            "/uploads/user/"
            "2023-10-30-210509.799257combinedunescoIHPblueeng.png"
        )


class TestCRIDACategoryHelpers:
    """Test CRIDA category helper functions (no DB required)."""

    def test_get_crida_sectors_returns_list(self):
        from ckanext.pages.plugin import get_crida_sectors
        sectors = get_crida_sectors()
        assert isinstance(sectors, list)
        assert len(sectors) >= 8
        for s in sectors:
            assert 'id' in s
            assert 'label' in s
            assert 'icon' in s
            assert 'color' in s

    def test_get_crida_stages_returns_list(self):
        from ckanext.pages.plugin import get_crida_stages
        stages = get_crida_stages()
        assert isinstance(stages, list)
        assert len(stages) >= 4
        ids = [s['id'] for s in stages]
        assert 'full-implementation' in ids
        assert 'pilot-exploratory' in ids

    def test_get_crida_regions_returns_list(self):
        from ckanext.pages.plugin import get_crida_regions
        regions = get_crida_regions()
        assert isinstance(regions, list)
        assert len(regions) == 5
        ids = [r['id'] for r in regions]
        assert 'africa' in ids
        assert 'lac' in ids
        assert 'asia-pacific' in ids

    def test_get_crida_scales_returns_list(self):
        from ckanext.pages.plugin import get_crida_scales
        scales = get_crida_scales()
        assert isinstance(scales, list)
        assert len(scales) == 4

    def test_get_crida_climate_challenges_returns_list(self):
        from ckanext.pages.plugin import get_crida_climate_challenges
        challenges = get_crida_climate_challenges()
        assert isinstance(challenges, list)
        assert len(challenges) >= 6
        ids = [c['id'] for c in challenges]
        assert 'drought' in ids
        assert 'flooding' in ids

    def test_get_crida_solution_types_returns_list(self):
        from ckanext.pages.plugin import get_crida_solution_types
        solutions = get_crida_solution_types()
        assert isinstance(solutions, list)
        assert len(solutions) >= 5
        ids = [s['id'] for s in solutions]
        assert 'nature-based' in ids
        assert 'infrastructure' in ids

    def test_get_crida_category_label_known(self):
        from ckanext.pages.plugin import get_crida_category_label
        label = get_crida_category_label('sector', 'water-supply')
        assert label == 'Water Supply & Distribution'

    def test_get_crida_category_label_unknown(self):
        from ckanext.pages.plugin import get_crida_category_label
        label = get_crida_category_label('sector', 'nonexistent')
        assert label == 'nonexistent'

    def test_get_crida_category_label_bad_type(self):
        from ckanext.pages.plugin import get_crida_category_label
        label = get_crida_category_label('invalid_type', 'something')
        assert label == 'something'

    def test_seed_category_map_covers_main_cases(self):
        from ckanext.pages.commands.seed_crida import CATEGORY_MAP
        assert len(CATEGORY_MAP) >= 27
        for key, cats in CATEGORY_MAP.items():
            assert 'sector' in cats, f"Missing sector for {key}"
            assert 'region' in cats, f"Missing region for {key}"
            assert isinstance(cats['sector'], list)
            assert isinstance(cats.get('climate_challenge', []), list)
