from __future__ import unicode_literals

from django.contrib.auth.models import AnonymousUser, User
from django.template import Context
from django.test.client import RequestFactory
from django.utils import six
from djblets.siteconfig.models import SiteConfiguration
from djblets.testing.decorators import add_fixtures
from mock import Mock

from reviewboard.actions.errors import DepthLimitExceededError
from reviewboard.reviews.actions import (AddGeneralCommentAction,
                                         CloseMenuAction,
                                         DeleteAction,
                                         DownloadDiffAction,
                                         EditReviewAction,
                                         ReviewRequestAction,
                                         ReviewRequestMenuAction,
                                         ShipItAction,
                                         SubmitAction,
                                         UpdateMenuAction,
                                         UploadDiffAction,
                                         clear_all_actions,
                                         get_review_request_actions,
                                         get_top_level_actions,
                                         register_actions,
                                         unregister_actions)
from reviewboard.reviews.models import ReviewRequest
from reviewboard.testing import TestCase


class ActionsTestCase(TestCase):
    """Test case for unit tests dealing with actions."""

    @classmethod
    def setUpClass(cls):
        super(ActionsTestCase, cls).setUpClass()

        cls._registry = get_review_request_actions()

    def setUp(self):
        super(ActionsTestCase, self).setUp()

        self.request = RequestFactory().request()
        self.request.user = AnonymousUser()

    def tearDown(self):
        super(ActionsTestCase, self).tearDown()

        # This prevents registered/unregistered/modified actions from leaking
        # between different unit tests.

        self._registry.reset()


class ReadOnlyActionTestsMixin(object):
    """Mixin for Review Board actions-related unit tests with read-only mode.

    This mixin is used to add read-only mode tests to action test cases.Using
    this mixin is especially important for actions that change visibility
    based on whether read-only mode is active. Actions that should always be
    visible can also be tested by setting ``read_only_always_show``.
    """

    def setUp(self):
        """Set up the test case."""
        super(ReadOnlyActionTestsMixin, self).setUp()

        self.siteconfig = SiteConfiguration.objects.get_current()

    def shortDescription(self):
        """Return an updated description for a particular test.

        If the test has an ``action`` attribute set and contains ``<ACTION>``
        in the docstring, then ACTION will be replaced by the ``action_id``
        attribute of the
        :py:class:`~reviewboard.reviews.actions.BaseReviewRequestAction`.

        Returns:
            unicode:
            The description of the test.
        """
        desc = super(ReadOnlyActionTestsMixin, self).shortDescription()

        if self.action and getattr(self, self._testMethodName, False):
            desc = desc.replace('<ACTION>', type(self.action).__name__)

        return desc

    def _create_request_context(self, *args, **kwargs):
        """Create and return objects for use in the request context.

        Args:
            *args (tuple):
                Positional arguments for use in subclasses.

            **kwargs (dict):
                Keyword arguments for use in subclasses.

        Returns:
            dict:
            Additional context to use when testing read-only actions.
        """
        return {}

    def test_should_render_with_user_in_read_only(self):
        """Testing <ACTION>.should_render with authenticated user in read-only
        mode
        """
        self.request.user = User.objects.get(username='doc')

        # Turning on read-only mode prevents creation of some objects so call
        # _create_request_context first.
        request_context = self._create_request_context(user=self.request.user)

        settings = {
            'site_read_only': True,
        }

        with self.siteconfig_settings(settings):
            if getattr(self, 'read_only_always_show', False):
                self.assertTrue(self.action.should_render(request_context))
            else:
                self.assertFalse(self.action.should_render(request_context))

    def test_should_render_with_superuser_in_read_only(self):
        """Testing <ACTION>.should_render with superuser in read-only mode"""
        self.request.user = User.objects.get(username='admin')

        # Turning on read-only mode prevents creation of some objects so call
        # _create_request_context first.
        request_context = self._create_request_context(user=self.request.user)

        settings = {
            'site_read_only': True,
        }

        with self.siteconfig_settings(settings):
            self.assertTrue(self.action.should_render(request_context))


