#!/usr/bin/env python3

import os

from setuptools import setup, find_packages

# vcs+proto://host/path@revision#egg=project-version
# this is latest upstream commit (April 2017)
# upstream maintainer of urwidtrees doesn't maintain PyPI urwidtrees
urwidtrees_source = "git+https://github.com/pazz/urwidtrees.git@9142c59d3e41421ff6230708d08b6a134e0a8eed#egg=urwidtrees-1.0.3.dev"

requirements = [
    "urwid",
    "docker",
    "urwidtrees"
]

setup(
    name='sen',
    version='0.8.0',
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
    dependency_links=[urwidtrees_source],
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
