# -*- coding: utf-8 -*-

from __future__ import print_function
from setuptools import setup
from setuptools.command.test import test as TestCommand
import io
import sys

import mappet


def read(*filenames, **kwargs):
    encoding = kwargs.get('encoding', 'utf-8')
    sep = kwargs.get('sep', '\n')
    buf = []
    for filename in filenames:
        with io.open(filename, encoding=encoding) as f:
            buf.append(f.read())
    return sep.join(buf)

long_description = read('README.rst')


class PyTest(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        import pytest
        errcode = pytest.main(self.test_args)
        sys.exit(errcode)


setup(
    name='mappet',
    version=mappet.__version__,
    url='https://github.com/stxnext/mappet',
    license='GNU Lesser General Public License v3(LGPLv3)',
    author='Radosław Szalski',
    tests_require=[
        'pytest',
    ],
    install_requires=[
        'lxml',
        'python-dateutil',
    ],
    cmdclass={'test': PyTest},
    author_email='radoslaw.szalski@gmail.com',
    description='Work with XML documents as if they were Python objects',
    long_description=long_description,
    packages=['mappet'],
    include_package_data=True,
    platforms='any',
    test_suite='mappet.tests',
    classifiers=[
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Development Status :: 3 - Alpha',
        'Natural Language :: English',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)',
        'Operating System :: OS Independent',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Text Processing :: Markup :: XML',
        'Topic :: Utilities',
    ],
    keywords='xml parsing mapping',
    extras_require={
        'testing': [
            'pytest',
            'mock',
            'tox',
        ],
    }
)
