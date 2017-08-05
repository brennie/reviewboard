"""Tests for review request actions."""

from __future__ import unicode_literals

from django.contrib.auth.models import AnonymousUser, User
from django.test.client import RequestFactory
from djblets.testing.decorators import add_fixtures
from mock import Mock

from reviewboard.reviews.actions import (AddGeneralCommentAction,
                                         CloseMenuAction,
                                         DeleteAction,
                                         DownloadDiffAction,
                                         EditReviewAction,
                                         ShipItAction,
                                         SubmitAction,
                                         UpdateMenuAction,
                                         UploadDiffAction)
from reviewboard.reviews.models import ReviewRequest
from reviewboard.testing import TestCase


class AddGeneralCommentActionTests(TestCase):
    """Unit tests for AddGeneralCommentAction."""

    fixtures = ['test_users']

    def setUp(self):
        super(AddGeneralCommentActionTests, self).setUp()

        self.action = AddGeneralCommentAction()

    def test_should_render_with_authenticated(self):
        """Testing AddGeneralCommentAction.should_render with authenticated
        user
        """
        request = RequestFactory().request()
        request.user = User.objects.get(username='doc')

        self.assertTrue(self.action.should_render({'request': request}))

    def test_should_render_with_anonymous(self):
        """Testing AddGeneralCommentAction.should_render with authenticated
        user
        """
        request = RequestFactory().request()
        request.user = AnonymousUser()

        self.assertFalse(self.action.should_render({'request': request}))


class CloseMenuActionTests(TestCase):
    """Unit tests for CloseMenuAction."""

    fixtures = ['test_users']

    def setUp(self):
        super(CloseMenuActionTests, self).setUp()

        self.action = CloseMenuAction()

    def test_should_render_for_owner(self):
        """Testing CloseMenuAction.should_render for owner of review request"""
        review_request = self.create_review_request(publish=True)

        request = RequestFactory().request()
        request.user = review_request.submitter

        self.assertTrue(self.action.should_render({
            'review_request': review_request,
            'request': request,
            'perms': {
                'reviews': {
                    'can_change_status': False,
                },
            },
        }))

    def test_should_render_for_owner_unpublished(self):
        """Testing CloseMenuAction.should_render for owner of review
        unpublished review request
        """
        review_request = self.create_review_request(public=False)

        request = RequestFactory().request()
        request.user = review_request.submitter

        self.assertTrue(self.action.should_render({
            'review_request': review_request,
            'request': request,
            'perms': {
                'reviews': {
                    'can_change_status': False,
                },
            },
        }))

    def test_should_render_for_user(self):
        """Testing CloseMenuAction.should_render for normal user"""
        review_request = self.create_review_request(publish=True)

        request = RequestFactory().request()
        request.user = User.objects.create_user(username='test-user',
                                                email='user@example.com')

        self.assertFalse(self.action.should_render({
            'review_request': review_request,
            'request': request,
            'perms': {
                'reviews': {
                    'can_change_status': False,
                },
            },
        }))

    def test_should_render_user_with_can_change_status(self):
        """Testing CloseMenuAction.should_render for user with
        can_change_status permission
        """
        review_request = self.create_review_request(publish=True)

        request = RequestFactory().request()
        request.user = User.objects.create_user(username='test-user',
                                                email='user@example.com')

        self.assertTrue(self.action.should_render({
            'review_request': review_request,
            'request': request,
            'perms': {
                'reviews': {
                    'can_change_status': True,
                },
            },
        }))

    def test_should_render_user_with_can_change_status_and_unpublished(self):
        """Testing CloseMenuAction.should_render for user with
        can_change_status permission and unpublished review request
        """
        review_request = self.create_review_request(public=False)

        request = RequestFactory().request()
        request.user = User.objects.create_user(username='test-user',
                                                email='user@example.com')

        self.assertFalse(self.action.should_render({
            'review_request': review_request,
            'request': request,
            'perms': {
                'reviews': {
                    'can_change_status': True,
                },
            },
        }))

    def test_should_render_with_discarded(self):
        """Testing CloseMenuAction.should_render with discarded review request
        """
        review_request = \
            self.create_review_request(status=ReviewRequest.DISCARDED)

        request = RequestFactory().request()
        request.user = review_request.submitter

        self.assertFalse(self.action.should_render({
            'review_request': review_request,
            'request': request,
            'perms': {
                'reviews': {
                    'can_change_status': False,
                },
            },
        }))

    def test_should_render_with_submitted(self):
        """Testing CloseMenuAction.should_render with submitted review request
        """
        review_request = \
            self.create_review_request(status=ReviewRequest.SUBMITTED)

        request = RequestFactory().request()
        request.user = review_request.submitter

        self.assertFalse(self.action.should_render({
            'review_request': review_request,
            'request': request,
            'perms': {
                'reviews': {
                    'can_change_status': False,
                },
            },
        }))


