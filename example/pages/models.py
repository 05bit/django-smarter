from django.db import models
from django.core.urlresolvers import reverse

class Page(models.Model):
    owner = models.ForeignKey('auth.User')
    title = models.CharField(max_length=100)
    text = models.TextField()

    def __unicode__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('page-details', kwargs={'pk': self.pk})
