#-*- coding: utf-8 -*-
import re
from django.conf.urls.defaults import patterns, include, url


class AlreadyRegistered(Exception):
    """Views registration error: view is already registered."""
    pass


class InvalidAction(Exception):
    """Views action error: action name must contain only latin
    letters and "_"/"-", can't start with "get_" or "_"/"-", can't
    contain "__".
    """
    pass


_baseconfig = {
    'index': {
        'url': r'',
    },
    'add': {
        'url': r'add/',
    },
    'details': {
        'url': r'(?P<pk>\d+)/',
    },
    'edit': {
        'url': r'(?P<pk>\d+)/edit/',
    },
    'remove': {
        'url': r'(?P<pk>\d+)/remove/',
    },
}


class Site(object):
    def __init__(self, prefix=None, delim='-'):
        if not delim in ('-', '-', ''):
            raise Exception("Delimiter must be in '-', '_' or empty string.")
        self._prefix = prefix
        self._delim = delim
        self._registered = []

    def register(self, model_or_views, base_url=None, prefix=None):
        """Register views.

        Arguments:
        model_or_views -- model or views class

        Keyword arguments:
        base_url -- base url for views
        prefix   -- prefix in url names for urls resolver

        Returns: None
        """
        from django.db.models import Model

        if issubclass(model_or_views, Model):
            model, views = model_or_views, GenericViews
        else:
            model, views = None, model_or_views

        for r in self._registered:
            if r['model'] == model and r['views'] == views:
                raise AlreadyRegistered()

        prefix_bits, model_name = [], model._meta.object_name.lower()
        if self._prefix:
            prefix_bits.append(self._prefix)
        if prefix:
            prefix_bits.append(prefix)
        else:
            prefix_bits.append(model_name)

        self._registered.append({
                'base_url': base_url and base_url or '%s/' % model_name,
                'prefix': self._delim.join(prefix_bits),
                'delim': self._delim,
                'model': model,
                'views': views,
            })

    @property
    def urls(self):
        """Site urls."""
        return [url(r['base_url'], include(r['views']()._urls(**r)))
            for r in self._registered]


class GenericViews(object):

    def __init__(self):
        options = getattr(self, 'options', {})
        defaults = getattr(self, 'defaults', {})
        self._actions = set(_baseconfig.keys()).union(defaults.keys()).union(options.keys())
        for action in self._actions:
            if re.match(r"^((get_|_|-).*|.*__.*)", action):
                raise InvalidAction("Invalid action name: %s" % action)

    def _urls(self, **kw):
        return [url(r'^' + self._param(action, 'url') + r'$',
                    self._view(action, kw['model']),
                    name=kw['delim'].join((kw['prefix'], action)))
                for action in self._actions]

    def _param(self, action, name):
        options = getattr(self, 'options', {})
        defaults = getattr(self, 'defaults', {})
        if action in options and name in options[action]:
            return options[action][name]
        elif action in defaults and name in defaults[action]:
            return defaults[action][name]
        else:
            return _baseconfig[action][name]

    def _pipeline(self, action, options):
        pass

    def _view(self, action, model):
        def v(request):
            raise Exception(action)
        return v

    def index(self, request):
        pass










from django.db.models import Model
# from smarter.views import GenericViews, BaseViews
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





