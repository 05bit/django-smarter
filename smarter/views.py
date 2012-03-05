#-*- coding: utf-8 -*-
from django.core import serializers
from django.forms.models import modelform_factory, ModelForm
from django.http import HttpResponse, Http404
from django.shortcuts import redirect, render_to_response, get_object_or_404
from django.views.generic.base import View, TemplateResponseMixin
from django.utils import simplejson
from django.utils.decorators import classonlymethod
from django.utils.functional import update_wrapper


class BaseViews(View, TemplateResponseMixin):
    """Base class for views.
    """

    model = None

    ### View factory method
    
    def as_view(self, action=None, **initkwargs):
        """Create class-based view instance for given ``action``.

        Each action corresponds to ``<action>_view`` method.
        """
        cls = self.view_class
        model = getattr(self, 'model', None)
        
        # validate action
        # if not action in cls.action_names:
        #     raise Exception("Unknown action! Your action name should"
        #                     "be in this list: %s" % str(cls.action_names))
                            
        # sanitize keyword arguments
        # (copy-paste from django/views/generic/base.py)
        for key in initkwargs:
            if key in cls.http_method_names:
                raise TypeError(u"You tried to pass in the %s method name as a "
                                u"keyword argument to %s(). Don't do that."
                                % (key, cls.__name__))
            if not hasattr(cls, key):
                raise TypeError(u"%s() received an invalid keyword %r" % (
                    cls.__name__, key))

        # construct view method        
        dispatch = getattr(cls, '%s_view' % action)
        def view(request, *args, **kwargs):
            handler = cls(action=action,
                        request=request,
                        model=model,
                        name_prefix=self.name_prefix,
                        **initkwargs)
            handler.args = args
            handler.kwargs = kwargs
            return dispatch(handler, request, *args, **kwargs)
            
        # take name and docstring from class
        # and possible attributes set by decorators
        # like csrf_exempt from dispatch
        # (copy-paste from django/views/generic/base.py)
        update_wrapper(view, cls, updated=())
        update_wrapper(view, dispatch, assigned=())
        
        return view

    ### URLs

    @classonlymethod
    def as_urls(cls, name_prefix=None, view_class=None):
        handler = cls()
        handler.view_class = view_class or cls
        handler.name_prefix = name_prefix
        return handler.urlpatterns
    
    def url_name(self, action):
        return '%s%s' % (self.name_prefix, action)

    @property
    def urlpatterns(self):
        raise NotImplemented
    
    def render_to_response(self, context):
        context = self.update_context(context)
        return super(BaseViews, self).render_to_response(context)
    
    def update_context(self, context):
        return context

    def render_to_json(self, context, **kwargs):
        if isinstance(context, (dict, list)):
            output = simplejson.dumps(context)
        else:
            output = serializers.serialize('json', context, **kwargs)
        return HttpResponse(output, mimetype="application/json")


