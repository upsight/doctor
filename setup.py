import os
from setuptools import setup

# Use exec so pip can get the version before installing the module
version_filename = os.path.abspath(os.path.join(
    os.path.dirname(__file__), 'doctor', '_version.py'))
with open(version_filename, 'r') as vf:
    exec(compile(vf.read(), version_filename, 'exec'), globals(), locals())

readme_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), 'README.rst'))
with open(readme_path, 'r') as fp:
    long_description = fp.read()

setup(
    name='doctor',
    version=__version__,  # noqa -- flake8 should ignore this line
    description=('This module uses python 3 type hints to validate request and '
                 'response data in Flask Python APIs and generate API '
                 'documentation.'),
    long_description=long_description,
    long_description_content_type='text/x-rst',
    url='https://github.com/upsight/doctor',
    license='MIT',
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.6',
    ],
    keywords=['python', 'flask', 'json', 'api', 'validation',
              'documentation', 'sphinx'],
    author='Upsight',
    author_email='dev@upsight.com',
    packages=[
        'doctor',
        'doctor.docs',
        'doctor.utils',
    ],
    install_requires=[
        'isodate >= 0.6.0, < 1.0.0',
        'jsonschema >= 2.5.1, < 3.0.0',
        'pyyaml >= 3.11, < 4.0',
        'rfc3987 >= 1.3.4, < 2.0.0',
        'simplejson >= 3.6.3, < 4.0.0',
        'strict-rfc3339 >= 0.5, < 1.0',
    ],
    extras_require={
        'docs': [
            'mock >= 2.0.0, < 3.0.0',
            'sphinx >= 1.5.4, < 2.0.0',
            'sphinx-autodoc-typehints >= 1.2.4, < 2.0.0',
            'sphinx-rtd-theme >= 0.2.4, < 1.0.0',
            'sphinxcontrib-httpdomain >= 1.5.0, < 2.0.0',
        ],
        'tests': [
            'coverage >= 4.4.1, < 5.0.0',
            'flake8 >= 3.3.0, < 4.0.0',
            'flask >= 0.10.1, < 1.0.0',
            'flask-restful==0.3.6',
            'Flask-Testing==0.6.2',
            'mock >= 2.0.0, < 3.0.0',
            'pytest >= 3.3.2, < 4.0.0',
        ],
    },
)
