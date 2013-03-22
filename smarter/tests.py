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


class Tests(TestCase):
    urls = 'smarter.tests'

    def setUp(self):
        global urlpatterns
        self.client = Client()
        self.site = smarter.Site()

        self.site.register(smarter.GenericViews, TestModel)
        urlpatterns += patterns('', *self.site.urls)

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
        self.assertRedirects(r, '/testmodel/1/')
        self.assertEqual(TestModel.objects.get(pk=1).text, "Hahaha!")

        r = self.client.post('/testmodel/1/edit/', {'text': "Lalala!"})
        self.assertRedirects(r, '/testmodel/1/')
        self.assertEqual(TestModel.objects.get(pk=1).text, "Lalala!")





