#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Medlemssys
==========

Medlemssys is a membership register.  Primarily written for norwegian youth
organizations, but can and is used by other kinds of organizations.

It doesn't do anything very advanced, but provides a way to list the members,
export to CSV, can read OCR-files, send emails and some more.

Installation
------------

Doing a simple install, you can install "medlemssys" for a test version, or
"medlemssys[production]" to get a few required extras for a real setup::

    pip install medlemssys[production]

You'll use the `medlemssys` command for all commands.  It's a small wrapper
around the django-admin command.  The first thing you'll want to do is to
create a settings file::

    medlemssys init

This will give you a `medlemssys_conf.py` file.  Have a look at it, and change
what you need.  You should load in the data to the database and create yourself
a user::

    medlemssys migrate
    medlemssys createsuperuser

If you chose the production setup, you can run gunicorn::

    export DJANGO_SETTINGS_MODULE=medlemssys_conf
    gunicorn --bind 0.0.0.0:8000 medlemssys.config.wsgi:application

You can of course also try the django development server to just test your
register::

    medlemssys runserver 0.0.0.0:8000

"""

from setuptools import setup
from setuptools import find_packages


setup(
    name='medlemssys',
    use_scm_version=True,
    description='Membership register for norwegian youth organizations',
    long_description=__doc__,
    license='AGPLv3+',
    author='Odin Hørthe Omdal',
    author_email='odin.omdal@gmail.com',
    url='https://github.com/odinho/medlemssys',
    install_requires=[
        'Django >= 1.7, < 1.10',
        'logan',
        'whitenoise',
        'django-model-utils',
        'pytz',
        'reportlab',
        'python-dateutil',
        'django-reversion >= 2.0',
        'django-reversion-compare >= 0.7',
    ],
    extras_require={
        'production': [
            'django-gunicorn',
            'gunicorn',
            'psycopg2',
            'raven',
        ],
    },
    setup_requires=['setuptools_scm'],
    entry_points={
        'console_scripts': [
            'medlemssys = medlemssys.runner:main',
        ],
    },
    packages=find_packages(),
    package_data={
        '': ['templates/*', 'templates/**/*', 'templates/**/**/*',
             'static/**', 'static/**/*'],
        'medlemssys.giro': ['OCRB.ttf'],
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: End Users/Desktop',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.7',
        'Topic :: Database :: Front-Ends',
        'Topic :: Office/Business',
    ],
)
