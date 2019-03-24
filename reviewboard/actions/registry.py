"""Registries for actions, which allow for nesting."""

from collections import OrderedDict

from django.utils.translation import ugettext_lazy as _
from djblets.registries.registry import ALREADY_REGISTERED, NOT_REGISTERED
from djblets.registries.signals import registry_populating

from reviewboard.actions.base import BaseAction, MenuActionMixin
from reviewboard.actions.errors import DepthLimitExceededError
from reviewboard.registries.registry import OrderedRegistry


PARENT_IS_CHILD = 'PARENT_IS_CHILD'
PARENT_NOT_FOUND = 'PARENT_NOT_FOUND'


class ActionRegistry(OrderedRegistry):
    """A registry for tracking a set of actions."""

    default_errors = dict(
        OrderedRegistry.default_errors,
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
                'Could not retrieve children of action with action-id = '
                '%(parent_id)s: this action is not registered.'
            ),
        }
    )

    lookup_attrs = ('action_id',)

    lookup_error_class = KeyError

    def __init__(self):
        """Initialize the registry."""
        super(ActionRegistry, self).__init__()

        # A mapping of top-level action IDs to their children's IDs.
        #
        # The keys in this dictionary will be IDs of top-level actions. Any
        # element registered that does not have its ID as a key in this
        # dictionary therefore *must* be a child action.
        self._children = OrderedDict()

        # A mapping of child action IDs to the IDs of their parents.
        self._parents = {}

    def get_action(self, action_id):
        """Return the action with the given action ID.

        Args:
            action_id (unicode):
                The ID of the action to return.

        Returns:
            reviewboard.actions.base.BaseAction:
            The requested action or ``None`` if it is not registered.
        """
        return self.get('action_id', action_id)

    def register(self, action, parent_id=None):
        """Register an action.

        Args:
            action (reviewboard.actions.base.BaseAction):
                The action to register.

            parent_id (unicode, optional):
                The ID of this action's parent action, if any.

                If provided, the action will be nested under that action.
                Actions may only be nested a single level.

        Raises:
            KeyError:
                The parent action is not registered.

            djblets.registries.errors.RegistrationError:
                Raised if the item is missing one of the required attributes.

            djblets.registries.errors.AlreadyRegisteredError:
                Raised if the item is already registered or if the item shares
                an attribute name, attribute value pair with another item in
                the registry.

            reviewboard.actions.errors.DepthLimitExceededError:
                The action would be nested too deeply.
        """
        if parent_id:
            if self.get_action(parent_id) is None:
                raise self.lookup_error_class(self.format_error(
                    NOT_REGISTERED,
                    attr_name='action_id',
                    attr_value=parent_id))
            elif parent_id not in self._children:
                raise DepthLimitExceededError(action.action_id)

        super(ActionRegistry, self).register(action)

        if parent_id:
            self._children[parent_id].append(action.action_id)
            self._parents[action.action_id] = parent_id
        else:
            self._children[action.action_id] = []

    def unregister(self, action):
        """Unregister an action.

        Args:
            action (reviewboard.actions.BaseAction):
                The action to unregister.

        Raises:
            KeyError:
                Raised if the item is not found in the registry.
        """
        super(ActionRegistry, self).unregister(action)

        child_ids = self._children.get(action.action_id)

        if child_ids is not None:
            # This action was a parent action. Unregister all its children.

            for child_id in list(child_ids):
                self.unregister_by_attr('action_id', child_id)

            del self._children[action.action_id]
        else:
            # This action was a child action. Remove its association with its
            # parent action.
            parent_id = self._parents.pop(action.action_id)
            self._children[parent_id].remove(action.action_id)

    def get_root_actions(self):
        """Yield the top-level actions.

        Yields:
            reviewboard.actions.base.Action:
            The top-level registered actions.
        """
        self.populate()

        for action_id in self._children:
            yield self.get_action(action_id)

    def get_child_actions(self, parent_id):
        """Yield the child actions for the given parent.

        Args:
            parent_id (unicode):
                The ID of the parent.

        Yields:
            reviewboard.actions.base.BaseAction:
            The child actions of the parent.

        Raises:
            KeyError:
                The parent action is not registered.

            ValueError:
                The action with the given ``parent_id`` is not a parent action.
        """
        self.populate()

        if self.get_action(parent_id) is None:
            raise self.lookup_error_class(self.format_error(
                PARENT_NOT_FOUND,
                parent_id=parent_id))
        elif parent_id not in self._children:
            raise ValueError(self.format_error(
                PARENT_IS_CHILD,
                parent_id=parent_id))

        for action_id in self._children[parent_id]:
            yield self.get_action(action_id)

    def populate(self):
        """Populate the actions registry."""
        if self._populated:
            return

        self._populated = True

        for item in self.get_defaults():
            if isinstance(item, tuple):
                parent, children = item
                assert isinstance(parent, BaseAction)
                assert isinstance(parent, MenuActionMixin)

                self.register(parent)

                for child in children:
                    self.register(child, parent_id=parent.action_id)

            else:
                assert isinstance(item, BaseAction)
                self.register(item)

        registry_populating.send(sender=type(self),
                                 registry=self)

    def reset(self):
        """Reset the registry."""
        if self.populated:
            # Unregister the root actions, which will subsequently unregister
            # all child actions.
            for root_action in list(self.get_root_actions()):
                self.unregister(root_action)

        super(ActionRegistry, self).reset()

