RELEASING
=========

When a release is ready, use the following steps to release the new version:

1. Bump the version number in `_version.py <https://github.com/upsight/doctor/blob/master/doctor/_version.py#L1>`_
2. Update the `CHANGELOG <https://github.com/upsight/doctor/blob/master/CHANGELOG.rst>`_ with the changes for this release.
3. Tag the release.  ``git tag -a -m "v1.3.0" "v1.3.0"; git push --tags``
4. Upload the release to `pypi <https://pypi.python.org/pypi/doctor>`_.  You will need to upload the source and wheel versions.  This can be done with distutils.
   Visit `this link <https://packaging.python.org/guides/migrating-to-pypi-org/#uploading>`_ for information on creating your `.pypirc` file.

.. code-block:: bash

    $ python3 setup.py sdist upload -r pypi
    ...
    Submitting dist/doctor-1.3.0.tar.gz to https://upload.pypi.org/legacy/
    Server response (200): OK
    $ python3 setup.py bdist_wheel upload -r pypi
    ...
    Submitting dist/doctor-1.3.0-py2-none-any.whl to https://upload.pypi.org/legacy/
    Server response (200): OK

