"""Action templatetags."""

from __future__ import unicode_literals

import logging

from django.template import Library


register = Library()


@register.simple_tag(takes_context=True)
def child_actions(context, menu):
    """Render all registered child actions.

    Args:
        context (django.template.Context):
            The collection of key-value pairs available in the template.

    Returns:
        unicode: The HTML content to be rendered.
    """
    content = []

    for child_action in menu.get('child_actions', []):
        try:
            content.append(child_action.render(context))
        except Exception:
            logging.exception('Error rendering child action %s',
                              child_action.action_id)

    return ''.join(content)
