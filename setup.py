#!/usr/bin/env python3

from setuptools import setup, find_packages

setup(
    name = "dbd",
    version = "0.1",
    packages = find_packages(),

    entry_points = {
        'console_scripts': [
            'dbd = dbd.dbd:main'
        ]
    },

    install_requires = ['docker', 'pyyaml'],

    # package_data={
    #     # If any package contains *.txt or *.rst files, include them:
    #     '': ['*.txt', '*.rst'],
    #     # And include any *.msg files found in the 'hello' package, too:
    #     'hello': ['*.msg'],
    # },

    # metadata to display on PyPI
    # author="Me",
    # author_email="me@example.com",
    # description="This is an Example Package",
    # license="PSF",
    # keywords="hello world example examples",
    # url="http://example.com/HelloWorld/",   # project home page, if any
    # project_urls={
    #     "Bug Tracker": "https://bugs.example.com/HelloWorld/",
    #     "Documentation": "https://docs.example.com/HelloWorld/",
    #     "Source Code": "https://code.example.com/HelloWorld/",
    # }

    # could also include long_description, download_url, classifiers, etc.
)
