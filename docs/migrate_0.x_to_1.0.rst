Hints for updating app from older smarter
=========================================

Base API changes
----------------

* name_prefix -> prefix
* SmarterSite -> Site
* smarter.views.GenericViews -> smarter.GenericViews
* register(views_or_model, generic_views=None) -> register(views, model)

URLs paths
----------

Define 'url' for custom actions (search for ``urls_custom``).

URLs names
----------
    
* prefix='([^\']+)-' -> prefix='\1'

Template paths:

* Move templates to new paths::

    ('%(app)s/%(model)s/%(action)s.html',
     '%(app)s/%(model)s/%(action)s.ajax.html',
     'smarter/%(action)s.html',
     'smarter/_form.html',
     'smarter/_ajax.html',)

* or redefine 'template' in defaults, e.g::

    ('%(app)s/%(model)s_%(action)s.html',
     '%(model)s_%(action)s.html',
     'smarter/%(action)s.html')

Decorators
----------
    
Now defined in options as 'decorators' tuple/list, no 'method_decorator' needed.

AJAX
----

Define 'ajax' handler in options.

Permissions
-----------

``GenericViews.check_permissions()`` is not called anymore, use 'permissions' options and ``GenericViews.{action}__perm`` methods.

Form save
---------

``GenericViews.save_form()`` is not called anymore, use ``GenericViews.{action}__save`` methods.

Views
-----

* {action}_view -> {action} 
* {action} method should return dict instead if ``HttpResponse``
* no self.process_form() - it's not needed anymore
* ``update_context`` is not called anymore, use ``{action}__post`` methods
* no ``render_to_response`` method anymore, use Django ``render`` shortcut with ``GenericViews.get_templates`` method
* ``get_object`` and ``get_objects_list`` require request object as first argument
* ``deny`` method requires request object as argument
* form_params_[action] -> [action]'s 'form' in result dict 
