"""Template tags for rendering actions."""

from __future__ import unicode_literals

import logging

from django.template import Library
from django.utils.html import format_html_join


logger = logging.getLogger(__name__)

register = Library()


@register.simple_tag(takes_context=True)
def render_child_actions(context, menu):
    """Render the registered child actions of the given menu action.

    Args:
        context (django.template.Context):
            The current rendering context.

        menu (reviewboard.actions.base.MenuActionMixin):
            The menu action whose children are to be rendered.

    Returns:
        django.util.safestring.SafeText:
        The rendered HTML.
    """
    content = []
    request = context['request']

    for child_action in menu:
        try:
            content.append(child_action.render(request, context))
        except Exception:
            logging.exception('Error rendering child action %s',
                              child_action.action_id)

    return ''.join(content)