class DeleteActionTests(TestCase):
    """Unit tests for DeleteAction."""

    def setUp(self):
        super(DeleteActionTests, self).setUp()

        self.action = DeleteAction()

    def test_should_render_with_published(self):
        """Testing DeleteAction.should_render with standard user"""
        self.assertFalse(self.action.should_render({
            'perms': {
                'reviews': {
                    'delete_reviewrequest': False,
                },
            },
        }))

    def test_should_render_with_permission(self):
        """Testing SubmitAction.should_render with delete_reviewrequest
        permission
        """
        self.assertTrue(self.action.should_render({
            'perms': {
                'reviews': {
                    'delete_reviewrequest': True,
                },
            },
        }))


class DownloadDiffActionTests(TestCase):
    """Unit tests for DownloadDiffAction."""

    fixtures = ['test_users']

    def setUp(self):
        super(DownloadDiffActionTests, self).setUp()

        self.action = DownloadDiffAction()

    def test_get_url_on_diff_viewer(self):
        """Testing DownloadDiffAction.get_url on diff viewer page"""
        request = RequestFactory().request()
        request.resolver_match = Mock()
        request.resolver_match.url_name = 'view-diff'

        self.assertEqual(self.action.get_url({'request': request}),
                         'raw/')

    def test_get_url_on_interdiff(self):
        """Testing DownloadDiffAction.get_url on diff viewer interdiff page"""
        request = RequestFactory().request()
        request.resolver_match = Mock()
        request.resolver_match.url_name = 'view-interdiff'

        self.assertEqual(self.action.get_url({'request': request}),
                         'raw/')

    def test_get_url_on_diff_viewer_revision(self):
        """Testing DownloadDiffAction.get_url on diff viewer revision page"""
        request = RequestFactory().request()
        request.resolver_match = Mock()
        request.resolver_match.url_name = 'view-diff-revision'

        self.assertEqual(self.action.get_url({'request': request}),
                         'raw/')

    def test_get_url_on_review_request(self):
        """Testing DownloadDiffAction.get_url on review request page"""
        request = RequestFactory().request()
        request.resolver_match = Mock()
        request.resolver_match.url_name = 'review-request-detail'

        review_request = self.create_review_request()

        self.assertEqual(
            self.action.get_url({
                'request': request,
                'review_request': review_request,
            }),
            '/r/%s/diff/raw/' % review_request.display_id)

    @add_fixtures(['test_site'])
    def test_get_url_on_review_request_with_local_site(self):
        """Testing DownloadDiffAction.get_url on review request page with
        LocalSite
        """
        request = RequestFactory().request()
        request.resolver_match = Mock()
        request.resolver_match.url_name = 'review-request-detail'
        request._local_site_name = self.local_site_name

        review_request = self.create_review_request(id=123,
                                                    with_local_site=True)

        self.assertEqual(
            self.action.get_url({
                'request': request,
                'review_request': review_request,
            }),
            '/s/%s/r/%s/diff/raw/' % (self.local_site_name,
                                      review_request.display_id))

    def test_get_hidden_on_diff_viewer(self):
        """Testing DownloadDiffAction.get_hidden on diff viewer page"""
        request = RequestFactory().request()
        request.resolver_match = Mock()
        request.resolver_match.url_name = 'view-diff'

        self.assertFalse(self.action.get_hidden({'request': request}))

    def test_get_hidden_on_interdiff(self):
        """Testing DownloadDiffAction.get_hidden on diff viewer interdiff page
        """
        request = RequestFactory().request()
        request.resolver_match = Mock()
        request.resolver_match.url_name = 'view-interdiff'

        self.assertTrue(self.action.get_hidden({'request': request}))

    def test_get_hidden_on_diff_viewer_revision(self):
        """Testing DownloadDiffAction.get_hdiden on diff viewer revision page
        """
        request = RequestFactory().request()
        request.resolver_match = Mock()
        request.resolver_match.url_name = 'view-diff-revision'

        self.assertFalse(self.action.get_hidden({'request': request}))

    def test_get_hidden_on_review_request(self):
        """Testing DownloadDiffAction.get_hdiden on diff viewer revision page
        """
        request = RequestFactory().request()
        request.resolver_match = Mock()
        request.resolver_match.url_name = 'review-request-detail'

        review_request = self.create_review_request()

        self.assertFalse(self.action.get_hidden({
            'request': request,
            'review_request': review_request,
        }))

    def test_should_render_on_diff_viewer(self):
        """Testing DownloadDiffAction.should_render on diff viewer page"""
        request = RequestFactory().request()
        request.resolver_match = Mock()
        request.resolver_match.url_name = 'view-diff'

        review_request = self.create_review_request()

        self.assertTrue(self.action.should_render({
            'request': request,
            'review_request': review_request,
        }))

    def test_should_render_on_interdiff(self):
        """Testing DownloadDiffAction.should_render on diff viewer interdiff
        page
        """
        request = RequestFactory().request()
        request.resolver_match = Mock()
        request.resolver_match.url_name = 'view-interdiff'

        review_request = self.create_review_request()

        self.assertTrue(self.action.should_render({
            'request': request,
            'review_request': review_request,
        }))

    def test_should_render_on_diff_viewer_revision(self):
        """Testing DownloadDiffAction.should_render on diff viewer revision
        page
        """
        request = RequestFactory().request()
        request.resolver_match = Mock()
        request.resolver_match.url_name = 'view-diff-revision'

        review_request = self.create_review_request()

        self.assertTrue(self.action.should_render({
            'request': request,
            'review_request': review_request,
        }))

    @add_fixtures(['test_scmtools'])
    def test_should_render_on_review_request_with_repository(self):
        """Testing DownloadDiffAction.should_render on review request page
        with repository
        """
        request = RequestFactory().request()
        request.resolver_match = Mock()
        request.resolver_match.url_name = 'review-request-detail'

        review_request = self.create_review_request(create_repository=True)

        self.assertTrue(self.action.should_render({
            'request': request,
            'review_request': review_request,
        }))

    @add_fixtures(['test_scmtools'])
    def test_should_render_on_review_request_without_repository(self):
        """Testing DownloadDiffAction.should_render on review request page
        without repository
        """
        request = RequestFactory().request()
        request.resolver_match = Mock()
        request.resolver_match.url_name = 'review-request-detail'

        review_request = self.create_review_request()

        self.assertFalse(self.action.should_render({
            'request': request,
            'review_request': review_request,
        }))


