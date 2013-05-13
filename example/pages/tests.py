from django.test import TestCase
from django.core.urlresolvers import reverse

class ProjectLevelSmarterTest(TestCase):
    def test_automatic_view_discovery(self):
        '''
        Testing the automatic view discovery
        '''
        self.assertEqual(reverse('autodiscovery-test-index'), '/autodiscovery-test/')
