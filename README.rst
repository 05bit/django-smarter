django-smarter
==============

Django application for smarter generic applications building.

Overview
--------

What is *generic* Django application? Well, it's mostly about add-edit-view-remove different objects, but is not limited to that.

If you want admin-like application, but you need a full control on source, than ``django-smarter`` may fit your needs.

Installation
------------

Requirements:
	- Django >= 1.3

To install::
	
	pip install django-smarter

Then add `smarter` to your `INSTALLED_APPS`.

Getting started
---------------

Create your models
~~~~~~~~~~~~~~~~~~

Let’s define a simple model:

.. code-block:: python

	class Page(models.Model):
		title = models.CharField(max_length=100)
		text = models.TextField

		def __unicode__(self):
			return self.name

Create generic views
~~~~~~~~~~~~~~~~~~~~

Now you can create generic views for the model.

In your urls.py:

.. code-block:: python

	from smarter import SmarterSite
	from myapp.models import Page

	site = SmarterSite()
	site.register(Page)

	urlpatterns = patterns('',
		url(r'^', include(site.urls)),

		# other urls ...
	)

This will create generic views for Page model, accessed by urls:

	/page/
	/page/add/
	/page/<pk>/
	/page/<pk>/edit/
	/page/<pk>/remove/

Customize templates
~~~~~~~~~~~~~~~~~~~

Each url is mapped to view method and templates.

Templates by urls:

	/page/ => myapp/page_index.html
	/page/add/ => myapp/page_add.html
	/page/<pk>/ => myapp/page_details.html
	/page/<pk>/edit/ => myapp/page_edit.html
	/page/<pk>/remove/ => myapp/page_remove.html

Index template has template variable ``objects_list``.

All other templates have variable ``obj``.

Edit and add templates have also template variable ``form``.

Override views
~~~~~~~~~~~~~~

You can subclass views class and add new view methods or override
existing ones.

.. code-block:: python

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


