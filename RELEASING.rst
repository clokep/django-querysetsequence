Releasing django-querysetsequence
=================================

1. Bump the version in ``setup.cfg``, ``CHANGELOG.rst``, and ``docs/conf.py``.
2. Double check the trove classifiers in ``setup.cfg`` (they should match the
   supported Python version in ``README.rst`` and ``tox.ini``).
3. Make a git commit.
4. Create a git tag: ``git tag <version>``
5. Build the package via ``python -m build``.
6. Run twine checks: ``twine check dist/*``
7. Upload to PyPI: ``twine upload dist/*``
