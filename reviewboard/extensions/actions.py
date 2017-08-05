from copy import copy


class DictActionMixin(object):
    """An action for ActionHook-style dictionaries.

    For backwards compatibility, actions may also be supplied as a dictionary
    of information. This mixin is used (with an appropriate base class) to
    convert such a dictionary into a new-style action class.
    """

    def __init__(self, action, applies_to=None):
        """Initialize this action.

        Args:
            action (dict):
                A dictionary representing this action, as specified by the
                :py:class:`ActionHook` class.

            applies_to (callable, optional):
                A callable that examines a given context and determines if this
                action applies to the page.
        """
        action = copy(action)

        try:
            action['action_id'] = action.pop('id')
        except KeyError:
            action['action_id'] = ('%s-action'
                                   % action['label'].lower().replace(' ', '-'))

        self.__dict__.update(action)
        self._applies_to = applies_to

    def should_render(self, context):
        """Return whether or not this action should render.

        Args:
            context (django.template.Context):
                The collection of key-value pairs available in the template
                just before this action is to be rendered.

        Returns:
            bool: Determines if this action should render.
        """
        return self._applies_to is None or self._applies_to(context['request'])
