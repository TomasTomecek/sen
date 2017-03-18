#!/usr/bin/env python3

import os

from setuptools import setup, find_packages

requirements = [
    "urwid",
    "urwidtrees",
    "docker"
]

setup(
    name='sen',
    version='0.5.1',
    description="Terminal User Interface for Docker Engine",
    author='Tomas Tomecek',
    author_email='tomas@tomecek.net',
    url="https://github.com/TomasTomecek/sen/",
    license="MIT",
    entry_points={
        'console_scripts': ['sen=sen.cli:main'],
    },
    packages=find_packages(exclude=["*.tests", "*.tests.*", "tests.*", "tests"]),
    install_requires=requirements,
    classifiers=['Development Status :: 5 - Production/Stable',
                 'Intended Audience :: Developers',
                 'Intended Audience :: System Administrators',
                 'License :: OSI Approved :: MIT License',
                 'Operating System :: POSIX :: Linux',
                 'Programming Language :: Python :: Implementation :: CPython',
                 'Programming Language :: Python :: 3',
                 'Programming Language :: Python :: 3 :: Only',
                 'Programming Language :: Python :: 3.4',
                 'Topic :: System :: Monitoring',
                 ],
)
