import os
from setuptools import setup


execfile(os.path.join(os.path.abspath(os.path.dirname(__file__)),
                      'doctor', '_version.py'))

setup(
    name='doctor',
    version=__version__,  # noqa -- flake8 should ignore this line
    description=('A module that assists in using JSON schemas to validate data '
                 'in Flask APIs and generate API documentation.'),
    url='https://github.com/upsight/doctor',
    license='MIT',
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
    ],
    keywords=['python', 'flask', 'json', 'jsonschema', 'validation',
              'documentation', 'sphinx'],
    author='Upsight',
    author_email='dev@upsight.com',
    packages=[
        'doctor',
        'doctor.docs',
        'doctor.utils',
    ],
    install_requires=[
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
            'nose >= 1.3.7, < 2.0.0',
            'nose-exclude >= 0.5.0, < 1.0.0',
        ],
    },
)
