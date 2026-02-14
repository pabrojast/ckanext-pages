import pytest
import datetime
from collections import OrderedDict

from ckan.tests import factories, helpers


@pytest.mark.usefixtures("with_plugins", "clean_db")
@pytest.mark.ckan_config("ckan.plugins", "pages")
class TestPagesActions:
    def test_pages_create_action(self, app):
        user = factories.User()
        helpers.call_action(
            "ckanext_pages_update",
            {"user": user["name"]},
            name="page_name",
            title="New Page",
            content="This is a test content",
        )

        page = helpers.call_action("ckanext_pages_show", {}, page="page_name")

        assert page["name"] == "page_name"
        assert page["title"] == "New Page"
        assert page["content"] == "This is a test content"

    def test_pages_update_action(self, app):
        user = factories.User()
        helpers.call_action(
            "ckanext_pages_update",
            {"user": user["name"]},
            name="page_name",
            title="New Page",
            content="This is a test content",
        )

        page = helpers.call_action("ckanext_pages_show", {}, page="page_name")

        assert page["name"] == "page_name"
        assert page["title"] == "New Page"
        assert page["content"] == "This is a test content"

        # sending the parameter page is mandatory for the validator to pass.
        helpers.call_action(
            "ckanext_pages_update",
            {"user": user["name"]},
            name="page_name",
            title="New Page Updated",
            content="This is a test content updated",
            page="page_name",
        )

        page = helpers.call_action("ckanext_pages_show", {}, page="page_name")

        assert page["name"] == "page_name"
        assert page["title"] == "New Page Updated"
        assert page["content"] == "This is a test content updated"

    def test_pages_revision_restore_action(self, app):
        user = factories.User()
        helpers.call_action(
            "ckanext_pages_update",
            {"user": user["name"]},
            name="page_name",
            title="First Revision Title",
            content="First Revision Content",
        )

        helpers.call_action(
            "ckanext_pages_update",
            {"user": user["name"]},
            name="page_name",
            title="Page Updated",
            content="This is a test content updated",
            page="page_name",
        )

        page = helpers.call_action("ckanext_pages_show", {}, page="page_name")

        revisions = page.get('revisions')

        assert len(revisions) == 2
        assert page['content'] == "This is a test content updated"

        sorted_revisions = OrderedDict(reversed(sorted(
                revisions.items(),
                key=lambda x: datetime.datetime.timestamp(
                    datetime.datetime.fromisoformat(x[1]['created'])
                    )
        )))

        last_revision = sorted_revisions.popitem()

        helpers.call_action(
            "ckanext_pages_revision_restore",
            {"user": user["name"]},
            page="page_name",
            revision=last_revision[0]
        )

        page = helpers.call_action("ckanext_pages_show", {}, page="page_name")

        assert page['title'] == "Page Updated"
        assert page['content'] == "First Revision Content"
        assert page['revisions'][last_revision[0]]['current']

    def test_pages_list(self, app):
        sysadmin = factories.Sysadmin()
        helpers.call_action(
            "ckanext_pages_update",
            {"user": sysadmin["name"]},
            name="page_name_1",
            title="New Page 1",
            content="This is a test content",
            private=False,
        )
        helpers.call_action(
            "ckanext_pages_update",
            {"user": sysadmin["name"]},
            name="page_name_2",
            title="New Page 2",
            content="This is a test content",
            private=False,
        )
        helpers.call_action(
            "ckanext_pages_update",
            {"user": sysadmin["name"]},
            name="page_name_3",
            title="New Page 3",
            content="This is a test content",
            private=False,
        )

        results = helpers.call_action("ckanext_pages_list", {"user": sysadmin["name"]})

        assert len(results) == 3
        assert results[0]["title"] == "New Page 3"
        assert results[2]["title"] == "New Page 1"

        helpers.call_action(
            "ckanext_pages_update",
            {"user": sysadmin["name"]},
            name="page_name_4",
            title="New Page 4",
            content="This is a test content",
            private=True,
        )

        results = helpers.call_action("ckanext_pages_list", {"user": sysadmin["name"]})
        assert len(results) == 4

        user = factories.User()
        results = helpers.call_action(
            "ckanext_pages_list", {"user": user["name"], "ignore_auth": False}
        )
        assert len(results) == 3

    def test_workflow_submit_for_review(self, app):
        """Test submitting a page for review"""
        sysadmin = factories.Sysadmin()
        
        # Create a draft page
        helpers.call_action(
            "ckanext_pages_update",
            {"user": sysadmin["name"]},
            name="test_page",
            title="Test Page",
            content="Test content",
            status="draft",
        )
        
        # Submit for review
        result = helpers.call_action(
            "ckanext_pages_submit_for_review",
            {"user": sysadmin["name"]},
            page="test_page",
        )
        
        assert result["status"] == "pending"
        
        # Verify the page is now pending
        page = helpers.call_action("ckanext_pages_show", {"user": sysadmin["name"]}, page="test_page")
        assert page["status"] == "pending"

    def test_workflow_approve(self, app):
        """Test approving a pending page"""
        sysadmin = factories.Sysadmin()
        
        # Create a pending page
        helpers.call_action(
            "ckanext_pages_update",
            {"user": sysadmin["name"]},
            name="test_page_approve",
            title="Test Page",
            content="Test content",
            status="pending",
        )
        
        # Approve the page
        result = helpers.call_action(
            "ckanext_pages_approve",
            {"user": sysadmin["name"]},
            page="test_page_approve",
        )
        
        assert result["status"] == "approved"
        
        # Verify the page is now approved
        page = helpers.call_action("ckanext_pages_show", {"user": sysadmin["name"]}, page="test_page_approve")
        assert page["status"] == "approved"

    def test_workflow_reject(self, app):
        """Test rejecting a pending page"""
        sysadmin = factories.Sysadmin()
        
        # Create a pending page
        helpers.call_action(
            "ckanext_pages_update",
            {"user": sysadmin["name"]},
            name="test_page_reject",
            title="Test Page",
            content="Test content",
            status="pending",
        )
        
        # Reject the page
        result = helpers.call_action(
            "ckanext_pages_reject",
            {"user": sysadmin["name"]},
            page="test_page_reject",
        )
        
        assert result["status"] == "rejected"
        
        # Verify the page is now rejected
        page = helpers.call_action("ckanext_pages_show", {"user": sysadmin["name"]}, page="test_page_reject")
        assert page["status"] == "rejected"

    def test_workflow_visibility_non_admin(self, app):
        """Test that non-admin users can only see approved pages"""
        sysadmin = factories.Sysadmin()
        user = factories.User()
        
        # Create pages with different statuses
        helpers.call_action(
            "ckanext_pages_update",
            {"user": sysadmin["name"]},
            name="draft_page",
            title="Draft Page",
            content="Draft content",
            status="draft",
            private=False,
        )
        
        helpers.call_action(
            "ckanext_pages_update",
            {"user": sysadmin["name"]},
            name="approved_page",
            title="Approved Page",
            content="Approved content",
            status="approved",
            private=False,
        )
        
        # Non-admin should only see approved pages
        results = helpers.call_action(
            "ckanext_pages_list", 
            {"user": user["name"], "ignore_auth": False}
        )
        
        # Should only see the approved page
        page_names = [p['name'] for p in results]
        assert "approved_page" in page_names
        assert "draft_page" not in page_names
