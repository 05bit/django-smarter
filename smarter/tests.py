"""
Unit tests for django-smarter.
"""
from django.conf.urls import patterns, include, url
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import resolve, reverse, Resolver404
from django.http import HttpResponse
from django.db import models
from django.test import TestCase
from django.test.client import Client
import smarter

# Custom urls for tests
urlpatterns = patterns('',)


def handler404(request):
    """Custom 404 handler for tests."""
    from django.http import HttpResponseNotFound
    return HttpResponseNotFound('Not found: %s' % request.path)


class TestModel(models.Model):
    """Model for tests."""
    text = models.TextField()

    def get_absolute_url(self):
        return ('/test/testmodel/%s/' % self.pk)


class AnotherTestModel(models.Model):
    """Well, another model for tests."""
    text = models.TextField()

    def get_absolute_url(self):
        return ('/test/testmodel/%s/' % self.pk)


class TestViews(smarter.GenericViews):
    options = {
        'details-extended': {
            'url': r'(?P<pk>\d+)/extended/',
            'template': 'details_extended.html',
            'form': None,
        },

        'decorated': {
            'url': r'(?P<pk>\d+)/decorated/',
            'form': None,
            'decorators': (login_required,),
        },

        'protected': {
            'url': r'(?P<pk>\d+)/protected/',
            'form': None,
            'permissions': ('smarter.view_testmodel',)
        }
    }


class Tests(TestCase):
    urls = 'smarter.tests'

    def setUp(self):
        self.client = Client()
        self.site = smarter.Site()
        self.site.register(TestViews, TestModel)
        TestModel.objects.create(id=1, text='The first object.')

        global urlpatterns
        if not len(urlpatterns):
            urlpatterns += patterns('', url(r'^test/', include(self.site.urls)),)

    def _test_url(self, url, status=200):
        self.assertEqual(self.client.get(url).status_code, status)

    def test_site_urls_registering(self):
        """
        Test registering and unregistering urls.
        """
        self.assertTrue(resolve('/test/testmodel/')) # index
        self.assertTrue(resolve('/test/testmodel/add/')) # add
        self.assertTrue(resolve('/test/testmodel/1/edit/')) # edit
        self.assertTrue(resolve('/test/testmodel/2/')) # details
        self.assertTrue(resolve('/test/testmodel/2/remove/')) # remove
        try:
            self.assertTrue(resolve('/test/testmodel/lalala/')) # no such url
        except Resolver404:
            pass

        #site.unregister(TestModel) #still unimplemented
        #self.assertEqual(len(site.urls), 0)
        #will fail because unregister() is still unimplemented

    def test_urls_reversing(self):
        reverse('testmodel-index')
        reverse('testmodel-add')
        reverse('testmodel-edit', kwargs={'pk': 1})
        reverse('testmodel-remove', kwargs={'pk': 1})
        reverse('testmodel-details', kwargs={'pk': 1})

    def test_generic_views_read(self):
        """
        Test views reading with client requests.
        """
        self._test_url('/test/testmodel/')
        self._test_url('/test/testmodel/add/')
        self._test_url('/test/testmodel/100/', 404)
        TestModel.objects.create(id=100, text='Lalala!')
        self._test_url('/test/testmodel/100/')
        self._test_url('/test/testmodel/100/edit/')
        self._test_url('/test/testmodel/100/remove/')

    def test_generic_views_write(self):
        """
        Test views writing with client requests.
        """
        r = self.client.post('/test/testmodel/add/', {'text': "Hahaha!"})
        self.assertRedirects(r, '/test/testmodel/2/')
        self.assertEqual(TestModel.objects.get(pk=2).text, "Hahaha!")

        r = self.client.post('/test/testmodel/2/edit/', {'text': "Lalala!"})
        self.assertRedirects(r, '/test/testmodel/2/')
        self.assertEqual(TestModel.objects.get(pk=2).text, "Lalala!")

    def test_custom_views_read(self):
        from django.template import TemplateDoesNotExist
        try:
            self._test_url('/test/testmodel/1/extended/')
            raise Exception("Template was found some way, but it should not!")
        except TemplateDoesNotExist:
            pass

    def test_decorated_view(self):
        with self.settings(LOGIN_URL='/test/testmodel/'):
            r = self.client.get('/test/testmodel/1/decorated/')
            self.assertRedirects(r, '/test/testmodel/?next=/test/testmodel/1/decorated/')

    def test_permissions(self):
        self._test_url('/test/testmodel/1/protected/', 403)
