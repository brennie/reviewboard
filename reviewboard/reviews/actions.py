"""Review request actions."""

from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _
from djblets.util.compat.django.template.loader import render_to_string

from reviewboard.admin.read_only import is_site_read_only_for
from reviewboard.actions.errors import DepthLimitExceededError
from reviewboard.actions.base import BaseAction, MenuActionMixin
from reviewboard.actions.registry import ActionRegistry
from reviewboard.reviews.features import general_comments_feature
from reviewboard.reviews.models import ReviewRequest
from reviewboard.site.urlresolvers import local_site_reverse


class ReviewRequestActionRegistry(ActionRegistry):
    """An actions registry specifically for review request actions."""

    def get_defaults(self):
        """Return the default review request actions.

        Returns:
            list:
            A list of the default review request actions.
        """
        return [
            (CloseMenuAction(), (
                SubmitAction(),
                DiscardAction(),
                DeleteAction(),
            )),
            (UpdateMenuAction(), (
                UploadDiffAction(),
                UploadFileAction(),
            )),
            DownloadDiffAction(),
            EditReviewAction(),
            AddGeneralCommentAction(),
            ShipItAction(),
        ]


_action_registry = ReviewRequestActionRegistry()


def get_review_request_actions():
    """Return the review request action registry.

    Returns:
        ReviewRequestActionRegistry:
        The review request action registry.
    """
    return _action_registry


class ReviewRequestAction(BaseAction):
    """The base class for review request actions."""

    registry = _action_registry
    template_name = 'reviews/action.html'

    render_in_read_only_mode = False

    def get_render_context(self, context):
        render_context = super(ReviewRequestAction,
                               self).get_render_context(context)
        render_context.update({
            field: context[field]
            for field in ('request', 'review_request', 'perms')
        })
        return render_context

    def should_render(self, context):
        """Return whether or not the action should render.

        By default, actions do not render in read-only mode (unless the user is
        a superuser).

        Args:
            context (django.template.Context):
                The current rendering context.

        Returns:
            bool:
            Whether or not the action should render.
        """
        return (self.render_in_read_only_mode or
                not is_site_read_only_for(context['request'].user))


class ReviewRequestMenuAction(MenuActionMixin, ReviewRequestAction):
    """The base class for review request menu actions."""

    template_name = 'reviews/menu_action.html'



def get_top_level_actions():
    """Return a generator of all top-level registered action instances.

    Yields:
        BaseReviewRequestAction:
        All top-level registered review request action instances.
    """
    return _action_registry.get_root_actions()


def register_actions(actions, parent_id=None):
    """Register the given actions as children of the corresponding parent.

    If no parent_id is given, then the actions are assumed to be top-level.

    Args:
        actions (iterable of BaseReviewRequestAction):
            The collection of action instances to be registered.

        parent_id (unicode, optional):
            The action ID of the parent of each action instance to be
            registered.

    Raises:
        KeyError:
            The parent action cannot be found or a second registration is
            attempted (action IDs must be unique across all types of actions
            and menu actions, at any depth).

        reviewboard.actions.errors.DepthLimitExceededError:
            The maximum depth limit is exceeded.
    """
    for action in actions:
        _action_registry.register(action, parent_id)


def unregister_actions(action_ids):
    """Unregister each of the actions corresponding to the given IDs.

    Args:
        action_ids (iterable of unicode):
            The collection of action IDs corresponding to the actions to be
            removed.

    Raises:
        KeyError:
            An unregistration is attempted before it's registered.
    """
    for action_id in action_ids:
        _action_registry.unregister_by_attr('action_id', action_id)


def clear_all_actions():
    """Clear all registered actions.

    This method is really only intended to be used by unit tests. We might be
    able to remove this hack once we convert to djblets.registries.

    Warning:
        This will clear **all** actions, even if they were registered in
        separate extensions.
    """
    _action_registry.reset()


class CloseMenuAction(ReviewRequestMenuAction):
    """A menu action for closing a review request."""

    action_id = 'close-review-request-action'
    label = _('Close')

    def should_render(self, context):
        """Return whether or not the action should render.

        This action will render if the review request is pending review and the
        user is either the submitter or has the ``reviews.can_change_status``
        permission.

        Args:
            context (django.template.Context):
                The current rendering context.

        Returns:
            bool:
            Whether or not the action should render.
        """
        review_request = context['review_request']

        return (
            super(CloseMenuAction, self).should_render(context) and
            (review_request.status == ReviewRequest.PENDING_REVIEW and
             (context['request'].user.pk == review_request.submitter_id or
              (context['perms']['reviews']['can_change_status'] and
               review_request.public)))
        )


class SubmitAction(ReviewRequestAction):
    """An action for submitting a review request."""

    action_id = 'submit-review-request-action'
    label = _('Submitted')

    def should_render(self, context):
        """Return whether or not the action should render.

        This action will render only if the review request is public.

        Args:
            context (django.template.Context):
                The current rendering context.

        Returns:
            bool:
            Whether or not the action should render.
        """
        return (
            super(SubmitAction, self).should_render(context) and
            context['review_request'].public
        )


class DiscardAction(ReviewRequestAction):
    """An action for discarding the review request."""

    action_id = 'discard-review-request-action'
    label = _('Discarded')


