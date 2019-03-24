"""Base classes for actions."""

from __future__ import unicode_literals

from django.utils.html import mark_safe
from djblets.util.compat.django.template.loader import render_to_string


class BaseAction(object):
    """The base class for all actions.

    This class is not meant to be used or subclassed directly. One of its
    subclasses should be used or subclassed instead.

    Note:
        Since the same action will be rendered for multiple users in a
        multi-threaded environment, the action's state should not be modified
        after initialization. If different attributes are required on a
        per-user basis, the getter methods (:py:meth:`get_label`,
        :py:meth:`get_url`, and :py:meth:`get_hidden`) sould be overridden
        instead.

        By default these methods just return the orginal attributes.
    """

    @property
    def registry(self):
        raise NotImplementedError(
            '%r (type %s) does not have the registry attribute set'
            % (self, type(self).__name__)
        )

    #: The ID of this action.
    #:
    #: This identifier must be unique across the type of action.
    action_id = None

    #: The action's label.
    #:
    #: This will be displayed to the user.
    label = None

    #: The URL to invoke if this action is clicked.
    url = '#'

    #: Whether or not this action should be hidden from the user.
    hidden = False

    @property
    def template_name(self):
        """The template to use for rendering the action."""
        raise NotImplementedError(
            '%r (type %s) does not have the template_name attribute set'
            % (self, type(self).__name__))

    def get_label(self, context):
        """Return the label for this action.

        By default, this returns :py:attr:`label`, but subclasses can override
        this behavior.

        Args:
            context (django.template.Context):
                The context that the action is rendering in.

        Returns:
            unicode:
            The label for this action.
        """
        return self.label

    def get_url(self, context):
        """Return the target URL of this action.

        By default, this returns :py:attr:`url`, but subclasses can override
        this behavior.

        Args:
            context (django.template.Context):
                The context that the action is rendering in.

        Returns:
            unicode:
            The URL to invoke for this action.
        """
        return self.url

    def get_hidden(self, context):
        """Return whether or not the action is to be hidden.

        By default, this returns :py:attr:`hidden`, but subclasses can override
        this behavior.

        Args:
            context (django.template.Context):
                The context that the action is rendering in.

        Returns:
            bool:
            Whether or not this action is to be hidden.
        """
        return self.hidden

    def should_render(self, context):
        """Return whether or not the action should be rendered.

        By default, this always returns ``True``, btu subclasses can override
        this behavior.

        Args:
            context (django.template.context):
                The context that the action is rendering in.

        Returns:
            bool:
            Whether or not this action should be rendered.
        """
        return True

    def render(self, request, context):
        """Render the action.

        Args:
            request (django.http.HttpRequest):
                The HTTP request from the client.

            context (:
                The context that the action is rendering in.

        Returns:
            django.utils.safestring.SafeText:
            The rendered HTML.
        """
        if self.should_render(context):
            render_context = self.get_render_context(context)
            return render_to_string(
                template_name=self.template_name,
                request=request,
                context=render_context)

        return mark_safe('')

    def get_render_context(self, context):
        """Return the rendering context for the action.

        Args:
            context (django.template.Context):
                The context that the action is rendering in.

        Returns:
            dict:
            The context used for rendering the action.
        """
        return {
            'action': {
                'action_id': self.action_id,
                'label': self.get_label(context),
                'url': self.get_url(context),
                'hidden': self.get_hidden(context),
            },
        }

    def __repr__(self):
        """Represent the action as a string.

        Returns:
            unicode:
            A string representation of the type and action ID.
        """
        return '<%s(action_id=%s)>' % (type(self).__name__, self.action_id)


class MenuActionMixin(object):
    """A mixin for transforming an action into a dropdown menu."""

    @property
    def child_actions(self):
        """The list of actions nested under this one."""
        return self.registry.get_child_actions(self.action_id)

    def get_render_context(self, context):
        """Return the rendering context for the menu action.

        Args:
            context (django.template.Context):
                The context that the action is rendering in.

        Returns:
            dict:
            The context used for rendering the menu action.
        """
        render_context = super(MenuActionMixin, self).get_render_context(
            context)
        render_context['action']['children'] = list(self.child_actions)
        return render_context

