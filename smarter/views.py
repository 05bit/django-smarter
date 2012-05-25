#-*- coding: utf-8 -*-
from django.core import serializers
from django.forms.models import modelform_factory, ModelForm
from django.http import HttpResponse, Http404
from django.shortcuts import redirect, render_to_response, get_object_or_404
from django.template.loader import select_template
from django.template import Context, RequestContext
from django.utils import simplejson
from django.utils.functional import update_wrapper


class BaseViews(object):
    """
    Base class for views. It doesn't implement any real
    urls or views.
    """

    model = None

    ### View factory method
    
    def as_view(self, action=None):
        """
        Create class-based view instance for given ``action``.
        Each action corresponds to ``<action>_view`` method.
        """
        view_method_name = '%s_view' % action.replace('-', '_')
        view_method = getattr(self.view_class, view_method_name)
        def view(request, *args, **kwargs):
            handler = self.view_class()
            handler.action = action
            handler.model = self.model
            handler.name_prefix = self.name_prefix
            handler.request = request
            handler.args = args
            handler.kwargs = kwargs
            return view_method(handler, request, *args, **kwargs)            
        # (copy-paste from django/views/generic/base.py)
        update_wrapper(view, self.view_class, updated=())
        update_wrapper(view, view_method, assigned=())        
        return view

    ### URLs

    @classmethod
    def as_urls(cls, name_prefix=None, view_class=None):
        handler = cls()
        handler.view_class = view_class or cls
        handler.name_prefix = name_prefix
        return handler.urls()

    def urls(self):
        from django.conf.urls.defaults import patterns
        urlpatterns = patterns('')
        for u in [self.urls_base(), self.urls_custom()]:
            if u: urlpatterns += u
        return urlpatterns

    def urls_base(self):
        raise NotImplemented

    def urls_custom(self):
        return None

    def url(self, schema, action):
        from django.conf.urls.defaults import url
        return url(schema, self.as_view(action), name=self.url_name(action))
    
    def url_name(self, action):
        return ''.join((self.name_prefix, action))

    ### Response
    
    def get_template_names(self):
        raise NotImplemented
    
    def update_context(self, context):
        return context

    def render_to_json(self, context, **kwargs):
        if isinstance(context, (dict, list)):
            r = simplejson.dumps(context)
        else:
            r = serializers.serialize('json', context, **kwargs)
        return HttpResponse(r, mimetype="application/json")

    def render_to_response(self, context, **kwargs):
        t = select_template(self.get_template_names())
        c = self.update_context(context)
        if not isinstance(c, Context):
            c = RequestContext(self.request, c)
        return HttpResponse(t.render(c), **kwargs)


class GenericViews(BaseViews):
    """
    Defines generic views for actions: 'add', 'edit', 'remove',
    'index', 'details'.

    Basic usage example::

        from myapp.models import MyModel
        from smarter.views import GenericViews

        urlpatterns += patterns('',
            url(r'^my_prefix/', include(GenericViews.as_urls(model=MyModel)))
        )
    """

    ### URLs

    @classmethod
    def as_urls(cls, model=None, name_prefix=None, view_class=None):
        handler = cls()
        handler.model = model or cls.model
        handler.view_class = view_class or cls
        handler.name_prefix = name_prefix or '%s-%s-' % (
            handler.model._meta.app_label,
            handler.model._meta.object_name.lower())
        return handler.urls()

    def urls_base(self):
        return (self.url(r'^$', 'index'),
                self.url(r'^add/$', 'add'),
                self.url(r'^(?P<pk>\d+)/$', 'details'),
                self.url(r'^(?P<pk>\d+)/edit/$', 'edit'),
                self.url(r'^(?P<pk>\d+)/remove/$', 'remove'))

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
    
    def get_form_params(self):
        params_method = 'form_params_%s' % self.action.replace('-', '_')
        if hasattr(self, params_method):
            return getattr(self, params_method)()
        return {}
    
    def save_form(self, form):
        return form.save()
    
    ### Add view

    def add_view(self, request, *args, **kwargs):
        action = self.action
        form_params = self.get_form_params()
        if request.method == 'POST':
            form = self.get_form(action=action,
                                data=request.POST,
                                files=request.FILES,
                                **form_params)
            if form.is_valid():
                instance = self.save_form(form)
                return self.add_success(request, instance)
        else:
            form = self.get_form(action=action, **form_params)
        context = {'form': form}
        return self.render_to_response(context)
    
    def add_success(self, request, instance):
        if request.is_ajax():
            return self.render_to_json({'status': 'OK'})
        else:
            return redirect(instance.get_absolute_url())

    ### Edit view

    def edit_view(self, request, *args, **kwargs):
        """
        Generic update view: get object by 'pk' and edit
        it using standard ModelForm.
        """
        action = self.action
        form_params = self.get_form_params()
        if request.method == 'POST':
            form = self.get_form(action=action,
                                data=request.POST,
                                files=request.FILES,
                                **form_params)
            if form.is_valid():
                instance = self.save_form(form)
                return self.edit_success(request, instance)
        else:
            form = self.get_form(action=action, **form_params)
        context = {'form': form}
        return self.render_to_response(context)

    def edit_success(self, request, instance):
        if request.is_ajax():
            return self.render_to_json({'status': 'OK'})
        else:
            return redirect(instance.get_absolute_url())

    def form_params_edit(self):
        pk = self.kwargs['pk']
        try:
            instance = self.model.objects.get(pk=pk)
        except self.model.DoesNotExist:
            instance = None
        return {'instance': instance}

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
            return self.render_to_json({'status': 'OK'})
        else:
            return redirect('../..')
    
    ### Template names

    def get_template_names(self):
        return ['%s/%s_%s.html' % (
                    self.model._meta.app_label,
                    self.model._meta.object_name.lower(),
                    self.action),
                'smarter/%s.html' % self.action]


