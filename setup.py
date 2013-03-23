# -*- coding: utf-8 -*-
"""Setup file for easy installation"""
from os.path import join, dirname
from setuptools import setup

version = '1.0b'

LONG_DESCRIPTION = """
Smarter declarative style generic views for Django.
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
      description='Smarter declarative style generic views for Django.',
      license='BSD',
      keywords='django, application, scaffolding, crud, views, utility',
      url='https://github.com/05bit/django-smarter',
      packages=['smarter',],
      include_package_data=True,
      long_description=long_description(),
      install_requires=['Django>=1.4',],
      classifiers=['Development Status :: 4 - Beta',
                   'Operating System :: OS Independent',
                   'License :: OSI Approved :: BSD License',
                   'Intended Audience :: Developers',
                   'Environment :: Web Environment',
                   'Programming Language :: Python :: 2.5',
                   'Programming Language :: Python :: 2.6',
                   'Programming Language :: Python :: 2.7'])
