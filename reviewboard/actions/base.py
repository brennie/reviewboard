"""Base classes for actions."""

from __future__ import unicode_literals

from django.template.loader import render_to_string


class BaseAction(object):
    """A base class for an action.

    Creating an action requires subclassing :py:class:`BaseAction` and =
    overriding any fields and/or methods as desired. Different instances of the
    same subclass can override the class fields with their own instance
    fields.

    This class is not intended to be subclassed directly. Instead, one of the
    following classes should be subclassed, depending on where you want the
    action to be rendered.

    * :py:class:`reviewboard.actions.header.HeaderAction`
    * :py:class:`reviewboard.actions.header.HeaderMenuAction`
    * :py:class:`reviewboard.reviews.actions.ReviewRequestAction`
    * :py:class:`reviewboard.reviews.actions.ReviewRequestMenuAction`

    Classes subclassing :py:class:`~reviewboard.actions.header.HeaderAction` or
    :py:class:`~reviewboard.actions.header.HeaderMenuAction` will be rendered
    in the page header.

    Classes subclassing
    :py:class:`~reviewboard.reviews.actions.ReviewRequestAction` and
    :py:class:`~reviewboard.reviews.actions.ReviewRequestMenuAction` will be
    rendered in the review request header on review request and diff viewer
    pages.

    Example:
        .. code-block:: python

           class UsedOnceAction(HeaderAction):
               action_id = 'once'
               label = 'This is used once'

           class UsedMultipleAction(HeaderAction):
               def __init__(self, action_id, label):
                   self.action_id = 'repeat-%s' % action_id
                   self.label = label
    Note:
        Since the same action will be rendered for multiple users in a
        multi-threaded environment, the action's state should not be modified
        after initialization. If different attributes are required at runtime,
        the getter methods such as :py:meth:`get_label` can be overridden
        instead. By default, these methods just return the original attribute.
    """

    @property
    def registry(self):
        raise NotImplementedError('%r (type: %s) does not have the registry '
                                  'attribute set'
                                  % (self, type(self)))

    #: The ID of this action.
    #:
    #: This must be unique across all types of actions.
    action_id = None

    #: The label for the action.
    #:
    #: This will be displayed to the user.
    label = None

    #: The URL to invoke if this action is clicked.
    url = '#'

    #: Whether or not this action should be hidden from the user.
    hidden = False

    template_name = 'actions/action.html'
    context_key = 'action'

    def get_label(self, context):
        """Return the label of this action.

        By default, this returns :py:attr:`label`. subclasses can override
        this behaviour.

        Args:
            context (django.template.Context):
                The parent rendering context.


        Returns:
            unicode:
            The label.
        """
        return self.label

    def get_url(self, context):
        """Return the target URL of this action.

        By default, this returns :py:attr:`url`. subclasses can override this
        behaviour.

        Args:
            context (django.template.Context):
                The parent rendering context.

        Returns:
            unicode:
            The target URL.
        """
        return self.url

    def get_hidden(self, context):
        """Return whether or not this action should be hidden.

        By default, this returns :py:attr:`hidden`. subclasses can override
        this behaviour.

        Args:
            context (django.template.Context):
                The parent rendering context.

        Returns:
            bool:
            Whether or not this action should be hidden.
        """
        return self.hidden

    def should_render(self, context):
        """Return whether or not this action should be rendered.

        By default, this always returns ``True``. subclasses can override this
        behaviour.

        Args:
            context (django.template.Context):
                The parent rendering context.

        Returns:
            bool:
            Whether or not this action should be rendered.
        """
        return True

    def render(self, context):
        if self.should_render(context):
            context.push()

            try:
                context[self.context_key] = self.get_render_context(context)
                from pprint import pprint; pprint(context)
                return render_to_string(self.template_name, context)
            finally:
                context.pop()

        return ''

    def get_render_context(self, context):
        """Return the rendering context for this action.

        Args:
            context (django.template.Context):
                The parent rendering context.

        Returns:
            dict:
            A dictionary of information necessary to render this action.
        """
        return {
            'id': self.action_id,
            'label': self.get_label(context),
            'url': self.get_url(context),
            'hidden': self.get_hidden(context)
        }

    def __repr__(self):
        return '<%s(action_id=%s)>' % (type(self).__name__, self.action_id)


class BaseMenuAction(BaseAction):
    """The base class for menu actions.

    This class is not intended to be subclassed directly.
    """

    context_key = 'menu'
    template_name = 'actions/header_action_dropdown.html'

    @property
    def child_actions(self):
        return self.registry.get_child_actions(self.action_id)

    def get_render_context(self, context):
        values = super(BaseMenuAction, self).get_render_context(context)
        values['child_actions'] = list(self.child_actions)
        return values
