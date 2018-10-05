#!/usr/bin/env python3

from setuptools import setup, find_packages

setup(
    name = "dbd",
    version = "0.1",
    packages = find_packages(),
    include_package_data=True,
    entry_points = {
        'console_scripts': [
            'dbd = dbd.dbd:main'
        ]
    },

    install_requires = ['docker', 'pyyaml'],

    # metadata to display on PyPI
    author="Daniel Becker",
    author_email="daniel.becker@cloudera.com",
    description="Dockerised Big Data cluster.",
    license="Apache License 2.0",
    keywords="dockerised big data cluster hadoop oozie integration testing",
    url="https://github.com/d-becker/dbd"
)
