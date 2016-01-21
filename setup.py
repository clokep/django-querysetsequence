import codecs

from setuptools import setup


def long_description():
    with codecs.open('README.rst', encoding='utf8') as f:
        desc = f.read()

    with codecs.open('CHANGELOG.rst', encoding='utf8') as f:
        changelog = f.read()

    return '%s\n\n%s' % (desc, changelog)

setup(
    name='django-querysetsequence',
    py_modules=['queryset_sequence'],
    version='0.2.4',
    description='Chain together multiple (disparate) QuerySets to treat them as a single QuerySet.',
    long_description=long_description(),
    author='Percipient Networks, LLC',
    author_email='support@strongarm.io',
    url='https://github.com/percipient/django-querysetsequence',
    download_url='https://github.com/percipient/django-querysetsequence',
    keywords=['django', 'queryset', 'chain', 'multi', 'multiple', 'iterable'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Environment :: Web Environment',
        'Topic :: Internet',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Framework :: Django',
        'License :: OSI Approved :: ISC License (ISCL)',
    ],
    install_requires=[
        'django>=1.8.0',
    ],
)