class EditReviewActionTests(TestCase):
    """Unit tests for EditReviewAction."""

    fixtures = ['test_users']

    def setUp(self):
        super(EditReviewActionTests, self).setUp()

        self.action = EditReviewAction()

    def test_should_render_with_authenticated(self):
        """Testing EditReviewAction.should_render with authenticated user"""
        request = RequestFactory().request()
        request.user = User.objects.get(username='doc')

        self.assertTrue(self.action.should_render({'request': request}))

    def test_should_render_with_anonymous(self):
        """Testing EditReviewAction.should_render with authenticated user"""
        request = RequestFactory().request()
        request.user = AnonymousUser()

        self.assertFalse(self.action.should_render({'request': request}))


class ShipItActionTests(TestCase):
    """Unit tests for ShipItAction."""

    fixtures = ['test_users']

    def setUp(self):
        super(ShipItActionTests, self).setUp()

        self.action = ShipItAction()

    def test_should_render_with_authenticated(self):
        """Testing ShipItAction.should_render with authenticated user"""
        request = RequestFactory().request()
        request.user = User.objects.get(username='doc')

        self.assertTrue(self.action.should_render({'request': request}))

    def test_should_render_with_anonymous(self):
        """Testing ShipItAction.should_render with authenticated user"""
        request = RequestFactory().request()
        request.user = AnonymousUser()

        self.assertFalse(self.action.should_render({'request': request}))


class SubmitActionTests(TestCase):
    """Unit tests for SubmitAction."""

    fixtures = ['test_users']

    def setUp(self):
        super(SubmitActionTests, self).setUp()

        self.action = SubmitAction()

    def test_should_render_with_published(self):
        """Testing SubmitAction.should_render with published review request"""
        self.assertTrue(self.action.should_render({
            'review_request': self.create_review_request(public=True),
        }))

    def test_should_render_with_unpublished(self):
        """Testing SubmitAction.should_render with unpublished review request
        """
        self.assertFalse(self.action.should_render({
            'review_request': self.create_review_request(public=False),
        }))


