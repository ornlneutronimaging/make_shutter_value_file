#!/usr/bin/env python
from setuptools import setup, find_packages
import codecs


def read_file(filename):
    """
    Read a utf8 encoded text file and return its contents.
    """
    with codecs.open(filename, 'r', 'utf8') as f:
        return f.read()


setup(
    name="MakeShutterValueFile",
    version="0.0.1",
    author="Jean Bilheux",
    author_email="bilheuxjm@ornl.gov",
    packages=find_packages(exclude=['tests', 'notebooks']),
    # package_data={'MakeShutterValueFile': ['reference_data/_data_for_unittest/*']},
    include_package_data=True,
    test_suite='tests',
    install_requires=[
        'numpy',
    ],
    dependency_links=[
    ],
    description="tool to create ShutterValue.txt file used by MCP detector",
    long_description=read_file('README.rst'),
    license='BSD',
    keywords=['neutron', 'imaging', 'detector'],
    url="https://github.com/ornlneutronimaging/make_shutter_value_file.git",
    classifiers=['Development Status :: 3 - Alpha',
                 'License :: OSI Approved :: BSD License',
                 'Topic :: Scientific/Engineering :: Physics',
                 'Intended Audience :: Developers',
                 'Programming Language :: Python :: 3.5',
                 'Programming Language :: Python :: 3.6',
                 'Programming Language :: Python :: 3.7',
                 'Natural Language :: English'],
)
