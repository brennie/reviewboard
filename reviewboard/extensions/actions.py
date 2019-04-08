"""Extension-specific action support."""

from copy import copy


class DictActionMixin(object):
    """An action mixin class for old-style ActionHook dictionaries.

    For backwards compatability, actions may be supplied to action hooks as a
    dictionary of information. This mixin is used (with approprite base
    classes) to convert such a dictionary into a new class-based action.
    """

    def __init__(self, action_info, applies_to=None):
        """Initialize the action.

        Args:
            action_info (dict):
                A dictionary representing this action, as specified by the
                :py:class:`reviewboard.extensions.hooks.ActionHook` class.

            applies_to (callable, optional):
                A callable that examines a given
                :py:class:`~django.template.Context` and determines if the
                action applies.
        """
        action_info = copy(action_info)

        try:
            action_info['action_id'] = action_info.pop('id')
        except KeyError:
            action_info['action_id'] = (
                '%s-action'
                % action_info['label'].lower().replace(' ', '-')
            )

        self.__dict__.update({
            field: action_info[field]
            for field in (
                'action_id',
                'label',
                'url',
                'image',
                'image_height',
                'image_width',
            )
            if field in action_info
        })

        self._applies_to = applies_to

    def should_render(self, context):
        """Return whether or not this action should render.

        This action will be rendered if either `applies_to`` was not passed to
        the constructor, or ``applies_to`` was passed and returns ``True`` when
        applied to ``context``.

        Args:
            context (django.template.context):
                The context that the action is rendering in.

        Returns:
            bool:
            Whether or not this action should be rendered.
        """
        return self._applies_to is None or self._applies_to(context['request'])

    def get_render_context(self, context):
        render_context = super(DictActionMixin, self).get_render_context(
            context)
        render_context['action'].update({
            field: getattr(self, field)
            for field in (
                'image',
                'image_height',
                'image_width',
            )
            if hasattr(self, field)
        })

        return render_context