class DeleteAction(ReviewRequestAction):
    """An action for permanently deleting the review request."""

    action_id = 'delete-review-request-action'
    label = _('Delete Permanently')

    def should_render(self, context):
        """Return whether or not the action should render.

        This action will render only if the user has the
        ``reviews.delete_reviewrequest`` permission.

        Args:
            context (django.template.Context):
                The current rendering context.

        Returns:
            bool:
            Whether or not the action should render.
        """
        return (
            super(DeleteAction, self).should_render(context) and
            context['perms']['reviews']['delete_reviewrequest']
        )


class UpdateMenuAction(ReviewRequestMenuAction):
    """A menu action for updating the corresponding review request."""

    action_id = 'update-review-request-action'
    label = _('Update')

    def should_render(self, context):
        """Return whether or not the action should render.

        This action will render only if the the review request is pending and
        the user is either the submitter or has the
        ``reviews.can_edit_reviewrequest`` permission

        Args:
            context (django.template.Context):
                The current rendering context.

        Returns:
            bool:
            Whether or not the action should render.
        """
        review_request = context['review_request']
        return (
            super(UpdateMenuAction, self).should_render(context) and
            (review_request.status == ReviewRequest.PENDING_REVIEW and
             (context['request'].user.pk == review_request.submitter_id or
              context['perms']['reviews']['can_edit_reviewrequest']))
        )


class UploadDiffAction(ReviewRequestAction):
    """An action for updating/uploading a diff for the review request."""

    action_id = 'upload-diff-action'

    def get_label(self, context):
        """Return the action's label.

        The label will change depending on whether or not the review request
        already has a diff.

        Args:
            context (django.template.Context):
                The current rendering context.

        Returns:
            unicode:
            The label for this action.
        """
        review_request = context['review_request']
        draft = review_request.get_draft(context['request'].user)

        if (draft and draft.diffset) or review_request.get_diffsets():
            return _('Update Diff')

        return _('Upload Diff')

    def should_render(self, context):
        """Return whether or not the action should render.

        This action will only render if the review request is associated with a
        repository.

        Args:
            context (django.template.Context):
                The current rendering context.

        Returns:
            bool:
            Whether or not the action should render.
        """
        return (
            super(UploadDiffAction, self).should_render(context) and
            context['review_request'].repository_id is not None
        )


class UploadFileAction(ReviewRequestAction):
    """An action for uploading a file for the review request."""

    action_id = 'upload-file-action'
    label = _('Add File')


class DownloadDiffAction(ReviewRequestAction):
    """An action for downloading a diff from the review request."""

    action_id = 'download-diff-action'
    label = _('Download Diff')

    render_in_read_only_mode = True

    def get_url(self, context):
        """Return the URL for this action.

        Args:
            context (django.template.Context):
                The current rendering context.

        Returns:
            unicode:
            The URL for this action.
        """
        from reviewboard.urls import diffviewer_url_names

        if context['request'].resolver_match.url_name in diffviewer_url_names:
            return 'raw/'

        return local_site_reverse(
            'raw-diff',
            context['request'],
            kwargs={
                'review_request_id': context['review_request'].display_id,
            })

    def get_hidden(self, context):
        """Return whether or not the action should be initially hidden.

        Args:
            context (django.template.Context):
                The current rendering context.

        Returns:
            bool:
            Whether or not the action should be initially hidden.
        """
        return (
            context['request'].resolver_match.url_name == 'view-interdiff' or
            super(DownloadDiffAction, self).get_hidden(context)
        )

    def should_render(self, context):
        """Return whether or not the action should render.

        This action will only render if the review request has a diff
        associated with it or we are on a diffviewer URL.

        Args:
            context (django.template.Context):
                The current rendering context.

        Returns:
            bool:
            Whether or not the action should render.
        """
        from reviewboard.urls import diffviewer_url_names

        url_name = context['request'].resolver_match.url_name

        return (
            super(DownloadDiffAction, self).should_render(self) and
            (context['review_request'].repository_id is not None or
             url_name in diffviewer_url_names)
        )


class EditReviewAction(ReviewRequestAction):
    """An action for editing a review for the review request."""

    action_id = 'review-action'
    label = _('Review')

    def should_render(self, context):
        """Return whether or not the action should render.

        This action will only render if the user is authenticatd.

        Args:
            context (django.template.Context):
                The current rendering context.

        Returns:
            bool:
            Whether or not the action should render.
        """
        return (
            super(EditReviewAction, self).should_render(context) and
            context['request'].user.is_authenticated()
        )

class AddGeneralCommentAction(ReviewRequestAction):
    """An action for adding a new general comment to a review."""

    action_id = 'general-comment-action'
    label = _('Add General Comment')

    def should_render(self, context):
        """Return whether or not the action should render.

        This action will only render if the user is authenticated and the
        general comments feature is enabled.

        Args:
            context (django.template.Context):
                The current rendering context.

        Returns:
            bool:
            Whether or not the action should render.
        """
        request = context['request']
        return (
            super(AddGeneralCommentAction, self).should_render(context) and
            request.user.is_authenticated() and
            general_comments_feature.is_enabled(request=request)
        )

class ShipItAction(ReviewRequestAction):
    """An action for quickly approving the review request without comments."""

    action_id = 'ship-it-action'
    label = _('Ship It!')

    def should_render(self, context):
        """Return whether or not the action should render.

        This action will only render if the user is authenticated.

        Args:
            context (django.template.Context):
                The current rendering context.

        Returns:
            bool:
            Whether or not the action should render.
        """
        return (
            super(ShipItAction, self).should_render(context) and
            context['request'].user.is_authenticated()
        )
