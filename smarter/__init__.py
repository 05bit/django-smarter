#-*- coding: utf-8 -*-
"""
django-smarter
--------------

Copyright (c) 2013, Alexey Kinyov <rudy@05bit.com>
Licensed under MIT, see LICENSE for more details.
"""
import re
from django.conf.urls.defaults import patterns, include, url
from django.forms.models import modelform_factory, ModelForm
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
    'details': {
        'url': r'(?P<pk>\d+)/',
    },
    'add': {
        'url': r'add/',
        'redirect': (lambda view, request, **kw: kw['obj'].get_absolute_url()),
    },
    'edit': {
        'url': r'(?P<pk>\d+)/edit/',
        'redirect': (lambda view, request, **kw: kw['obj'].get_absolute_url()),
    },
    'remove': {
        'url': r'(?P<pk>\d+)/remove/',
        'redirect': '../',
    },
}

_action = '_action'


class Site(object):
    def __init__(self, prefix=None, delim='-'):
        """
        Creates site object.

        Keyword arguments:
        prefix  -- prefix for url names
        delim   -- delimiter for url names, can be '_', '-' or empty string
        """
        if not delim in ('-', '-', ''):
            raise Exception("Delimiter must be in '-', '_' or empty string.")
        self._prefix = prefix
        self._delim = delim
        self._registered = []

    def register(self, views, model=None, base_url=None, prefix=None):
        """Register views.

        Views added with `base_url` and every view gets named url
        with scheme: [site prefix]-[views prefix]-[action], e.g.:

            app-page-index
            app-page-add
            app-page-edit
            app-page-details
            etc.

        If `prefix` is not defined [views prefix] is set to model
        lowercase name.

        Arguments:
        views -- views class, e.g. smarter.GenericViews

        Keyword arguments:
        model    -- model for views (overrides one defined in views class)
        base_url -- base url for views
        prefix   -- prefix in url names for urls resolver

        Returns: None
        """
        from django.db.models import Model

        model = model or views.model
        if not model:
            raise Exception("Model is not specified, views must be registered for some model!")

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

        if base_url:
            base_url = '%s/' % (base_url.strip(' /') or model_name)
        else:
            base_url = '%s/' % model_name

        self._registered.append({
                'base_url': base_url,
                'prefix': self._delim.join(prefix_bits),
                'delim': self._delim,
                'model': model,
                'views': views,
            })

    @property
    def urls(self):
        """
        Site urls.
        """
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
            'smarter/_ajax.html',),
        'decorators': None,
    }

    def __init__(self, **kwargs):
        """
        Creates and initializes generic views handler. You should not
        call it directly, as views are created while registering
        ``Site.urls``.
        """
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
            try:
                return _baseconfig[action][name]
            except KeyError:
                pass

        return default

    def get_object(self, **kwargs):
        return get_object_or_404(self.model, **kwargs)

    def get_objects_list(self, request, **kwargs):
        return self.model.objects.filter(**kwargs)

    def get_initial(self, request):
        initial_fields, initial = self.get_param(request, 'initial'), {}
        if initial_fields:
            for f in initial_fields:
                if f in request.GET:
                    initial[f] = request.GET[f]
        return initial

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

        form_kwargs = kwargs.get('form', {})
        form_kwargs.setdefault('initial', self.get_initial(request))        
        if request.method == 'POST':
            form = form_class(request.POST, files=request.FILES, **form_kwargs)
        else:
            form = form_class(**form_kwargs)

        for k, v in (self.get_param(request, 'labels') or {}).items():
            form.fields[k].label = v
        for k, v in (self.get_param(request, 'widgets') or {}).items():
            form.fields[k].widget = v
        for k, v in (self.get_param(request, 'help_text') or {}).items():
            form.fields[k].help_text = v
        for k, v in (self.get_param(request, 'required') or {}).items():
            form.fields[k].required = v

        return form

    def deny(self, request, message=None):
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied

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
        pass

    def _urls(self):
        return [url(r'^' + self.get_param(action, 'url') + r'$',
                    self._view(action), name=self._url_name(action))
                for action in self._actions]

    def _url_name(self, action):
        return '%s%s%s' % (self._prefix, self._delim, action)

    def _pipeline(self, action):
        """
        View method pipeline.
        """
        pipes = ('%s', '%s__perm', '%s__form', '%s__ctxt', '%s__done')
        for pipe in pipes:
            method = pipe % action.replace('-', '_')
            if hasattr(self, method):
                yield getattr(self, method)
            else:
                yield getattr(self, pipe % '_pipe')

    def _pipe(self, request, **kwargs):
        """
        Default initial view method. Returns object and
        form parameters.
        """
        obj = self.get_object(**kwargs)
        return {'obj': obj, 'form': {'instance': obj}}

    def _pipe__perm(self, request, **kwargs):
        """
        Checks permissions.
        """
        perm = self.get_param(request, 'permissions')
        if perm and not request.user.has_perm(perm):
            return self.deny(request)

    def _pipe__form(self, request, **kwargs):
        """
        Creates and processes form.
        """
        form = self.get_form(request, **kwargs)
        if form:
            kwargs['form'] = form
            if form.is_bound and form.is_valid():
                kwargs['obj'] = self._pipe__save(request, **kwargs)
                kwargs['form_saved'] = True
            return kwargs
        else:
            kwargs.pop('form', None)
            return kwargs

    def _pipe__save(self, request, form=None, **kwargs):
        """
        Saves form.
        """
        return form.save()

    def _pipe__ctxt(self, request, **kwargs):
        """
        Extends render context.
        """
        pass

    def _pipe__done(self, request, **kwargs):
        """
        View processing done: redirect if ``form_saved is ``True`` or
        render template.
        """
        if kwargs.get('form_saved', False):
            redirect_path = self.get_param(request, 'redirect')
            if callable(redirect_path):
                return redirect(redirect_path(self, request, **kwargs))
            else:
                return redirect(redirect_path)
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
        
        for d in self.get_param(action, 'decorators') or ():
            inner = d(inner)

        return inner
