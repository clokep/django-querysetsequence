import codecs

from setuptools import setup, find_packages


def long_description():
    with codecs.open('README.rst', encoding='utf8') as f:
        return f.read()

setup(
    name='django-querysetsequence',
    packages=find_packages(),
    version='0.14',
    description='Chain together multiple (disparate) QuerySets to treat them as a single QuerySet.',
    long_description=long_description(),
    long_description_content_type='text/x-rst',
    author='Patrick Cloke',
    author_email='clokep@patrick.cloke.us',
    url='https://github.com/clokep/django-querysetsequence',
    download_url='https://github.com/clokep/django-querysetsequence',
    keywords=['django', 'queryset', 'chain', 'multi', 'multiple', 'iterable'],
    license='ISC',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Environment :: Web Environment',
        'Topic :: Internet',
        'Framework :: Django',
        'Framework :: Django :: 2.2',
        'Framework :: Django :: 3.0',
        'Framework :: Django :: 3.1',
        'Framework :: Django :: 3.2',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'License :: OSI Approved :: ISC License (ISCL)',
    ],
    install_requires=[
        'django>=2.2',
    ],
    python_requires=">=3.6",
)
