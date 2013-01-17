#-*- coding: utf-8 -*-
from django.conf.urls.defaults import patterns, include, url
from django.db.models import Model
from smarter.views import GenericViews, BaseViews

class SmarterSite(object):

    def __init__(self, name_prefix=None):
        self.name_prefix = name_prefix
        self.registered = []

    @property
    def urls(self):
        urlpatterns = patterns('')
        for item in self.registered:
            urlpatterns += patterns('',
                url('^' + item['base_url'], include(item['urls']))
            )
        return urlpatterns

    def register(self, model_or_views, generic_views=GenericViews,
                base_url=None, name_prefix=None):
        if issubclass(model_or_views, BaseViews):
            if hasattr(model_or_views, 'model'):
                model = model_or_views.model
        elif issubclass(model_or_views, Model):
            model = model_or_views

        if model:
            model_name = model.__name__.lower()
            full_name_prefix = self.name_prefix or ''
            full_name_prefix += name_prefix or ('%s-' % model_name)
            full_base_url = base_url or ('%s/' % model_name)
        else:
            full_name_prefix = (self.name_prefix or '') + (name_prefix or '')
            full_base_url = base_url or ''

        if issubclass(model_or_views, BaseViews):
            urls = model_or_views.as_urls(
                                name_prefix=full_name_prefix)
        elif issubclass(model_or_views, Model):
            urls = generic_views.as_urls(model=model_or_views,
                                name_prefix=full_name_prefix)
        else:
            raise Exception("First argument must be model class or BaseViews subclass")

        self.registered.append({
                'base_url': full_base_url,
                'urls': urls
            })

    def unregister(self, model_or_views):
        raise NotImplementedError





