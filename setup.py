from setuptools import setup


setup(
    name='medlemssys',
    version='0.5',
    description='Membership register for norwegian youth organizations',
    license='AGPL',
    install_requires=[
        'Django>=1.7',
        'logan',
        'whitenoise',
        'django-model-utils',
        'pytz',
        'reportlab',
        'python-dateutil',
        'django-reversion >= 1.10',
        'django-reversion-compare < 0.7',
    ],
    extras_require={
        'production': [
            'django-gunicorn',
            'gunicorn',
            'raven',
        ],
    },
    entry_points={
        'console_scripts': [
            'medlemssys = medlemssys.runner:main',
        ],
    },
    packages=('medlemssys',)
)