class GenericViews(BaseViews):
    """Defines generic views for actions: 'add', 'edit', 'remove',
    'index', 'details'.

    Basic usage example::

        from myapp.models import MyModel
        from smarter.views import GenericViews

        urlpatterns += patterns('',
            url(r'^my_prefix/', include(GenericViews.as_urls(model=MyModel)))
        )
    """

    ### URLs

    @classonlymethod
    def as_urls(cls, model=None, name_prefix=None, view_class=None):
        handler = cls(model=model or cls.model)
        handler.view_class = view_class or cls
        if name_prefix:
            handler.name_prefix = name_prefix
        else:
            handler.name_prefix = '%s-%s-' % (
                        model._meta.app_label,
                        model._meta.object_name.lower(),
                    )
        return handler.urlpatterns

    @property
    def urlpatterns(self):
        from django.conf.urls.defaults import patterns, url, include
        # if hasattr(self, '_urlpatterns_cache'):
        #     return self._urlpatterns_cache
        urlpatterns = patterns('',
            url(r'^$',
                self.as_view('index'),
                name=self.url_name('index')),
            url(r'^add/$',
                self.as_view('add'),
                name=self.url_name('add')),
            url(r'^(?P<pk>\d+)/$',
                self.as_view('details'),
                name=self.url_name('details')),
            url(r'^(?P<pk>\d+)/edit/$',
                self.as_view('edit'),
                name=self.url_name('edit')),
            url(r'^(?P<pk>\d+)/remove/$',
                self.as_view('remove'),
                name=self.url_name('remove')),
        )
        # self._urlpatterns_cache = urlpatterns
        return urlpatterns

    ### Form creator

    def get_form(self, action, **kwargs):
        # pre-defined Form class
        if hasattr(self, 'form_class'):
            form_class = self.form_class.get(action, None)
        else:
            form_class = None
        # form options
        if hasattr(self, 'form_opts'):
            form_opts = self.form_opts.get(action, {})
        else:
            form_opts = {}
        # make form class
        if not form_class:
            modelform_opts = {}
            for k in ('fields', 'exclude', 'formfield_callback'):
                modelform_opts[k] = form_opts.get(k, None)
            modelform_opts['form'] = form_opts.get('form', ModelForm)
            form_class = modelform_factory(model=self.model, **modelform_opts)
        # create form instance
        form = form_class(**kwargs)
        widgets = form_opts.get('widgets', {})
        for k,v in widgets.items():
            form.fields[k].widget = v
        help_text = form_opts.get('help_text', {})
        for k,v in help_text.items():
            form.fields[k].help_text = v
        return form
        #return self.create_form(form_class, form_opts, **kwargs)
    
    def get_form_kwargs(self, action, request, *args, **kwargs):
        form_kwargs_func = getattr(self, 'get_form_kwargs_%s' % action, None)
        if callable(form_kwargs_func):
            return form_kwargs_func(request, *args, **kwargs)
        return {}
    
    def save_form(self, form):
        return form.save()
            
    # def create_form(self, form_class, form_opts, **kwargs):
    #     form = form_class(**kwargs)
    #     widgets = form_opts.get('widgets', {})
    #     for k,v in widgets.items():
    #         form.fields[k].widget = v
    #     help_text = form_opts.get('help_text', {})
    #     for k,v in help_text.items():
    #         form.fields[k].help_text = v
    #     return form
    
    ### Add view

    def add_view(self, request, *args, **kwargs):
        action = self.action
        form_kwargs = self.get_form_kwargs(action, request, *args, **kwargs)
        if request.method == 'POST':
            form = self.get_form(action=action,
                                data=request.POST,
                                files=request.FILES,
                                **form_kwargs)
            if form.is_valid():
                instance = self.save_form(form)
                return self.add_success(request, instance)
        else:
            form = self.get_form(action=action, **form_kwargs)
        context = {'form': form}
        return self.render_to_response(context)
    
    def add_success(self, request, instance):
        if request.is_ajax():
            return self.render_to_json({'status': 'DONE'})
        else:
            return redirect(instance.get_absolute_url())

    ### Edit view

    def get_form_kwargs_edit(self, request, *args, **kwargs):
        pk = self.kwargs['pk']
        try:
            instance = self.model.objects.get(pk=pk)
        except self.model.DoesNotExist:
            instance = None
        return {'instance': instance}

    def edit_view(self, request, *args, **kwargs):
        """
        Generic update view: get object by 'pk' and edit
        it using standard ModelForm.
        """
        action = self.action
        form_kwargs = self.get_form_kwargs(action, request, *args, **kwargs)
        if request.method == 'POST':
            form = self.get_form(action=action,
                                data=request.POST,
                                files=request.FILES,
                                **form_kwargs)
            if form.is_valid():
                instance = self.save_form(form)
                return self.edit_success(request, instance)
        else:
            form = self.get_form(action=action, **form_kwargs)
        context = {'form': form}
        return self.render_to_response(context)

    def edit_success(self, request, instance):
        if request.is_ajax():
            return self.render_to_json({'status': 'DONE'})
        else:
            return redirect(instance.get_absolute_url())

    ### Index view

    def index_view(self, request, *args, **kwargs):
        objects_list = self.model.objects.all()
        return self.render_to_response({'objects_list': objects_list})

    ### Object view

    def details_view(self, request, *args, **kwargs):
        pk = self.kwargs['pk']
        try:
            obj = self.model.objects.get(pk=pk)
        except self.model.DoesNotExist:
            raise Http404
        return self.render_to_response({'obj': obj})

    ### Remove view

    def remove_view(self, request, *args, **kwargs):
        pk = self.kwargs['pk']
        obj = get_object_or_404(self.model, pk=pk)
        if request.method == 'POST':
            obj.delete()
            return self.remove_success(request, obj)
        else:
            return self.render_to_response({'obj': obj})

    def remove_success(self, request, obj):
        if request.is_ajax():
            return self.render_to_json({'status': 'DONE'})
        else:
            return redirect('../..')
    
    ### Template names

    def get_template_names(self):
        return ['%s/%s_%s.html' % (
                    self.model._meta.app_label,
                    self.model._meta.object_name.lower(),
                    self.action),
                'smarter/%s.html' % self.action]


