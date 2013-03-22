"""
Unit tests for django-smarter.
"""
import itertools
from django.test import TestCase
from django.http import HttpResponse
from django.conf.urls import patterns, include, url
from django.db import models
from django.core.urlresolvers import Resolver404
from django.test.client import Client
import smarter
from views import BaseViews, GenericViews

# Custom urls for tests
urlpatterns = patterns('',)


def resolve(url):
    """Resolve url directly with test urlpatterns."""
    for pattern in urlpatterns:
        try:
            if pattern.resolve(url):
                return True
        except Resolver404:
            pass
    return False


def handler404(request):
    """Custom 404 handler for tests."""
    from django.http import HttpResponseNotFound
    return HttpResponseNotFound('Not found: %s' % request.path)


class TestModel(models.Model):
    """Well, model for tests."""
    text = models.TextField()

    def get_absolute_url(self):
        return ('/testmodel/%s/' % self.pk)


class TestViews(smarter.GenericViews):
    options = {
        'details-extended': {
            'url': r'(?P<pk>\d+)/extended/',
            'template': 'details_extended.html',
            'form': None,
        }
    }


class Tests(TestCase):
    urls = 'smarter.tests'

    def setUp(self):
        self.client = Client()
        self.site = smarter.Site()

        global urlpatterns
        self.site.register(TestViews, TestModel)
        urlpatterns += patterns('', *self.site.urls)

        TestModel.objects.create(id=1, text='The first object.')

    def _test_url(self, url, status=200):
        self.assertEqual(self.client.get(url).status_code, status)

    def test_site_urls_registering(self):
        """
        Test registering and unregistering urls.
        """
        self.assertTrue(resolve('testmodel/')) # index
        self.assertTrue(resolve('testmodel/add/')) # add
        self.assertTrue(resolve('testmodel/1/edit/')) # edit
        self.assertTrue(resolve('testmodel/2/')) # details
        self.assertTrue(resolve('testmodel/2/remove/')) # remove
        self.assertTrue(not resolve('testmodel/lalala/')) # no such url

        #site.unregister(TestModel) #still unimplemented
        #self.assertEqual(len(site.urls), 0)
        #will fail because unregister() is still unimplemented

    def test_generic_views_read(self):
        """
        Test views reading with client requests.
        """
        self._test_url('/testmodel/')
        self._test_url('/testmodel/add/')
        self._test_url('/testmodel/100/', 404)
        TestModel.objects.create(id=100, text='Lalala!')
        self._test_url('/testmodel/100/')
        self._test_url('/testmodel/100/edit/')
        self._test_url('/testmodel/100/remove/')

    def test_generic_views_write(self):
        """
        Test views writing with client requests.
        """
        r = self.client.post('/testmodel/add/', {'text': "Hahaha!"})
        self.assertRedirects(r, '/testmodel/2/')
        self.assertEqual(TestModel.objects.get(pk=2).text, "Hahaha!")

        r = self.client.post('/testmodel/2/edit/', {'text': "Lalala!"})
        self.assertRedirects(r, '/testmodel/2/')
        self.assertEqual(TestModel.objects.get(pk=2).text, "Lalala!")

    def test_custom_views_read(self):
        from django.template import TemplateDoesNotExist
        try:
            self._test_url('/testmodel/1/extended/')
            raise Exception("Template was found some way, but it should not!")
        except TemplateDoesNotExist:
            pass




