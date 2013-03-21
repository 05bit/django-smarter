django-smarter
==============

Django application for smarter CRUD-based applications building.

Overview
--------

Well, it's mostly about CRUD-based applications - create, read, update and delete different objects, but is not limited to that. If you want admin-like application, but you need a full control on source, than ``django-smarter`` may fit your needs.

Changes in v0.5
---------------

**Warning!** There are some backwards incompatible changes in v0.5

Watch section `Customise views`_.

Installation
------------

Requirements:
    - Django >= 1.3

To install::
    
    pip install django-smarter

Then add ``smarter`` to your ``INSTALLED_APPS``:

.. code:: python

    INSTALLED_APPS = (
        ...
        'smarter',
        ...
    )

Getting started
---------------

Create your models
~~~~~~~~~~~~~~~~~~

Let’s define a simple model:

.. code:: python

    class Page(models.Model):
        title = models.CharField(max_length=100)
        text = models.TextField

        def __unicode__(self):
            return self.title

Create generic views
~~~~~~~~~~~~~~~~~~~~

Now you can create generic views for the model.

In your urls.py:

.. code:: python

    from smarter import SmarterSite
    from myapp.models import Page

    site = SmarterSite()
    site.register(Page)

    urlpatterns = patterns('',
        url(r'^', include(site.urls)),

        # other urls ...
    )

This will create generic views for Page model, accessed by urls:

- /page/
- /page/add/
- /page/<pk>/
- /page/<pk>/edit/
- /page/<pk>/remove/

Customize templates
~~~~~~~~~~~~~~~~~~~

Each url is mapped to view method and templates.

Templates by urls:

- /page/ => myapp/page_index.html
- /page/add/ => myapp/page_add.html
- /page/<pk>/ => myapp/page_details.html
- /page/<pk>/edit/ => myapp/page_edit.html
- /page/<pk>/remove/ => myapp/page_remove.html

Index template has template variable ``objects_list``.

All other templates have variable ``obj``.

Edit and add templates have also template variable ``form``.

Customise views
~~~~~~~~~~~~~~~

**Warning!** This section is new to v0.5 docs and the way of views customization is changed since 0.4.x.

Here's example of view customization with ``options`` dict. Keys in ``options`` are action names, so you can customize any of available actions.

.. code:: python

    from smarter.views import GenericViews
    from django import forms

    class Views(GenericViews):
        model = Page # some model

        options = {
            'add': {
                # custom form class
                'form': PageForm,

                # custom fields widgets
                'widgets': {
                    'title': forms.HiddenInput()
                },

                # explicit form fields
                'fields': ('title', 'text'),

                # exclude fields
                #'exclude': ('title',)
                
                # explicit custom template
                'template': 'page/custom_add.html',

                # help texts for fields
                'help_text': {
                    'title': 'Max. 100 chars',
                }
            },
            #...
        }

Override views
~~~~~~~~~~~~~~

You can subclass views class and add new view methods or override
existing ones.

.. code:: python

    from django.shortcuts import get_object_or_404
    from smarter.views import GenericViews
    from myapp.models import Page

    class PageViews(GenericViews):
        model = Page

        def urls_custom(self):
            return [
                self.url(r'^(?P<pk>\d+)/bookmark/$', 'bookmark')
            ]

        def bookmark_view(self, request, pk):
            obj = get_object_or_404(page, pk=pk)
            # do some stuff for bookmarking ...
            context = {'obj': obj}
            # will render to myapp/page_bookmark.html
            return self.render_to_response(context)

Than you need to register custom views in urls.py:

.. code:: python

    from smarter import SmarterSite
    from myapp.views import PageViews

    site = SmarterSite()
    site.register(PageViews)

    urlpatterns = patterns('',
        url(r'^', include(site.urls)),

        # other urls ...
    )

Applying decorators
~~~~~~~~~~~~~~~~~~~

Assume, you'd like to add ``login_required`` decorator to views in your project. You may subclass from ``GenericViews`` and use ``method_decorator`` helper for that.

.. code:: python

    from django.contrib.auth.decorators import login_required
    from django.utils.decorators import method_decorator
    from smarter.views import GenericViews

    class Views(GenericViews):

        @method_decorator(login_required)
        def add_view(self, *args, **kwargs):
            return super(Views, self).add_view(*args, **kwargs)

Checking permissions
~~~~~~~~~~~~~~~~~~~~

There's a special method ``check_permissions`` which is invoked
from generic views.

It receives keyword arguments depending on processed view:

- for ``add`` action no extra arguments is passed, but if you define ``form_params_add()`` result will be passed as keyword arguments
- for ``edit`` action ``instance`` argument is passed, actually ``form_params_edit()`` result is passed
- for ``details`` and ``remove`` actions ``obj`` argument is passed

.. code:: python

    from django.core.exceptions import PermissionDenied
    from smarter.views import GenericViews

    class Views(GenericViews):

        def check_permissions(self, **kwargs):
            if self.action == 'add':
                if not self.request.is_superuser:
                    raise PermissionDenied

            if self.action == 'edit':
                obj = kwargs['instance']
                if obj.owner != self.request.user:
                    raise PermissionDenied


Hooks
~~~~~

What if you don't want to use ``MyModel.objects.all()``? What if you want to call a function or send a signal every time someone visits a certain object's detail page?

If it's a small change or addition, you can use the following hooks:

- ``get_objects_list(self, action)``, which returns a queryset. It's used directly by ``index_view``, and indirectly by the other views, because ``get_object`` depends on it (read below). The default implementation just returns ``self.model.objects.all()``

- ``get_object(self, pk)``, which will be used to get the object for remove_view, details_view and edit_view. The default implementation just returns ``self.get_objects_list().get(pk=pk)`` or raises ``Http404``.

- ``remove_object(self, obj)``, which deletes the object. The default implementation calls obj.delete().

- ``save_form(self, action, **kwargs)`` saves the form in both the ``edit`` and ``add`` views. 

- ``get_form(self, form)``: in this method, you return a form for the ``edit`` and ``add`` view. It's usually a ``ModelForm``, but you can provide a form instance with a save() method, or hook into ``save_form``. The default implementation gets a form from the ``self.form_class`` dict, otherwise creates a ModelForm using modelform_factory.

Don't forget you can get the current request through ``self.request``, and the current action (E.G. ``'index'`` or ``details``) is available in ``self.action``.
