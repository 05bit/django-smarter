"""
Unit tests for django-smarter.
"""
import itertools
from django.test import TestCase
from django.http import HttpRequest
from django.conf.urls import patterns, include, url
from django.db import models
from django.core.urlresolvers import Resolver404
from django.test.client import Client
import smarter
from views import BaseViews, GenericViews

urlpatterns = patterns('',)


def in_patterns(url):
    for pattern in urlpatterns:
        try:
            if pattern.resolve(url):
                return True
        except Resolver404:
            pass
    return False


class SimpleTest(TestCase):
    urls = 'smarter.tests'

    def setUp(self):
        global urlpatterns
        self.client = Client()
        self.site = smarter.Site()

        class TestModel(models.Model):
            text = models.TextField()

        self.site.register(smarter.GenericViews, TestModel)
        urlpatterns += patterns('', *self.site.urls)

    def _test_url(self, url, status=200):
        self.assertEqual(self.client.get(url).status_code, status)

    def test_site_urls_registering(self):
        """
        Test registering and unregistering urls.
        """
        self.assertTrue(in_patterns('testmodel/')) # index
        self.assertTrue(in_patterns('testmodel/add/')) # add
        self.assertTrue(in_patterns('testmodel/1/edit/')) # edit
        self.assertTrue(in_patterns('testmodel/2/')) # details
        self.assertTrue(in_patterns('testmodel/2/remove/')) # remove
        self.assertTrue(not in_patterns('testmodel/lalala/')) # no such url

        #site.unregister(TestModel) #still unimplemented
        #self.assertEqual(len(site.urls), 0)
        #will fail because unregister() is still unimplemented

    def test_generic_views_by_url(self):
        """
        Test with client requests.
        """
        self._test_url('/testmodel/')
        self._test_url('/testmodel/add/')
        self._test_url('/testmodel/1/')
        self._test_url('/testmodel/1/edit/')
        self._test_url('/testmodel/1/remove/')
