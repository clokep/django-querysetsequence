import codecs

from setuptools import setup, find_packages


def long_description():
    with codecs.open('README.rst', encoding='utf8') as f:
        return f.read()

setup(
    name='django-querysetsequence',
    packages=find_packages(),
    version='0.11dev',
    description='Chain together multiple (disparate) QuerySets to treat them as a single QuerySet.',
    long_description=long_description(),
    author='Percipient Networks, LLC',
    author_email='support@strongarm.io',
    url='https://github.com/percipient/django-querysetsequence',
    download_url='https://github.com/percipient/django-querysetsequence',
    keywords=['django', 'queryset', 'chain', 'multi', 'multiple', 'iterable'],
    license='ISC',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Environment :: Web Environment',
        'Topic :: Internet',
        'Framework :: Django',
        'Framework :: Django :: 1.11',
        'Framework :: Django :: 2.0',
        'Framework :: Django :: 2.1',
        'Framework :: Django :: 2.2',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Framework :: Django',
        'License :: OSI Approved :: ISC License (ISCL)',
    ],
    install_requires=[
        'django>=1.11',
    ],
    python_requires=">=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*, !=3.4.*",
)
