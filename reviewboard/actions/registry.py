"""The registry for actions."""

from collections import OrderedDict

from django.utils.translation import ugettext_lazy as _
from djblets.registries.registry import ALREADY_REGISTERED, NOT_REGISTERED

from reviewboard.actions.base import BaseAction
from reviewboard.registries.registry import Registry
from reviewboard.reviews.errors import DepthLimitExceededError


PARENT_IS_CHILD = 'PARENT_IS_CHILD'
PARENT_NOT_FOUND = 'PARENT_NOT_FOUND'


class ActionRegistry(Registry):
    """A registry for tracking a set of actions."""

    default_errors = dict(
        Registry.default_errors,
        **{
            ALREADY_REGISTERED: _(
                'Could not register action %(item)s: it is already registered.'
            ),

            NOT_REGISTERED: _(
                'No action with %(attr_name)s = %(attr_value)r registered.'
            ),

            PARENT_IS_CHILD: _(
                'Could not retrieve children of action with action_id = '
                '%(parent_id)s: this action is a child action.'
            ),

            PARENT_NOT_FOUND: _(
                'Could not retrieve children of action with action_id = '
                '%(parent_id)s: this action is not registered.'
            ),
        }
    )

    lookup_attrs = ('action_id',)

    lookup_error_class = KeyError

    #: The maximum nesting depth for actions.
    MAX_DEPTH = 2

    def __init__(self):
        """Initialize"""
        super(ActionRegistry, self).__init__()

        # A mapping of top-level actions to the IDs of their children.
        #
        # The keys in this dictionary will be all the top-level actions. Any
        # element registered that does not have its ID as a key in this
        # dictionary therefore *must* be a child action.
        self._child_actions = OrderedDict()

        # A mapping of child action IDs to the IDs of their parents.
        self._action_parents = {}

    def register(self, action, parent_id=None):
        """Register an action

        Args:
            action (BaseReviewRequestAction):
                The action to register.

            parent_id (unicode, optional):
                The ID of this action's parent, if any.

                If provided, the action will be nested under that action.
                Actions may only be nested a single level.

        Raises:
            djblets.registries.errors.ItemLookupError:
                If the parent action is not registered.

            reviewboard.reviews.errors.DepthLimitExceededError:
                If the action would be nested too deeply.
        """
        if parent_id:
            if self.get_action(parent_id) is None:
                raise self.lookup_error_class(self.format_error(
                    NOT_REGISTERED,
                    attr_name='action_id',
                    attr_value=parent_id,
                ))
            elif parent_id not in self._child_actions:
                raise DepthLimitExceededError(action.action_id, self.MAX_DEPTH)
            else:
                self._child_actions[parent_id].append(action.action_id)
                self._action_parents[action.action_id] = parent_id
        else:
            self._child_actions[action.action_id] = []

        super(ActionRegistry, self).register(action)

    def populate(self):
        if self._populated:
            return

        self._populated = True

        for item in self.get_defaults():
            if isinstance(item, tuple):
                parent, children = item
                assert isinstance(parent, BaseAction)

                self.register(parent)

                for child in children:
                    self.register(child, parent_id=parent.action_id)
            else:
                assert isinstance(item, BaseAction)
                self.register(item)

    def reset(self):
        print 'reset()'
        print list(self.get_root_actions())
        print list(self)
        if self.populated:
            for root_action in list(self.get_root_actions()):
                self.unregister(root_action)

            super(ActionRegistry, self).reset()

    def unregister(self, action):
        """Unregister an action.

        Args:
            action (BaseReviewRequestAction):
                The action to unregister.

        Raises:
            djblets.registries.errors.ItemLookupError:
                Raised if the item is not found in the registry.
        """
        super(ActionRegistry, self).unregister(action)

        if action.action_id in self._child_actions:
            # This is a parent action and we must unregister all child actions.
            child_ids = self._child_actions[action.action_id]

            for child_id in list(child_ids):
                self.unregister_by_attr('action_id', child_id)

            del self._child_actions[action.action_id]
        else:
            parent_id = self._action_parents.pop(action.action_id)
            self._child_actions[parent_id].remove(action.action_id)

    def get_action(self, action_id):
        """Return the action with the given action ID.

        Args:
            action_id (unicode):
                The ID of the action to return.

        Returns:
            BaseReviewRequestAction:
            The action if it is registered or ``None`` otherwise.
        """
        return self.get('action_id', action_id)

    def get_child_actions(self, parent_id):
        """Yield the child actions.

        Args:
            parent_id (unicode):
                The ID of the parent whose children are to be yielded.

        Yields:
            BaseReviewRequestAction:
            The review request action instances that are children of the given
             action.

        Raises:
            djblets.registries.errors.ItemLookupError:
                If the parent action is not registered.

            ValueError:
                If the parent action is not actually a parent action.
        """
        self.populate()

        if self.get_action(parent_id) is None:
            raise self.lookup_error_class(self.format_error(
                PARENT_NOT_FOUND,
                parent_id=parent_id
            ))
        elif parent_id not in self._child_actions:
            raise ValueError(self.format_error(
                PARENT_IS_CHILD,
                parent_id=parent_id
            ))

        for action_id in self._child_actions[parent_id]:
            yield self.get_action(action_id)

    def get_root_actions(self):
        """Yield the top-level actions.

        Yields:
            BaseReviewRequestAction:
            The top-level registered review request action instances.
        """
        self.populate()

        for action_id in self._child_actions:
            yield self.get_action(action_id)
