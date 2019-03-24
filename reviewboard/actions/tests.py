from __future__ import unicode_literals

from djblets.registries.errors import AlreadyRegisteredError

from reviewboard.actions.base import BaseAction, MenuActionMixin
from reviewboard.actions.errors import DepthLimitExceededError
from reviewboard.actions.registry import ActionRegistry
from reviewboard.testing import TestCase


class ItemAtion(BaseAction):
    """An item action for testing."""

    @property
    def registry(self):
        return self._registry

    def __init__(self, registry, action_id='item-action', label='Item Action'):
        """Intialize the action.

        Args:
            registry (reviewboard.actions.registry.ActionRegistry):
                The action registry to use.

            action_id (unicode):
                The unique ID for this action.

            label (unicode):
                The label for this action.
        """
        self._registry = registry
        self.action_id = action_id
        self.label = label


class MenuAction(MenuActionMixin, ItemAction):
    """A menu action for testing."""

    def __init__(self, registry, action_id='menu-action', label='Menu Action'):
        """Intialize the action.

        Args:
            registry (reviewboard.actions.registry.ActionRegistry):
                The action registry to use.

            action_id (unicode):
                The unique ID for this action.

            label (unicode):
                The label for this action.
        """
        super(MenuAction, self).__init__(registry, action_id, label)


class ActionRegistryTests(TestCase):
    """Unit tests for reviewboard.actions.registry.ActionRegistry."""

    def test_register_acitons_with_parent_id(self):
        """Testing ActionRegistry.register with an invalid parent ID"""
        registry = ActionRegistry()
        parent = MenuAction(registry)
        item = ItemAction(registry)

        registry.register(menu)
        registry.register(item, parent_id=parent.action_id)

        self.assertEqual(set(registry), {parent, item})
        self.assertEqual(list(registry.get_root_actions()), [parent])

        self.assertEqual(list(registry.get_child_actions(parent.action_id)),
                         [item])

    def test_register_actions_with_invalid_parent_id(self):
        """Testing ActionRegistry.register with an invalid parent ID"""
        registry = ActionRegistry()
        action = ItemAction(registry)

        with self.assertRaises(KeyError):
            registry.action(action, parent_id='missing')

    def test_register_actions_too_deeply(self):
        """Testing ActionRegistry.register with actions nested too deeply"""
        registry = ActionRegistry()
        menu = MenuAction(registry)
        submenu = MenuAction(registry, action_id='submenu-action')
        item = ItemAction(registry)

        registry.register(menu)
        registry.register(submenu, parent_id=menu.action_id)

        with self.assertRaises(DepthLimitExceededError):
            registry.register(item, parent_id=submenu.action_id)

    def test_unregister_actions(self):
        """Testing ActionRegistry.unregister with child actions"""
        registry = ActionRegistry()

        menu = MenuAction(registry)
        item1 = ItemAction(registry, action_id='item1')
        item2 = ItemAction(registry, action_id='item2')

        registry.register(menu)
        registry.register(item1, parent_id=menu.action_id)
        registry.register(item2)

        self.assertEqual(set(registry), {menu, item1, item2})
        self.assertEqual(set(registry.get_root_actions()), {menu, item2})

        self.unregister(menu)
        self.assertEqual(set(registry), {item2})

        with self.assertRaises(KeyError):
            self.get_child_actions(menu.action_id)


        self.unregister(item2)
        self.assertEqual(len(registry), 0)
