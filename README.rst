django-smarter
==============

**Smarter** way of getting declarative style generic views in Django project. It's a simple one-file helper for painless adding form-based CRUD (create-read-update-delete) views to your application. If you'll feel pain, that's may be not this case, so don't get smarter that way! :)

So many times we have to write:

.. sourcecode:: python

    def edit_post(request, pk):
        post = get_object_or_404(Post, pk=pk)
        if request.method == 'POST':
            form = EditPostForm(request.POST, instance=post)
            if form.is_valid():
                post = form.save()
                return redirect(post.get_absolute_url())
        else:
            form = EditPostForm()
        return render(request, 'edit_post.html', {'form': form})

Right? Well, it's ok to write some reusable helpers for such repeatable views, but when we don't need sophisticated ones we can go **smarter**:

.. sourcecode:: python

    class PostViews(smarter.GenericViews):
        model = Post
        options = {
            'add': {
                'form': NewPostForm
            }
            'edit': {
                'form': EditPostForm
            }
        }

That's it.


Changes in v1.0
---------------

API is finally and completely changed since v0.6 release.

We've made a "quantum jump" by breaking old-and-not-so-good API to new solid nice one and hope you'll like it.


Installation
------------

Requirements:
    - Django >= 1.3

To install::
    
    pip install django-smarter

You *may* add ``smarter`` to your ``INSTALLED_APPS`` to get default templates, but you *don't have to*:

.. sourcecode:: python

    INSTALLED_APPS = (
        ...
        'smarter',
        ...
    )

Then you should define your views and include them in urls, see `Getting started`_ section below.


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

    import smarter
    from myapp.models import Page

    site = smarter.Site()
    site.register(Page)

    urlpatterns = patterns('',
        url(r'^', include(site.urls)),

        # other urls ...
    )

This will create generic views for Page model, accessed by urls:

- /page/
- /page/add/
- /page/``<pk>``/
- /page/``<pk>``/edit/
- /page/``<pk>``/remove/

Customize templates
~~~~~~~~~~~~~~~~~~~

Each url by default is mapped to view method and template.

======================  ======================= =====================
         URL                    Template                Context
======================  ======================= =====================
/page/                  myapp/page_index.html   {{ objects_list }}
/page/add/              myapp/page_add.html     {{ obj }}, {{ form }}
/page/``<pk>``/         myapp/page_details.html {{ obj }}
/page/``<pk>``/edit/    myapp/page_edit.html    {{ obj }}, {{ form }}
/page/``<pk>``/remove/  myapp/page_remove.html  {{ obj }}
======================  ======================= =====================


API reference
-------------

smarter.Site
~~~~~~~~~~~~

| **Site**\(prefix=None)
|  - constructor
|
| **register**\(model_or_views, base_url=None, prefix=None)
|  - method to add your model or views
|
| **urls**
|  - property

smarter.GenericViews
~~~~~~~~~~~~~~~~~~~~

| **model**
|  - class property, model class for views
|
| **defaults**
|  - class property, dict with default options applied to all actions until being overriden by ``options``
|
| **options**
|  - class property, dict for views configration, each key corresponds to single action like 'add', 'edit', 'remove' etc.
|
| **resolve**\(``action, *args, **kwargs``)
|  - method, resolves url for given action name
|
| **deny**\(``request, message=None``)
|  - method, is called when action is not permitted for user, raises ``PermissionDenied`` exception or can return ``HttpResponse`` object
|
| **get_form**\(``request, **kwargs``)
|  - method, returns form for request
|
| **get_object**\(``request, **kwargs``)
|  - method, returns single object for request
|
| **get_objects_list**\(``request, **kwargs``)
|  - method, returns objects for request
|
| **get_template**\(``request_or_action``)
|  - method, returns template name or sequence of template names for rendering by action name or per-request
|
| **<action>**\(``request, **kwargs``)
|  - method, 1st (starting) handler in default pipeline
|
| **<action>_perm**\(``request, **kwargs``)
|  - method, 2nd handler in default pipeline, checks permissions
|
| **<action>_form**\(``request, **kwargs``)
|  - method, 3rd handler in default pipeline, manages form processing
|
| **<action>_save**\(``request, form, **kwargs``)
|  - method, called from **<action>_form** when form is ready to save, saves the form and returns saved instance
|
| **<action>_done**\(``request, **kwargs``)
|  - method, 4th (last) view handler in default pipeline, performs render or redirect

Options
~~~~~~~

sdfsd


Pipeline
~~~~~~~~

Each action like 'add', 'edit' or 'remove' is a **pipeline**: a sequence (list) of methods called one after another. A result of each method is passed to the next one.

The result is either **None** or **dict** or **HttpResponse** object:

1. **None** - result from previous pipeline method is used for next one,
2. **dict** - result is passed to next pipeline method,
3. **HttpResponse** - returned immidiately as view response.

For example, 'edit' pipeline is:

=========   =============================================
  Method                       Result
=========   =============================================
edit        {'instance': instance}
edit_perm   None or PermissionDenied exception is raised
edit_form   {'instance': instance} *(success)*
            or {'form': 'form'} *(fail)*
edit_done   render template or redirect to
            ``instance.get_absolute_url()``
=========   =============================================

Note, that in general you won't need to redefine pipeline methods, as in many cases custom behavior can be reached using **options**.

But for deeper understanding here's an example of custom pipeline for 'edit' action:

.. sourcecode:: python

    import smarter

    class PageViews(smarter.GenericViews):

        def edit(request, pk=None):
            # Custom initial title
            initial = {'title': request.GET.get('title': '')}
            return {
                'initial': initial,
                'instance': self.get_object(pk=pk),
            }

        def edit_perm(request, **kwargs):
            # Custom permission check
            instance = kwargs['instance']
            if instance.author != request.user:
                return self.deny(request)

        def edit_form(request, **kwargs):
            # Actually, nothing custom here, it's totally generic
            form = self.get_form(request, **kwargs)
            if form.is_valid():
                return {'instance': self.edit_save(request, form, **kwargs)}
            else:
                return {'form': form}

        def edit_done(request, instance=None, form=None):
            # Custom redirect to pages index on success
            if instance:
                # Success, redirecting!
                return redirect(self.resolve('index'))
            else:
                # Fail, form has errors
                return render(request, self.get_template(request), {'form': form})


Lightweight example
-------------------

...


Complete example
----------------

| You may look at complete example source here:
| https://github.com/05bit/django-smarter/tree/master/example


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