class AddGeneralCommentActionTests(ReadOnlyActionTestsMixin, ActionsTestCase):
    """Unit tests for AddGeneralCommentAction."""

    action = AddGeneralCommentAction()
    fixtures = ['test_users']

    def _create_request_context(self, *args, **kwargs):
        """Create and return objects for use in the request context.

        Args:
            *args (tuple):
                Positional arguments (unused).

            **kwargs (dict):
                Keyword arguments (unused).

        Returns:
            dict:
            Additional context to use when testing read-only actions.
        """
        return {
            'request': self.request,
        }

    def test_should_render_with_authenticated(self):
        """Testing AddGeneralCommentAction.should_render with authenticated
        user
        """
        self.request.user = User.objects.get(username='doc')
        self.assertTrue(
            self.action.should_render(self._create_request_context()))

    def test_should_render_with_anonymous(self):
        """Testing AddGeneralCommentAction.should_render with authenticated
        user
        """
        self.request.user = AnonymousUser()
        self.assertFalse(
            self.action.should_render(self._create_request_context()))


class CloseMenuActionTests(ReadOnlyActionTestsMixin, ActionsTestCase):
    """Unit tests for CloseMenuAction."""

    action = CloseMenuAction()
    fixtures = ['test_users']

    def _create_request_context(self, can_change_status=True, public=True,
                                status=ReviewRequest.PENDING_REVIEW,
                                user=None):
        """Create and return objects for use in the request context.

        Args:
            can_change_status (bool, optional):
                Whether the ``can_change_status`` permission should be set.

            public (bool, optional):
                Whether the review request should be public.

            status (unicode, optional):
                The status for the review request.

            user (django.contrib.auth.models.User, optional):
                An optional user to set as the owner of the request.

            *args (tuple):
                Additional positional arguments (unused).

            **kwargs (dict):
                Additional keyword arguments (unused).

        Returns:
            dict:
            Additional context to use when testing read-only actions.
        """
        review_request = self.create_review_request(
            public=public, status=status)
        self.request.user = user or review_request.submitter

        return {
            'review_request': review_request,
            'request': self.request,
            'perms': {
                'reviews': {
                    'can_change_status': can_change_status,
                },
            },
        }

    def test_should_render_for_owner(self):
        """Testing CloseMenuAction.should_render for owner of review request"""
        self.assertTrue(self.action.should_render(
            self._create_request_context()))

    def test_should_render_for_owner_unpublished(self):
        """Testing CloseMenuAction.should_render for owner of review
        unpublished review request
        """
        self.assertTrue(self.action.should_render(
            self._create_request_context(public=False)))

    def test_should_render_for_user(self):
        """Testing CloseMenuAction.should_render for normal user"""
        self.assertFalse(self.action.should_render(
            self._create_request_context(
                can_change_status=False,
                user=User.objects.create_user(username='test-user',
                                              email='user@example.com'))))

    def test_should_render_user_with_can_change_status(self):
        """Testing CloseMenuAction.should_render for user with
        can_change_status permission
        """
        self.assertTrue(self.action.should_render(
            self._create_request_context(
                can_change_status=True,
                user=User.objects.create_user(username='test-user',
                                              email='user@example.com'))))

    def test_should_render_user_with_can_change_status_and_unpublished(self):
        """Testing CloseMenuAction.should_render for user with
        can_change_status permission and unpublished review request
        """
        self.assertFalse(self.action.should_render(
            self._create_request_context(
                can_change_status=True,
                public=False,
                user=User.objects.create_user(username='test-user',
                                              email='user@example.com'))))

    def test_should_render_with_discarded(self):
        """Testing CloseMenuAction.should_render with discarded review request
        """
        self.assertFalse(self.action.should_render(
            self._create_request_context(status=ReviewRequest.DISCARDED)))

    def test_should_render_with_submitted(self):
        """Testing CloseMenuAction.should_render with submitted review request
        """
        self.assertFalse(self.action.should_render(
            self._create_request_context(status=ReviewRequest.SUBMITTED)))


