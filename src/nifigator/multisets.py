# -*- coding: utf-8 -*-

"""
"""

from fractions import Fraction
from collections import Counter


def jaccard_index(c1: set = None, c2: set = None):
    """
    Function to calculate the Jaccard index of two sets
    """
    denom = len(c1 | c2)
    if denom != 0:
        return Fraction(len(c1 & c2), denom)
    else:
        return 0


def containment_index(c1: set = None, c2: set = None):
    """
    Function to calculate the containment of set B in set A
    """
    denom = len(c1)
    if denom != 0:
        return Fraction(len(c1 & c2), denom)
    else:
        return 0


def merge_multiset(d: dict = None):
    """
    Function to calculate the multiset from a dict of phrases
    """
    x = Counter()
    for item in d.values():
        x += item
    return x
