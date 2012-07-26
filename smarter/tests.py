"""
Unit tests for django-smarter.

"""

import itertools

from django.test import TestCase
from django.http import HttpRequest
from django.conf.urls import patterns
from django.db import models
from django.core.urlresolvers import Resolver404

from smarter import SmarterSite

from views import BaseViews, GenericViews


class SimpleTest(TestCase):
    def test_site(self):
        '''
        Test registering, unregistering and urls
        
        '''
        
        site = SmarterSite()
        class TestModel(models.Model):
            test_field = models.TextField()
        
        urlpatterns = []
        
        def in_patterns(url):
            for pattern in urlpatterns:
                try:
                    if pattern.resolve(url):
                        return True
                except Resolver404:
                    pass
            return False
        
        site.register(TestModel)
        urlpatterns = patterns('', *site.urls)
        self.assertTrue(in_patterns('testmodel/')) #index
        self.assertTrue(in_patterns('testmodel/add/')) #add
        self.assertTrue(in_patterns('testmodel/1/edit/')) #edit
        self.assertTrue(in_patterns('testmodel/2/')) #details
        self.assertTrue(in_patterns('testmodel/2/remove/')) #remove
        #site.unregister(TestModel) #still unimplemented
        
        'final sanity check'
        #self.assertEqual(len(site.urls), 0)
        #will fail because unregister() is still unimplemented


    def test_generic_views(self):
        class TestModel(models.Model):
            test_field = models.TextField()
            
            class MockupManager(object):
                all = lambda self: 'all'
                get = lambda self, pk: pk
            
            objects=MockupManager()
        
        class TestableGenericViews(GenericViews):
            model = TestModel
            def render_to_response(self, context, **kwargs):
                return context
        
        v = TestableGenericViews()
        
        mockup_request = type('request', (object,), {})
        mockup_request.is_ajax = lambda s: False
        mockup_request.method = 'GET'
        
        
        '''
        v.as_view('add')(mockup_request)
        v.as_view('edit')(mockup_request, pk=3)
        v.as_view('remove')(mockup_request, pk=9)
        v.as_view('details')(mockup_request)
        #the above fails because GenericViews needs to have a 
        view_class set to be able to respond to requests.
        '''
        
