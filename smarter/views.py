#-*- coding: utf-8 -*-
from django.core import serializers
from django.core.exceptions import PermissionDenied
from django.core.serializers.json import DjangoJSONEncoder
from django.conf.urls.defaults import patterns
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
        try:
            view_method = getattr(self.view_class, view_method_name)
        except AttributeError:
            view_method = getattr(self.view_class, 'process_form')
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
    def as_urls(cls, name_prefix=None):
        """
        Returns all url patterns defined in urls_base()
        ans urls_custom().

        URSs names are prefixed with ``name_prefix``.
        """
        self = cls()
        self.view_class = cls
        self.name_prefix = name_prefix
        urlpatterns = patterns('')
        for u in [self.urls_base(), self.urls_custom()]:
            if u: urlpatterns += u
        return urlpatterns

    def urls_base(self):
        """
        Define generic urls here. Method should return
        list or tuple of url definitions.
        """
        raise NotImplementedError

    def urls_custom(self):
        """
        Define custom urls here. Method should return
        list or tuple of url definitions.
        """
        return None

    def url(self, schema, action):
        """
        Returns url definition by schema and action.
        """
        from django.conf.urls.defaults import url
        return url(schema, self.as_view(action), name=self.url_name(action))
    
    def url_name(self, action):
        return ''.join((self.name_prefix, action))

    ### Permissions

    def check_permissions(self, **kwargs):
        """
        Will raise django.core.exceptions.PermissionDenied exception if
        action not allowed. By default does nothing.
        """
        pass

    def deny(self):
        """
        Shortcut for raising PermissionDenied.
        """
        raise PermissionDenied

    ### Response
    
    def get_template_names(self):
        raise NotImplementedError
    
    def update_context(self, context):
        return context

    def render_to_json(self, context, **kwargs):
        if isinstance(context, (dict, list)):
            r = simplejson.dumps(context, cls=DjangoJSONEncoder)
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

    options = {}

    ### URLs

    @classmethod
    def as_urls(cls, model=None, name_prefix=None):
        self = cls()
        self.model = model or cls.model
        self.view_class = cls
        self.name_prefix = name_prefix or '%s-%s-' % (
            self.model._meta.app_label,
            self.model._meta.object_name.lower())
        urlpatterns = patterns('')
        for u in [self.urls_base(), self.urls_custom()]:
            if u: urlpatterns += u
        return urlpatterns

    def urls_base(self):
        return (self.url(r'^$', 'index'),
                self.url(r'^add/$', 'add'),
                self.url(r'^(?P<pk>\d+)/$', 'details'),
                self.url(r'^(?P<pk>\d+)/edit/$', 'edit'),
                self.url(r'^(?P<pk>\d+)/remove/$', 'remove'))

    ### Form creator

    def get_form(self, action, **kwargs):
        options = self.options.get(action, {})
        form_class = options.get('form', ModelForm)
        if issubclass(form_class, ModelForm):
            modeloptions = {}
            for k in ('fields', 'exclude', 'formfield_callback'):
                modeloptions[k] = options.get(k, None)
            modeloptions['form'] = form_class
            form_class = modelform_factory(model=self.model, **modeloptions)
        form = form_class(**kwargs)
        widgets = options.get('widgets', {})
        for k,v in widgets.items():
            form.fields[k].widget = v
        help_text = options.get('help_text', {})
        for k,v in help_text.items():
            form.fields[k].help_text = v
        return form

    ### Generic form processing
    
    def get_form_params(self):
        params_method = 'form_params_%s' % self.action.replace('-', '_')
        if hasattr(self, params_method):
            return getattr(self, params_method)()
        return {}
    
    def save_form(self, form):
        return form.save()

    def process_form(self, request, *args, **kwargs):
        """
        Generic form processing: render form on GET request
        and validate/save form on POST request.

        After successful form saving <action>_success()
        callback is invoked.
        """
        form_params = self.get_form_params()
        self.check_permissions(**form_params)
        if request.method == 'POST':
            form = self.get_form(action=self.action,
                                data=request.POST,
                                files=request.FILES,
                                **form_params)
            if form.is_valid():
                result = self.save_form(form)
                return self._process_form_success(request, result)
        else:
            form = self.get_form(action=self.action, **form_params)
        context = {'form': form}
        return self.render_to_response(context)

    def _process_form_success(self, request, result):
        """
        Invoke form processing callback <action>_success().

        Arguments:

            1. ``request``
            2. ``result`` is ``save_form()`` method result.
        """
        success_method = '%s_success' % self.action.replace('-', '_')
        if hasattr(self, success_method):
            return getattr(self, success_method)(request, result)
        else:
            if request.is_ajax():
                return self.render_to_json({'status': 'OK'})
            else:
                # TODO: design decision required
                return redirect(result.get_absolute_url())

    ### Add view

    def add_view(self, request, *args, **kwargs):
        form_params = self.get_form_params()
        self.check_permissions(**form_params)
        if request.method == 'POST':
            form = self.get_form(action=self.action,
                                data=request.POST,
                                files=request.FILES,
                                **form_params)
            if form.is_valid():
                instance = self.save_form(form)
                return self.add_success(request, instance)
        else:
            form = self.get_form(action=self.action, **form_params)
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
        form_params = self.get_form_params()
        self.check_permissions(**form_params)
        if request.method == 'POST':
            form = self.get_form(action=self.action,
                                data=request.POST,
                                files=request.FILES,
                                **form_params)
            if form.is_valid():
                instance = self.save_form(form)
                return self.edit_success(request, instance)
        else:
            form = self.get_form(action=self.action, **form_params)
        context = {'form': form}
        if hasattr(form,'instance'):
            context['obj'] = form.instance
        return self.render_to_response(context)

    def edit_success(self, request, instance):
        if request.is_ajax():
            return self.render_to_json({'status': 'OK'})
        else:
            return redirect(instance.get_absolute_url())

    def form_params_edit(self):
        pk = self.kwargs['pk']
        try:
            instance = self.get_object(pk)
        except self.model.DoesNotExist:
            instance = None
        return {'instance': instance}

    ### Index view
    
    def get_objects_list(self):
        return self.model.objects.all()

    def index_view(self, request):
        self.check_permissions()
        objects_list = self.get_objects_list()
        return self.render_to_response({'objects_list': objects_list})

    ### Object view
    
    def get_object(self, pk):
        try:
            return self.get_objects_list().get(pk=pk)
        except self.model.DoesNotExist:
            raise Http404
    
    def details_view(self, request, *args, **kwargs):
        pk = self.kwargs['pk']
        obj = self.get_object(pk)
        self.check_permissions(obj=obj)
        return self.render_to_response({'obj': obj})

    ### Remove view

    def remove_view(self, request, *args, **kwargs):
        pk = self.kwargs['pk']
        obj = self.get_object(pk)
        self.check_permissions(obj=obj)
        if request.method == 'POST':
            self.remove_object(obj)
            return self.remove_success(request, obj)
        else:
            return self.render_to_response({'obj': obj})

    def remove_success(self, request, obj):
        if request.is_ajax():
            return self.render_to_json({'status': 'OK'})
        else:
            return redirect('../..')
    
    def remove_object(self, obj):
        obj.delete()
    
    ### Template names

    def update_context(self, context):
        model_title = self.model._meta.verbose_name.title()
        model_title_plural = self.model._meta.verbose_name_plural.title()
        context.update({
            'model_title': model_title,
            'model_title_plural': model_title_plural,
        })
        return context

    def get_template_names(self):
        app = self.model._meta.app_label
        model = self.model._meta.object_name.lower()
        action = self.action
        return ['%s/%s_%s.html' % (app, model, action),
                '%s_%s.html' % (model, action),
                'smarter/%s.html' % action]


