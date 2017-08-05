"""Header actions."""

from reviewboard.actions.base import BaseAction, BaseMenuAction
from reviewboard.actions.registry import ActionRegistry

header_actions = ActionRegistry()


class HeaderAction(BaseAction):
    registry = header_actions

    #: An optional image URL to render with this action.
    image = None

    #: The
    image_width = None
    image_height = None

    def get_image(self, context):
        return self.image

    def get_image_height(self, context):
        return self.image_height

    def get_image_width(self, context):
        return self.image_width

    def get_render_context(self, context):
        values = super(HeaderAction, self).get_render_context(context)

        values.update({
            'image': self.get_image(context),
            'image_height': self.get_image_height(context),
            'image_width': self.get_image_width(context),
        })
        return values


class HeaderMenuAction(BaseMenuAction):
    registry = header_actions