class DeleteActionTests(ReadOnlyActionTestsMixin, ActionsTestCase):
    """Unit tests for DeleteAction."""

    fixtures = ['test_users']
    action = DeleteAction()

    def _create_request_context(self, delete_reviewrequest=True,
                                *args, **kwargs):
        """Create and return objects for use in the request context.

        Args:
            delete_reviewrequest (bool, optional):
                Whether the resulting context should include the
                ``delete_reviewrequest`` permission.

            *args (tuple):
                Positional arguments (unused).

            **kwargs (dict):
                Keyword arguments (unused).

        Returns:
            dict:
            Additional context to use when testing read-only actions.
        """
        return {
            'request': self.request,
            'perms': {
                'reviews': {
                    'delete_reviewrequest': delete_reviewrequest,
                },
            },
        }

    def test_should_render_with_published(self):
        """Testing DeleteAction.should_render with standard user"""
        self.request.user = User()
        self.assertFalse(self.action.should_render(
            self._create_request_context(delete_reviewrequest=False)))

    def test_should_render_with_permission(self):
        """Testing SubmitAction.should_render with delete_reviewrequest
        permission
        """
        self.request.user = User()
        self.assertTrue(self.action.should_render(
            self._create_request_context()))


class DownloadDiffActionTests(ReadOnlyActionTestsMixin, ActionsTestCase):
    """Unit tests for DownloadDiffAction."""

    action = DownloadDiffAction()
    fixtures = ['test_users']
    read_only_always_show=True

    def _create_request_context(self, review_request=None,
                                url_name='view-diff',
                                *args, **kwargs):
        """Create and return objects for use in the request context.

        Args:
            review_request (reviewboard.reviews.models.review_request.
                            ReviewRequest, optional):
                The review request to use. If not specified, one will be
                created.

            url_name (unicode, optional):
                The URL name to fake on the resolver.

            *args (tuple):
                Positional arguments (unused).

            **kwargs (dict):
                Keyword arguments (unused).

        Returns:
            dict:
            Additional context to use when testing read-only actions.
        """
        self.request.resolver_match = Mock()
        self.request.resolver_match.url_name = url_name

        if not review_request:
            review_request = self.create_review_request()

        return {
            'request': self.request,
            'review_request': review_request,
        }

    def test_get_url_on_diff_viewer(self):
        """Testing DownloadDiffAction.get_url on diff viewer page"""
        self.request.resolver_match = Mock()
        self.request.resolver_match.url_name = 'view-diff'

        self.assertEqual(self.action.get_url({'request': self.request}),
                         'raw/')

    def test_get_url_on_interdiff(self):
        """Testing DownloadDiffAction.get_url on diff viewer interdiff page"""
        self.request.resolver_match = Mock()
        self.request.resolver_match.url_name = 'view-interdiff'

        self.assertEqual(self.action.get_url({'request': self.request}),
                         'raw/')

    def test_get_url_on_diff_viewer_revision(self):
        """Testing DownloadDiffAction.get_url on diff viewer revision page"""
        self.request.resolver_match = Mock()
        self.request.resolver_match.url_name = 'view-diff-revision'

        self.assertEqual(self.action.get_url({'request': self.request}),
                         'raw/')

    def test_get_url_on_review_request(self):
        """Testing DownloadDiffAction.get_url on review request page"""
        self.request.resolver_match = Mock()
        self.request.resolver_match.url_name = 'review-request-detail'

        review_request = self.create_review_request()

        self.assertEqual(
            self.action.get_url({
                'request': self.request,
                'review_request': review_request,
            }),
            '/r/%s/diff/raw/' % review_request.display_id)

    @add_fixtures(['test_site'])
    def test_get_url_on_review_request_with_local_site(self):
        """Testing DownloadDiffAction.get_url on review request page with
        LocalSite
        """
        self.request.resolver_match = Mock()
        self.request.resolver_match.url_name = 'review-request-detail'
        self.request._local_site_name = self.local_site_name

        review_request = self.create_review_request(id=123,
                                                    with_local_site=True)

        self.assertEqual(
            self.action.get_url({
                'request': self.request,
                'review_request': review_request,
            }),
            '/s/%s/r/%s/diff/raw/' % (self.local_site_name,
                                      review_request.display_id))

    def test_get_hidden_on_diff_viewer(self):
        """Testing DownloadDiffAction.get_hidden on diff viewer page"""
        self.request.resolver_match = Mock()
        self.request.resolver_match.url_name = 'view-diff'

        self.assertFalse(self.action.get_hidden({'request': self.request}))

    def test_get_hidden_on_interdiff(self):
        """Testing DownloadDiffAction.get_hidden on diff viewer interdiff page
        """
        self.request.resolver_match = Mock()
        self.request.resolver_match.url_name = 'view-interdiff'

        self.assertTrue(self.action.get_hidden({'request': self.request}))

    def test_get_hidden_on_diff_viewer_revision(self):
        """Testing DownloadDiffAction.get_hdiden on diff viewer revision page
        """
        self.request.resolver_match = Mock()
        self.request.resolver_match.url_name = 'view-diff-revision'

        self.assertFalse(self.action.get_hidden({'request': self.request}))

    def test_get_hidden_on_review_request(self):
        """Testing DownloadDiffAction.get_hdiden on diff viewer revision page
        """
        self.request.resolver_match = Mock()
        self.request.resolver_match.url_name = 'review-request-detail'

        review_request = self.create_review_request()

        self.assertFalse(self.action.get_hidden({
            'request': self.request,
            'review_request': review_request,
        }))

    def test_should_render_on_diff_viewer(self):
        """Testing DownloadDiffAction.should_render on diff viewer page"""
        self.request.resolver_match = Mock()
        self.request.resolver_match.url_name = 'view-diff'

        review_request = self.create_review_request()

        self.assertTrue(self.action.should_render({
            'request': self.request,
            'review_request': review_request,
        }))

    def test_should_render_on_interdiff(self):
        """Testing DownloadDiffAction.should_render on diff viewer interdiff
        page
        """
        self.request.resolver_match = Mock()
        self.request.resolver_match.url_name = 'view-interdiff'

        review_request = self.create_review_request()

        self.assertTrue(self.action.should_render({
            'request': self.request,
            'review_request': review_request,
        }))

    def test_should_render_on_diff_viewer_revision(self):
        """Testing DownloadDiffAction.should_render on diff viewer revision
        page
        """
        self.request.resolver_match = Mock()
        self.request.resolver_match.url_name = 'view-diff-revision'

        review_request = self.create_review_request()

        self.assertTrue(self.action.should_render({
            'request': self.request,
            'review_request': review_request,
        }))

    @add_fixtures(['test_scmtools'])
    def test_should_render_on_review_request_with_repository(self):
        """Testing DownloadDiffAction.should_render on review request page
        with repository
        """
        self.request.resolver_match = Mock()
        self.request.resolver_match.url_name = 'review-request-detail'

        review_request = self.create_review_request(create_repository=True)

        self.assertTrue(self.action.should_render({
            'request': self.request,
            'review_request': review_request,
        }))

    @add_fixtures(['test_scmtools'])
    def test_should_render_on_review_request_without_repository(self):
        """Testing DownloadDiffAction.should_render on review request page
        without repository
        """
        self.request.resolver_match = Mock()
        self.request.resolver_match.url_name = 'review-request-detail'

        review_request = self.create_review_request()

        self.assertFalse(self.action.should_render({
            'request': self.request,
            'review_request': review_request,
        }))