class UpdateMenuActionTests(TestCase):
    """Unit tests for UpdateMenuAction."""

    fixtures = ['test_users']

    def setUp(self):
        super(UpdateMenuActionTests, self).setUp()

        self.action = UpdateMenuAction()

    def test_should_render_for_owner(self):
        """Testing UpdateMenuAction.should_render for owner of review request
        """
        review_request = self.create_review_request(publish=True)

        request = RequestFactory().request()
        request.user = review_request.submitter

        self.assertTrue(self.action.should_render({
            'review_request': review_request,
            'request': request,
            'perms': {
                'reviews': {
                    'can_edit_reviewrequest': False,
                },
            },
        }))

    def test_should_render_for_user(self):
        """Testing UpdateMenuAction.should_render for normal user"""
        review_request = self.create_review_request(publish=True)

        request = RequestFactory().request()
        request.user = User.objects.create_user(username='test-user',
                                                email='user@example.com')

        self.assertFalse(self.action.should_render({
            'review_request': review_request,
            'request': request,
            'perms': {
                'reviews': {
                    'can_edit_reviewrequest': False,
                },
            },
        }))

    def test_should_render_user_with_can_edit_reviewrequest(self):
        """Testing UpdateMenuAction.should_render for user with
        can_edit_reviewrequest permission
        """
        review_request = self.create_review_request(publish=True)

        request = RequestFactory().request()
        request.user = User.objects.create_user(username='test-user',
                                                email='user@example.com')

        self.assertTrue(self.action.should_render({
            'review_request': review_request,
            'request': request,
            'perms': {
                'reviews': {
                    'can_edit_reviewrequest': True,
                },
            },
        }))

    def test_should_render_with_discarded(self):
        """Testing UpdateMenuAction.should_render with discarded review request
        """
        review_request = \
            self.create_review_request(status=ReviewRequest.DISCARDED)

        request = RequestFactory().request()
        request.user = review_request.submitter

        self.assertFalse(self.action.should_render({
            'review_request': review_request,
            'request': request,
            'perms': {
                'reviews': {
                    'can_edit_reviewrequest': False,
                },
            },
        }))

    def test_should_render_with_submitted(self):
        """Testing UpdateMenuAction.should_render with submitted review request
        """
        review_request = \
            self.create_review_request(status=ReviewRequest.SUBMITTED)

        request = RequestFactory().request()
        request.user = review_request.submitter

        self.assertFalse(self.action.should_render({
            'review_request': review_request,
            'request': request,
            'perms': {
                'reviews': {
                    'can_edit_reviewrequest': False,
                },
            },
        }))


class UploadDiffActionTests(TestCase):
    """Unit tests for UploadDiffAction."""

    fixtures = ['test_users']

    def setUp(self):
        super(UploadDiffActionTests, self).setUp()

        self.action = UploadDiffAction()

    def test_get_label_with_no_diffs(self):
        """Testing UploadDiffAction.get_label with no diffs"""
        review_request = self.create_review_request()

        request = RequestFactory().request()
        request.user = review_request.submitter

        self.assertEqual(
            self.action.get_label({
                'review_request': review_request,
                'request': request,
            }),
            'Upload Diff')

    @add_fixtures(['test_scmtools'])
    def test_get_label_with_diffs(self):
        """Testing UploadDiffAction.get_label with diffs"""
        review_request = self.create_review_request(create_repository=True)
        self.create_diffset(review_request)

        request = RequestFactory().request()
        request.user = review_request.submitter

        self.assertEqual(
            self.action.get_label({
                'review_request': review_request,
                'request': request,
            }),
            'Update Diff')

    @add_fixtures(['test_scmtools'])
    def test_should_render_with_repository(self):
        """Testing UploadDiffAction.should_render with repository"""
        review_request = self.create_review_request(create_repository=True)

        self.assertTrue(self.action.should_render({
            'review_request': review_request,
        }))

    def test_should_render_without_repository(self):
        """Testing UploadDiffAction.should_render without repository"""
        review_request = self.create_review_request()

        self.assertFalse(self.action.should_render({
            'review_request': review_request,
        }))
