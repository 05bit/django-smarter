django-smarter
==============

**Smarter** way of getting declarative style generic views in Django.

It's a simple one-file helper for painless adding form-based CRUD (create-read-update-delete) views to your application. If you'll feel pain, that's may be not this case, so don't get smarter that way! :)

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

We've made a "quantum jump" by breaking old-and-not-so-good API to new one - solid and nice. Hope you'll like it.


Contributors
------------

* `Fabio Santos <https://github.com/fabiosantoscode>`_
* `Sameer Al-Sakran <https://github.com/salsakran>`_

Thank you comrades! :)

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
        author = models.ForeignKey('auth.User')
        title = models.CharField(max_length=100)
        text = models.TextField()

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

Actions
~~~~~~~

**Actions** are actually 'ids for views'. Well, each action has id like 'add', 'edit', 'bind-to-user' and is mapped to urls like '/add/', '/edit/', '/bind-to-user/'. And each action is bound to view method with underscores instead of '-'.

``smarter.GenericViews`` class defines such actions by default:

=======     =================   =========================
Action      URL                 View method
=======     =================   =========================
index       /                   index(``request``)
add         /add/               add(``request``)
details     /``<pk>``/          details(``request, pk``)
edit        /``<pk>``/edit/     edit(``request, pk``)
remove      /``<pk>``/remove/   remove(``request, pk``)
=======     =================   =========================


Options
~~~~~~~

**Options** is a ``GenericViews.options`` class property, it's a dict containing actions names as keys and actions parameters as values. Parameters structure is:

.. sourcecode:: python

    {
        'url':          <string for url pattern>,
        'form':         <form class>,
        'decorators':   <tuple/list of decorators>,
        'fields':       <tuple/list of form fields>,
        'exclude':      <tuple/list of excluded form fields>,
        'initial':      <tuple/list of form fields initialized by request.GET>,
        'permissions':  <tuple/list of required permissions>,
        'widgets':      <dict for widgets overrides>,
        'help_text':    <dict for help texts overrides>,
        'required':     <dict for required fields overrides>,
        'template':     <string template name>,
    }

Every key here is optional. So, here's how options can be defined for views:

.. sourcecode:: python

    import smarter

    class Views(smarter.GenericViews):
        model = <model>

        defaults = <default parameters>

        options = {
            '<action 1>': <parameters 1>,
            '<action 2>': <parameters 2>
        }

Action names
~~~~~~~~~~~~

Actions are named so they can be mapped to views methods and they should not override reserved attributes and methods, to they:

1. **must contain only** latin symbols and '_' or '-', **no spaces**
2. **can't** be in this list: 'model', 'defaults', 'options', 'resolve', 'deny'
3. **can't** start with '-', '_' or 'get\_'
4. **can't** contain '`__`'

Sure, you'll get an exception if something goes wrong with that. We're following `'errors should never pass silently'` here.

smarter.Site
~~~~~~~~~~~~

| **Site**\(prefix=None, delim='-')
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
|  - method, returns template name or sequence of template names by action name or per-request
|
| **<action>**\(``request, **kwargs``)
|  - method, 1st (starting) handler in default pipeline
|
| **<action>__perm**\(``request, **kwargs``)
|  - method, 2nd handler in default pipeline, checks permissions
|
| **<action>__form**\(``request, **kwargs``)
|  - method, 3rd handler in default pipeline, manages form processing
|
| **<action>__save**\(``request, form, **kwargs``)
|  - method, called from **<action>__form** when form is ready to save, saves the form and returns saved instance
|
| **<action>__done**\(``request, **kwargs``)
|  - method, 4th (last) view handler in default pipeline, performs render or redirect

Pipeline
~~~~~~~~

Each action like 'add', 'edit' or 'remove' is a **pipeline**: a sequence (list) of methods called one after another. A result of each method is passed to the next one.

The result is either **None** or **dict** or **HttpResponse** object:

1. **None** - result from previous pipeline method is used for next one,
2. **dict** - result is passed to next pipeline method,
3. **HttpResponse** - returned immidiately as view response.

For example, '**edit**' action pipeline is:

==========  =====================================  =============================================
  Method               Parameters                                 Result
==========  =====================================  =============================================
edit        ``request, pk``                        {'instance': instance}
edit__perm  ``request, instance=None, **kwargs``   None or PermissionDenied exception is raised
edit__form  ``request, instance=None, **kwargs``   {'instance': instance} *(success)*
                                                   or {'form': 'form'} *(fail)*
edit__done  ``request, instance=None, form=None``  render template or redirect to
                                                   ``instance.get_absolute_url()``
==========  =====================================  =============================================

Note, that in general you won't need to redefine pipeline methods, as in many cases custom behavior can be reached with declarative style using **options**. If you're going too far with overriding views, that may mean you'd better write some views from scratch separate from "smarter".

But for deeper understanding here's an example of custom pipeline for 'edit' action:

.. sourcecode:: python

    import smarter

    class PageViews(smarter.GenericViews):
        model = Page

        def edit(request, pk=None):
            # Custom initial title
            initial = {'title': request.GET.get('title': '')}
            return {
                'initial': initial,
                'instance': self.get_object(pk=pk),
            }

        def edit__perm(request, **kwargs):
            # Custom permission check
            instance = kwargs['instance']
            if instance.author != request.user:
                return self.deny(request)

        def edit__form(request, **kwargs):
            # Actually, nothing custom here, it's totally generic
            form = self.get_form(request, **kwargs)
            if form.is_valid():
                return {'instance': self.edit__save(request, form, **kwargs)}
            else:
                return {'form': form}

        def edit__done(request, instance=None, form=None):
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