class EditReviewActionTests(ReadOnlyActionTestsMixin, ActionsTestCase):
    """Unit tests for EditReviewAction."""

    action = EditReviewAction()
    fixtures = ['test_users']

    def _create_request_context(self, *args, **kwargs):
        """Create and return objects for use in the request context.

        Args:
            *args (tuple):
                Positional arguments (unused).

            **kwargs (dict):
                Keyword arguments (unused).

        Returns:
            dict:
            Additional context to use when testing read-only actions.
        """
        return {
            'request': self.request,
        }

    def test_should_render_with_authenticated(self):
        """Testing EditReviewAction.should_render with authenticated user"""
        self.request.user = User.objects.get(username='doc')
        self.assertTrue(self.action.should_render(
            self._create_request_context()))

    def test_should_render_with_anonymous(self):
        """Testing EditReviewAction.should_render with authenticated user"""
        self.request.user = AnonymousUser()
        self.assertFalse(self.action.should_render(
            self._create_request_context()))


class ShipItActionTests(ReadOnlyActionTestsMixin, ActionsTestCase):
    """Unit tests for ShipItAction."""

    action = ShipItAction()
    fixtures = ['test_users']

    def _create_request_context(self, *args, **kwargs):
        """Create and return objects for use in the request context.

        Args:
            *args (tuple):
                Positional arguments (unused).

            **kwargs (dict):
                Keyword arguments (unused).

        Returns:
            dict:
            Additional context to use when testing read-only actions.
        """
        return {
            'request': self.request,
        }

    def test_should_render_with_authenticated(self):
        """Testing ShipItAction.should_render with authenticated user"""
        self.request.user = User.objects.get(username='doc')
        self.assertTrue(self.action.should_render(
            self._create_request_context()))

    def test_should_render_with_anonymous(self):
        """Testing ShipItAction.should_render with authenticated user"""
        self.request.user = AnonymousUser()
        self.assertFalse(self.action.should_render(
            self._create_request_context()))


