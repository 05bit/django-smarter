#-*- coding: utf-8 -*-
import re
import warnings
from django.conf.urls.defaults import patterns, include, url
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render, redirect


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

_action = '_action'


class Site(object):
    def __init__(self, prefix=None, delim='-'):
        if not delim in ('-', '-', ''):
            raise Exception("Delimiter must be in '-', '_' or empty string.")
        self._prefix = prefix
        self._delim = delim
        self._registered = []

    def register(self, views, model=None, base_url=None, prefix=None):
        """Register views.

        Arguments:
        views -- views class, e.g. smarter.GenericViews

        Keyword arguments:
        model    -- model for views (overrides one defined in views class)
        base_url -- base url for views
        prefix   -- prefix in url names for urls resolver

        Returns: None
        """
        from django.db.models import Model

        if not model:
            model = views.model

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
        return [url(r['base_url'], include(r['views'](**r)._urls()))
            for r in self._registered]


class GenericViews(object):

    def __init__(self, **kwargs):
        options = getattr(self, 'options', {})
        defaults = getattr(self, 'defaults', {})

        self._actions = set(_baseconfig.keys()).union(defaults.keys()).union(options.keys())
        for action in self._actions:
            if re.match(r"^((get_|_|-).*|.*__.*)", action):
                raise InvalidAction("Invalid action name: %s" % action)

        if not kwargs['model']:
            raise Exception("No model specified for views!")

        self.model, self._delim, self._prefix = \
            kwargs['model'], kwargs['delim'], kwargs['prefix']

    def get_param(self, request_or_action, name):
        options = getattr(self, 'options', {})
        defaults = getattr(self, 'defaults', {})
        action = getattr(request_or_action, _action, request_or_action)

        if action in options and name in options[action]:
            return options[action][name]
        elif action in defaults and name in defaults[action]:
            return defaults[action][name]
        else:
            return _baseconfig[action][name]

    def get_object(self, **kwargs):
        return get_object_or_404(self.model, **kwargs)

    def get_template(self, request_or_action):
        action = getattr(request_or_action, _action, request_or_action)
        return ('smarter/%s.html' % action,)

    def index(self, request):
        return {'objects_list': []}

    def index__form(self, request, **kwargs):
        pass

    def index__done(self, request, **kwargs):
        return render(request, self.get_template(request), kwargs)

    def details(self, request, **kwargs):
        return {'obj': self.get_object(**kwargs)}

    def details__form(self, request, **kwargs):
        pass

    def details__done(self, request, **kwargs):
        return render(request, self.get_template(request), kwargs)

    def add(self, request):
        pass

    def _urls(self):
        return [url(r'^' + self.get_param(action, 'url') + r'$',
                    self._view(action), name=self._url_name(action))
                for action in self._actions]

    def _url_name(self, action):
        return '%s%s%s' % (self._prefix, self._delim, action)

    def _pipeline(self, action):
        pipes = ('%s', '%s__perm', '%s__form', '%s__done')
        for pipe in pipes:
            if hasattr(self, pipe % action):
                yield getattr(self, pipe % action)
            else:
                yield getattr(self, pipe % '_pipe')

    def _pipe(self, request, **kwargs):
        obj = self.get_object(**kwargs)
        return {'obj': obj}

    def _pipe__perm(self, request, **kwargs):
        pass

    def _pipe__form(self, request, **kwargs):
        instance = kwargs.pop('obj', None)
        return {'form': None}

    def _pipe__done(self, request, **kwargs):
        if 'obj' in kwargs:
            try:
                return redirect(kwargs['obj'].get_absolute_url())
            except AttributeError:
                return redirect(request.get_full_path())
        elif 'form' in kwargs:
            kwargs['obj'] = getattr(kwargs['form'], 'instance', None)

        return render(request, self.get_template(request), kwargs)

    def _view(self, action):
        def inner(request, **kwargs):
            # return HttpResponse(action)
            setattr(request, _action, action)
            result = kwargs
            for pipe in self._pipeline(action):
                result = pipe(request, **result) or result
                if isinstance(result, HttpResponse):
                    return result
        return inner








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





