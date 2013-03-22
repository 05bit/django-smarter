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
        Test with client requests.
        """
        self._test_url('/testmodel/')
        self._test_url('/testmodel/add/')

        self._test_url('/testmodel/1/', 404)
        TestModel.objects.create(text='Lalala!')
        self._test_url('/testmodel/1/')
        self._test_url('/testmodel/1/edit/')
        self._test_url('/testmodel/1/remove/')

    def test_generic_views_write(self):
        r = self.client.post('/testmodel/add/', {'text': 'Hahaha!'})
        self.assertEqual(r.status_code, 302)