class SubmitActionTests(ReadOnlyActionTestsMixin, ActionsTestCase):
    """Unit tests for SubmitAction."""

    action = SubmitAction()
    fixtures = ['test_users']

    def _create_request_context(self, public=True, user=None, *args, **kwargs):
        """Create and return objects for use in the request context.

        Args:
            public (bool, optional):
                Whether the review request should be public.

            user (django.contrib.auth.models.User, optional):
                The user to check visibility for.

            *args (tuple):
                Positional arguments (unused).

            **kwargs (dict):
                Keyword arguments (unused).

        Returns:
            dict:
            Additional context to use when testing read-only actions.
        """
        review_request = self.create_review_request(public=public)
        self.request.user = user or review_request.submitter

        return {
            'request': self.request,
            'review_request': review_request,
        }

    def test_should_render_with_published(self):
        """Testing SubmitAction.should_render with published review request"""
        self.assertTrue(self.action.should_render(
            self._create_request_context(public=True)))

    def test_should_render_with_unpublished(self):
        """Testing SubmitAction.should_render with unpublished review request
        """
        self.assertFalse(self.action.should_render(
            self._create_request_context(public=False)))


class UpdateMenuActionTests(ReadOnlyActionTestsMixin, ActionsTestCase):
    """Unit tests for UpdateMenuAction."""

    action = UpdateMenuAction()
    fixtures = ['test_users']

    def _create_request_context(self,
                                public=True,
                                status=ReviewRequest.PENDING_REVIEW,
                                user=None,
                                can_edit_reviewrequest=True,
                                *args, **kwargs):
        """Create and return objects for use in the request context.

        Args:
            public (bool, optional):
                Whether the review request should be public.

            status (unicode, optional):
                Review request status.

            user (django.contrib.auth.models.User, optional):
                The user to check visibility for.

            can_edit_reviewrequest (bool, optional):
                Whether the ``can_edit_reviewrequest`` permission should be
                set.

            *args (tuple):
                Positional arguments (unused).

            **kwargs (dict):
                Keyword arguments (unused).

        Returns:
            dict:
            Additional context to use when testing read-only actions.
        """
        review_request = self.create_review_request(public=public,
                                                    status=status)
        self.request.user = user or review_request.submitter

        return {
            'review_request': review_request,
            'request': self.request,
            'perms': {
                'reviews': {
                    'can_edit_reviewrequest': can_edit_reviewrequest,
                },
            },
        }

    def test_should_render_for_owner(self):
        """Testing UpdateMenuAction.should_render for owner of review request
        """
        self.assertTrue(self.action.should_render(
            self._create_request_context(can_edit_reviewrequest=False)))

    def test_should_render_for_user(self):
        """Testing UpdateMenuAction.should_render for normal user"""
        self.assertFalse(self.action.should_render(
            self._create_request_context(
                user=User.objects.create_user(username='test-user',
                                              email='user@example.com'),
                can_edit_reviewrequest=False)))

    def test_should_render_user_with_can_edit_reviewrequest(self):
        """Testing UpdateMenuAction.should_render for user with
        can_edit_reviewrequest permission
        """
        self.assertTrue(self.action.should_render(
            self._create_request_context(
                user=User.objects.create_user(username='test-user',
                                              email='user@example.com'))))

    def test_should_render_with_discarded(self):
        """Testing UpdateMenuAction.should_render with discarded review request
        """
        self.assertFalse(self.action.should_render(
            self._create_request_context(
                status=ReviewRequest.DISCARDED,
                can_edit_reviewrequest=False)))

    def test_should_render_with_submitted(self):
        """Testing UpdateMenuAction.should_render with submitted review request
        """
        self.assertFalse(self.action.should_render(
            self._create_request_context(
                status=ReviewRequest.SUBMITTED,
                can_edit_reviewrequest=False)))


