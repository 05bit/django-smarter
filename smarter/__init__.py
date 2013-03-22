#-*- coding: utf-8 -*-
import re
import warnings
from django.conf.urls.defaults import patterns, include, url
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.forms.models import modelform_factory, ModelForm


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
        'template': None,
    },
    'details': {
        'url': r'(?P<pk>\d+)/',
        'template': None,
    },
    'add': {
        'url': r'add/',
        'initial': None,
        'form': None,
        'exclude': None,
        'fields': None,
        'labels': None,
        'widgets': None,
        'required': None,
        'help_text': None,
        'template': None,
    },
    'edit': {
        'url': r'(?P<pk>\d+)/edit/',
        'initial': None,
        'form': None,
        'exclude': None,
        'fields': None,
        'labels': None,
        'widgets': None,
        'required': None,
        'help_text': None,
        'template': None,
    },
    'remove': {
        'url': r'(?P<pk>\d+)/remove/',
        'initial': None,
        'form': None,
        'exclude': None,
        'fields': None,
        'labels': None,
        'widgets': None,
        'required': None,
        'help_text': None,
        'template': None,
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
    defaults = {
        'initial': None,
        'form': ModelForm,
        'exclude': None,
        'fields': None,
        'labels': None,
        'widgets': None,
        'required': None,
        'help_text': None,
        'template': (
            '%(app)s/%(model)s/%(action)s.html',
            '%(app)s/%(model)s/%(action)s.ajax.html',
            'smarter/%(action)s.html',
            'smarter/_form.html',
            'smarter/_ajax.html',)
    }

    def __init__(self, **kwargs):
        options = getattr(self, 'options', {})
        defaults = getattr(self, 'defaults', {})

        self._actions = set(_baseconfig.keys()).union(options.keys())
        for action in self._actions:
            if re.match(r"^((get_|_|-).*|.*__.*)", action):
                raise InvalidAction("Invalid action name: %s" % action)

        if not kwargs['model']:
            raise Exception("No model specified for views!")

        self.model, self._delim, self._prefix = \
            kwargs['model'], kwargs['delim'], kwargs['prefix']

    def get_param(self, request_or_action, name, default=None):
        options = getattr(self, 'options', {})
        defaults = getattr(self, 'defaults', {})
        action = getattr(request_or_action, _action, request_or_action)

        if not action in self._actions:
            raise Exception("No such action %s:" % action)

        if action in options and name in options[action]:
            return options[action][name]
        elif name in defaults:
            return defaults[name]
        elif action in _baseconfig:
            return _baseconfig[action][name]
        elif not default is None:
            return default
        else:
            raise Exception("Can't find option value: %s - %s" % (action, name))

    def get_object(self, **kwargs):
        return get_object_or_404(self.model, **kwargs)

    def get_objects_list(self, request, **kwargs):
        return self.model.objects.filter(**kwargs)

    def get_template(self, request_or_action, is_ajax=None):
        format = {
            'action': getattr(request_or_action, _action, request_or_action),
            'app': self.model._meta.app_label,
            'model': self.model._meta.object_name.lower(),
        }
        template = self.get_param(request_or_action, 'template')

        if isinstance(template, (str, unicode)):
            return template % format

        if is_ajax is None and hasattr(request_or_action, 'is_ajax'):
            is_ajax = request_or_action.is_ajax()
        def _filtered():
            for t in template:
                if ('ajax' in t) == bool(is_ajax):
                    yield t % format
        return list(_filtered())
        # def _sorted():
        #     for t in templates:
        #         if ('ajax' in t) == bool(is_ajax):
        #             yield t
        #     for t in templates:
        #         if (not 'ajax' in t) == bool(is_ajax):
        #             yield t
        # return list(_sorted())

    def get_form(self, request, **kwargs):
        from django.forms.models import modelform_factory, ModelForm
        
        form_options = {'form': self.get_param(request, 'form')}
        if form_options['form']:
            form_options.update({
                'exclude': self.get_param(request, 'exclude'),
                'fields': self.get_param(request, 'fields'),
            })
            form_class = modelform_factory(model=self.model, **form_options)
        else:
            return

        if request.method == 'POST':
            form = form_class(request.POST, files=request.FILES, **kwargs)
        else:
            form = form_class(**kwargs)

        for k, v in (self.get_param(request, 'labels') or {}).items():
            form.fields[k].label = v
        for k, v in (self.get_param(request, 'widgets') or {}).items():
            form.fields[k].widget = v
        for k, v in (self.get_param(request, 'help_text') or {}).items():
            form.fields[k].help_text = v
        for k, v in (self.get_param(request, 'required') or {}).items():
            form.fields[k].required = v

        return form

    def index(self, request, **kwargs):
        return {'objects_list': self.get_objects_list(kwargs)}

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
        initial_fields, initial = self.get_param(request, 'initial'), {}
        if initial_fields:
            for f in initial_fields:
                if f in request.GET:
                    initial[f] = request.GET[f]
        return {'initial': initial or None}

    def _urls(self):
        return [url(r'^' + self.get_param(action, 'url') + r'$',
                    self._view(action), name=self._url_name(action))
                for action in self._actions]

    def _url_name(self, action):
        return '%s%s%s' % (self._prefix, self._delim, action)

    def _pipeline(self, action):
        pipes = ('%s', '%s__perm', '%s__form', '%s__done')
        for pipe in pipes:
            method = pipe % action.replace('-', '_')
            if hasattr(self, method):
                yield getattr(self, method)
            else:
                yield getattr(self, pipe % '_pipe')

    def _pipe(self, request, **kwargs):
        obj = self.get_object(**kwargs)
        return {'obj': obj}

    def _pipe__perm(self, request, **kwargs):
        pass

    def _pipe__form(self, request, **kwargs):
        instance = kwargs.pop('obj', None)
        form = self.get_form(request, instance=instance, **kwargs)
        if form:
            if form.is_bound and form.is_valid():
                return {'form': form,
                        'obj': self._pipe__save(request, form, **kwargs)}
            else:
                return {'form': form}

    def _pipe__save(self, request, form, **kwargs):
        return form.save()

    def _pipe__done(self, request, **kwargs):
        if 'form' in kwargs:
            if 'obj' in kwargs:
                try:
                    return redirect(kwargs['obj'].get_absolute_url())
                except AttributeError:
                    return redirect(request.get_full_path())
            else:
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





