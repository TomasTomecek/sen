#!/usr/bin/python3


from setuptools import setup, find_packages


def get_requirements():
    path = 'requirements.txt'
    try:
        with open(path) as f:
            packages = f.read().splitlines()
    except (IOError, OSError) as ex:
        raise RuntimeError("Can't open file with requirements: %r", ex)
    return packages


setup(
    name='sen',
    version='0.1.1',
    description="Terminal User Interface for Docker Engine",
    author='Tomas Tomecek',
    author_email='tomas@tomecek.net',
    url="https://github.com/TomasTomecek/sen/",
    license="MIT",
    entry_points={
        'console_scripts': ['sen=sen.cli:main'],
    },
    packages=find_packages(exclude=["*.tests", "*.tests.*", "tests.*", "tests"]),
    install_requires=get_requirements()
)