class UploadDiffActionTests(ReadOnlyActionTestsMixin, ActionsTestCase):
    """Unit tests for UploadDiffAction."""

    action = UploadDiffAction()
    fixtures = ['test_users', 'test_scmtools']

    def _create_request_context(self, create_repository=True, user=None,
                                *args, **kwargs):
        """Create and return objects for use in the request context.

        Args:
            create_repository (bool, optional):
                Whether to create a repository for the review request.

            user (django.contrib.auth.models.User, optional):
                The user to check visibility for.

            *args (tuple):
                Positional arguments (unused).

            **kwargs (dict):
                Keyword arguments (unused).

        Returns:
            dict:
            Additional context to use when testing read-only actions.
        """
        review_request = self.create_review_request(
            create_repository=create_repository)
        self.request.user = user or review_request.submitter

        return {
            'review_request': review_request,
            'request': self.request,
        }

    def test_get_label_with_no_diffs(self):
        """Testing UploadDiffAction.get_label with no diffs"""
        review_request = self.create_review_request()
        self.request.user = review_request.submitter

        self.assertEqual(
            self.action.get_label({
                'review_request': review_request,
                'request': self.request,
            }),
            'Upload Diff')

    def test_get_label_with_diffs(self):
        """Testing UploadDiffAction.get_label with diffs"""
        review_request = self.create_review_request(create_repository=True)
        self.create_diffset(review_request)

        self.request.user = review_request.submitter

        self.assertEqual(
            self.action.get_label({
                'review_request': review_request,
                'request': self.request,
            }),
            'Update Diff')

    def test_should_render_with_repository(self):
        """Testing UploadDiffAction.should_render with repository"""
        self.assertTrue(self.action.should_render(
            self._create_request_context()))

    def test_should_render_without_repository(self):
        """Testing UploadDiffAction.should_render without repository"""
        self.assertFalse(self.action.should_render(
            self._create_request_context(create_repository=False)))
