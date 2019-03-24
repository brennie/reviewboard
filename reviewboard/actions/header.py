"""Actions that appear in the Review Board header."""

from reviewboard.actions.base import BaseAction, MenuActionMixin
from reviewboard.actions.registry import ActionRegistry


_action_registry = ActionRegistry()

def get_header_actions():
    """Return the header action registry.

    Returns:
        ActionRegistry:
        The action registry for header actions.
    """
    return _action_registry


class HeaderAction(BaseAction):
    """An action that appears in the Review Board header."""

    template_name = 'actions/header_action.html'

    registry = _action_registry

    image = None
    image_width = None
    image_height = None

    def get_image(self, context):
        return self.image

    def get_image_width(self, context):
        return self.image_width

    def get_image_height(self, context):
        return self.image_height

    def get_render_context(self, context):
        values = super(HeaderAction, self).get_render_context(context)
        values.update({
            'image': self.get_image(context),
            'image_height': self.get_image_height(context),
            'image_width': self.get_image_width(context),
        })
        return values


class HeaderMenuAction(MenuActionMixin, HeaderAction):
    """A header menu action."""

    template_name = 'actions/header_menu_action.html'
