.. _action-hooks:
.. _action-hook:

============
Action Hooks
============

There are a variety of action hooks, which allow injecting clickable actions
into various parts of the UI.

:py:mod:`reviewboard.extensions.hooks` contains the following hooks:

.. autosummary::

   ~reviewboard.extensions.hooks.ReviewRequestActionHook
   ~reviewboard.extensions.hooks.DiffViewerActionHook
   ~reviewboard.extensions.hooks.HeaderActionHook

These hooks accept a subclass of :py:class:`~reviewboard.actions.base.BaseAction`, depending on the hook being used:

:py:class:`~reviewboard.reviews.actions.ReviewRequestAction`:
    This action class is used for `~.hooks.DiffViewerActionHook` and
    `~.hooks.ReviewRequestActionHook`.

:py:class:`~reviewboard.actinos.header.HeaderAction`:
    This action class is used for `~.hooks.HeaderActionHook`.

These classes are intended to be subclassed by your extension to provide customized behaviour.

These hooks also support old-style action hook dictionaries from before Review
Board 4.0. A list of dictionaries that define the actions to be inserted can be
passed instead of a subclass of the above classes. These dictionaries must have
the following keys:

*
    **id**: The ID of the action (optional)

*
    **label**: The label for the action.

*
    **url**: The URI to invoke when the action is clicked. If you want to
    invoke a javascript action, this should be '#', and you should use a
    selector on the **id** field to attach the handler (as opposed to a
    javascript: URL, which doesn't work on all browsers).

*
    **image**: The path to the image used for the icon (optional).

*
    **image_width**: The width of the image (optional).

*
    **image_height**: The height of the image (optional).

.. versionchanged:: 4.0
   * The :py:class:`~.hooks.ActionHook` class is now deprecated.
   * The method of passing in a list of dictionaries to these hooks is
     deprecated. Instead, a list of subclasses of :py:class:`~reviewboard.
     actions.base.BaseAction` should be passed instead.

.. seealso:: The :py:mod:`reviewboard.actions` module.

There are also hooks to provide dropdown menus:

.. autosummary::

   ~reviewboard.extensions.hooks.DiffViewerDropdownActionHook
   ~reviewboard.extensions.hooks.ReviewRequestDropdownActionHook
   ~reviewboard.extensions.hooks.HeaderDropdownActionHook

These hooks are work the same as the basic action hooks, except they accept a
list of subclasses of :py:class:`~reviewboard.actions.base.BaseMenuAction`.
Again, which subclass to use depends on the hook being used:

:py:class:`~reviewboard.reviews.actions.ReviewRequestMenuAction`:
    This action class is used for
    :py:class:`~.hooks.DiffViewerDropdownActionHook` and
    :py:class:`~.hooks.ReviewRequestDropdownActionHook`

:py:class:`~reviewboard.actions.header.HeaderMenuAction`:
    This action class is used for :py:class:`~.hooks.HeaderDropdownActionHook`.

These work like the basic ActionHooks, except instead of a **url** field, they
contain an **items** field which is another list of dictionaries. Only one
level of nesting is possible.

.. versionchanged:: 4.0

   * Up to two levels of action nesting are now possible.
   * The method of passing in a list of dictionaries to these hooks is
     deprecated. Instead, a list of subclasses of :py:class:`~reviewboard.
     actions.base.BaseMenuAction` should be pased instead.

.. seealso:: The :py:mod:`reviewboard.actions` module.


Modifying Review Request Actions
================================

.. versionadded:: 3.0

The :py:data:`reviewboard.reviews.actions.review_request_actions` registry is
used to remove (and re-add) default review request actions from an extension.
Specifically the :py:meth:`~reviewboard.reviews.actions.
ReviewRequestActionRegistry.unregister` method is used to remove default
actions and the :py:meth:`reviewboard.reviews.actions.
ReviewRequestActionRegistry.register` method is used to re-add default actions.

Note: any third-party actions should use one of the hooks above instead of
directly mutating the state of the actions registries.


Example
=======

.. code-block:: python

   from reviewboard.extensions.base import Extension
   from reviewboard.extensions.hooks import (HeaderDropdownActionHook,
                                             ReviewRequestActionHook,
                                             ReviewRequestDropdownActionHook)
   from reviewboard.reviews.actions import (CloseMenuAction,
                                            ReviewRequestAction,
                                            ReviewRequestMenuAction,
                                            review_request_actions)
   from reviewboard.urls import reviewable_url_names


   class NewCloseAction(ReviewRequestAction):
       action_id = 'new-close-action'
       label = 'New Close Action!'


   class SampleMenuAction(ReviewRequestMenuAction):
       action_id = 'sample-menu-action'
       label = 'Sample Menu'


   class FirstItemAction(ReviewRequestAction):
       action_id = 'first-item-action'
       label = 'First Item'


   class SampleSubmenuAction(ReviewRequestMenuAction):
       action_id = 'sample-submenu-action'
       label = 'Sample Submenu'


   class SubItemAction(ReviewRequestAction):
       action_id = 'sub-item-action'
       label = 'Sub Item'


   class LastItemAction(ReviewRequestAction):
       action_id = 'last-item-action'
       label = 'Last Item'


    class ReviewableDropdownActionHook(ReviewRequestDropdownActionHook):
        """A special case action hook.

        This hook renders the given dropdown menu on:

        * Review request pages.
        * Diffviewer pages
        * File attachment pages.
        """

        default_apply_to = reviewable_url_names


   class SampleExtension(Extension):
       def initialize(self):
           # Register a new action in the "Close" menu.
           review_request_actions.register(
               NewCloseAction(),
               parent_id=CloseMenuAction.action_id)

           # Register a new review request action that only appears if the user
           # is on a review request page.
           ReviewRequestActionHook(self, actions=[
               {
                   'id': 'foo-item-action',
                   'label': 'Foo Item',
                   'url': '#',
               },
           ])

           # Register a new dropdown menu action (with two levels of nesting)
           # that appears if the user is on a review request page, a file
           # attachment page, or a diff viewer page.
           ReviewableDropdownActionHook(
               self,
               actions=[
                   (SampleMenuAction(), [
                       FirstItemAction(),
                       (SampleSubmenuAction(), [
                           SubItemAction(),
                       ]),
                       LastItemAction(),
                   ]),
               ])

           # Add a dropdown in the header that links to other pages.
           HeaderDropdownActionHook(self, actions=[
               {
                   'label': 'Sample Header Dropdown',
                   'items': [
                       {
                           'label': 'Item 1',
                           'url': '#',
                       },
                       {
                           'label': 'Item 2',
                           'url': '#',
                       },
                   ],
               },
           ])

       def shutdown(self):
           super(SampleExtension, self).shutdown()

           # Since this action was not registered via a hook, we must manually
           # remove it.
           review_request_actions.unregister_by_attr(
               'action_id',
               NewCloseAction.action_id)
