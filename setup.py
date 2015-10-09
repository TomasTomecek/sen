#!/usr/bin/python3


from setuptools import setup, find_packages


setup(
    name='sen',
    version='0.1',
    description="Terminal User Interface for Docker Engine",
    author='Tomas Tomecek',
    author_email='tomas@tomecek.net',
    url="https://github.com/TomasTomecek/sen/",
    license="MIT",
    entry_points={
        'console_scripts': ['sen=sen.cli:main'],
    },
    packages=find_packages(exclude=["*.tests", "*.tests.*", "tests.*", "tests"]),
    install_requires=("urwid", "humanize", "docker"),
)
