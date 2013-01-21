# -*- coding: utf-8 -*-
"""Setup file for easy installation"""
from os.path import join, dirname
from setuptools import setup

version = '0.5'

LONG_DESCRIPTION = """
Django application for smarter application building.
"""

def long_description():
    """Return long description from README.rst if it's present
    because it doesn't get installed."""
    try:
        return open(join(dirname(__file__), 'README.rst')).read()
    except IOError:
        return LONG_DESCRIPTION

setup(name='django-smarter',
      version=version,
      author='Alexey Kinyov',
      author_email='rudy@05bit.com',
      description='Django application for smarter application building.',
      license='BSD',
      keywords='django, application, scaffolding',
      url='https://github.com/05bit/django-smarter',
      packages=['smarter',],
      long_description=long_description(),
      install_requires=['Django>=1.3',],
      classifiers=['Development Status :: 4 - Beta',
                   'Operating System :: OS Independent',
                   'License :: OSI Approved :: BSD License',
                   'Intended Audience :: Developers',
                   'Environment :: Web Environment',
                   'Programming Language :: Python :: 2.5',
                   'Programming Language :: Python :: 2.6',
                   'Programming Language :: Python :: 2.7'])
