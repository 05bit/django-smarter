django-smarter
==============

Django application for smarter CRUD-based applications building.

Overview
--------

Well, it's mostly about CRUD-based applications - create, read, update and delete different objects, but is not limited to that. If you want admin-like application, but you need a full control on source, than ``django-smarter`` may fit your needs.

Installation
------------

Requirements:
	- Django >= 1.3

To install::
	
	pip install django-smarter

Then add ``smarter`` to your ``INSTALLED_APPS``::

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

::

	class Page(models.Model):
		title = models.CharField(max_length=100)
		text = models.TextField

		def __unicode__(self):
			return self.title

Create generic views
~~~~~~~~~~~~~~~~~~~~

Now you can create generic views for the model.

In your urls.py:

::

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

Override views
~~~~~~~~~~~~~~

You can subclass views class and add new view methods or override
existing ones.

::

	from django.conf.urls.defaults import patterns, url, include
	from django.shortcuts import get_object_or_404
	from smarter.views import GenericViews
	from myapp.models import Page

	class PageViews(GenericViews):
		model = Page

		@property
		def urlpatterns(self):
			urlatterns = super(PageViews, self).urlpatterns + patterns('',
				url(r'^(?P<pk>\d+)/bookmark/$',
					self.as_view('bookmark'),
					name=self.url_name('bookmark')),
			)
			return urlatterns

		def bookmark_view(self, request, pk):
			obj = get_object_or_404(page, pk=pk)
			# do some stuff for bookmarking ...
			context = {'obj': obj}
			# will render to myapp/page_bookmark.html
			return self.render_to_response(context)

Than you need to register custom views in urls.py:

::

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

Example::

	from django.contrib.auth.decorators import login_required
	from django.utils.decorators import method_decorator
	from smarter.views import GenericViews

	class Views(GenericViews):

		@method_decorator(login_required)
		def add_view(self, *args, **kwargs):
			return super(Views, self).add_view(*args, **kwargs)
