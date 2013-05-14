import smarter
from .models import Page

class PageTestViews(smarter.GenericViews):
    'for test_automatic_view_discovery'
    model = Page

smarter.site.register(PageTestViews, base_url='autodiscovery-test/', prefix='autodiscovery-test')

