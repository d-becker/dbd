#!/usr/bin/env python

"""
This function merges xml files.

The code is copied from https://stackoverflow.com/a/11315257.

"""

import sys
from xml.etree import ElementTree

def run(files):
    """
    Merges the element trees of a list of xml
    files and writes the output to stdout.

    Note: Do not redirect stdout to an input file, use a temporary instead.

    Args:
        files: A list of filenames of xml files.

    """

    first = None
    for filename in files:
        data = ElementTree.parse(filename).getroot()
        if first is None:
            first = data
        else:
            first.extend(data)
    if first is not None:
        print(ElementTree.tostring(first).decode())

if __name__ == "__main__":
    run(sys.argv[1:])
