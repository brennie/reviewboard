"""Actions-based errors."""

from __future__ import unicode_literals


class DepthLimitExceededError(ValueError):
    """An error that occurs when the maximum depth limit is exceeded.

    Actions cannot be arbitrarily nested. For example, if the
    depth limit is 2, then this error would be triggered if an extension tried
    to add a menu action as follows:

    .. code-block:: python

       BaseReviewRequestActionHook(self, actions=[
           DepthZeroMenuAction([
               DepthOneFirstItemAction(),
               DepthOneMenuAction([
                   DepthTwoMenuAction([  # This depth is acceptable.
                       DepthThreeTooDeepAction(),  # This action is too deep.
                   ]),
               ]),
               DepthOneLastItemAction(),
           ]),
       ])
    """

    def __init__(self, action_id):
        """Initialize the exception."""
        super(DepthLimitExceededError, self).__init__(
            '%s exceeds the maximum depth limit of 2.'
            % action_id)
