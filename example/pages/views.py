import smarter
from .models import Page

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