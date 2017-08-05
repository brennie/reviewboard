from __future__ import unicode_literals

from django.template import Context
from djblets.registries.errors import AlreadyRegisteredError

from reviewboard.actions.registry import ActionRegistry
from reviewboard.actions.base import BaseAction, BaseMenuAction
from reviewboard.reviews.errors import DepthLimitExceededError
from reviewboard.testing import TestCase


class ItemAction(BaseAction):
    """An item action for testing."""

    @property
    def registry(self):
        return self._registry

    def __init__(self, registry, action_id='item-action', label='Item Action'):
        self._registry = registry
        self.action_id = action_id
        self.label = label


class MenuAction(BaseMenuAction):
    """A menu action for testing."""

    @property
    def registry(self):
        return self._registry

    def __init__(self, registry, action_id='menu-action', label='Menu Action'):
        self._registry = registry
        self.action_id = action_id
        self.label = label


class PoorlyCodedAction(ItemAction):
    """An action for testing that raises an exception."""

    def get_label(self, context):
        raise Exception()


class ActionRegistryTests(TestCase):
    """Unit tests for the review request actions registry."""

    def test_register_actions_with_invalid_parent_id(self):
        """Testing ActionRegistry.register with an invalid parent ID"""
        registry = ActionRegistry()
        action = ItemAction(registry)

        with self.assertRaises(KeyError):
            registry.register(action, parent_id='bad-id')

    def test_register_actions_with_already_registered_action(self):
        """Testing ActionRegistry.register with an already registered action"""
        registry = ActionRegistry()
        action = ItemAction(registry)

        registry.register(action)

        with self.assertRaises(AlreadyRegisteredError):
            registry.register(action)

    def test_register_actions_with_too_deep(self):
        """Testing ActionRegistry.register with exceeding max nesting"""
        class TestingActionRegistry(ActionRegistry):
            def get_defaults(self):
                return [
                    (MenuAction(self), (
                        ItemAction(self, action_id='nested'),
                    )),
                ]

        registry = TestingActionRegistry()
        invalid_action = ItemAction(registry, action_id='invalid')

        with self.assertRaises(DepthLimitExceededError):
            registry.register(invalid_action, parent_id='nested')

    def test_unregister_actions(self):
        """Testing ActionRegistry.unregister"""
        class TestingActionRegistry(ActionRegistry):
            def get_defaults(self):
                return [
                    (MenuAction(self), (
                        ItemAction(self, action_id='nested-item'),
                    )),
                    ItemAction(self, action_id='top-level-item'),
                ]

        registry = TestingActionRegistry()

        self.assertEqual(len(registry), 3)

        registry.unregister_by_attr('action_id', 'nested-item')
        registry.unregister_by_attr('action_id', 'top-level-item')

        self.assertEqual(set(registry),
                         {registry.get_action('menu-action')})

    def test_unregister_actions_with_child_action(self):
        """Testing ActionRegistry.unregister with nested actions"""
        class TestingActionRegistry(ActionRegistry):
            def get_defaults(self):
                return [
                    (MenuAction(self), (
                        ItemAction(self),
                    ))
                ]

        registry = TestingActionRegistry()

        self.assertEqual(len(registry), 2)

        registry.unregister_by_attr('action_id', 'menu-action')

        self.assertEqual(set(registry), set())

    def test_unregister_actions_with_unregistered_action(self):
        """Testing ActionRegistry.unregister with unregistered action"""
        registry = ActionRegistry()
        foo_action = ItemAction(registry)

        with self.assertRaises(KeyError):
            registry.unregister(foo_action)


class BaseActionTests(TestCase):
    """Unit tests for BaseAction."""

    def test_render_pops_context_even_after_error(self):
        """Testing BaseAction.render pops the context after an exception"""
        registry = ActionRegistry()

        context = Context({'comment': 'this is a comment'})
        old_dict_count = len(context.dicts)
        poorly_coded_action = PoorlyCodedAction(registry)

        with self.assertRaises(Exception):
            poorly_coded_action.render(context)

        new_dict_count = len(context.dicts)
        self.assertEquals(old_dict_count, new_dict_count)
