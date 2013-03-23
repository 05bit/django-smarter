import smarter
from .models import Page, PageFile

class PageViews(smarter.GenericViews):
    model = Page

    options = {
        'add': {
            'redirect': lambda view, request, **kwargs: view.get_url('index')
        },
        'edit': {
            'exclude': ('owner',),
            'redirect': lambda view, request, **kwargs: kwargs['obj'].get_absolute_url()
        }
    }

class PageFileViews(smarter.GenericViews):
    model = PageFile

    options = {
        'edit': None,
        'details': None,
        'add': {
            'redirect': lambda view, request, **kwargs: view.get_url('index')
        }
    }