# -*- coding: utf-8 -*-
"""
Some utils for working on real vectors stored as dictionaries
Author: Stéphane Nicolet
"""

import math
import copy


### Helper functions

def norm2(m):
    """
    Return the L2-norm of the point m
    """
    s = 0.0
    for (name, value) in m.items():
        s += value['value'] ** 2
    return math.sqrt(s)


def norm1(m):
    """
    Return the L1-norm of the point m
    """
    s = 0.0
    for (name, value) in m.items():
        s += abs(value['value'])
    return s


def linear_combinaison(alpha = 1.0, m1 = {},
                       beta = None, m2 = {}):
    """
    Return the linear combinaison m = alpha * m1 + beta * m2.
    """
    if m2 == {}:
        m2 = copy.deepcopy(m1)
        beta = 0.0

    m = copy.deepcopy(m1)
    for (name, value) in m1.items():
        val = alpha * value['value'] + beta * m2[name]['value']
        m[name]['value'] = val

    return m


def difference(m1, m2):
    """
    Return the difference m = m1 - m2.
    """
    return linear_combinaison(1.0, m1, -1.0, m2)


def sum(m1, m2):
    """
    Return the sum m = m1 + m2.
    """
    return linear_combinaison(1.0, m1, 1.0, m2)


def hadamard_product(m1, m2):
    """
    Return a vector where each entry is the product of the corresponding
    entries in m1 and m2
    """
    m = {}
    for (name, value) in m1.items():
        m[name] = value * m2.get(name, 0.0)

    return m


def regulizer(m, lambd , alpha):
    """
    Return a regulizer r = lamdb * ((1 - alpha) * norm1(m) + alpha * norm2(m))
    Useful to transform non-convex optimization problems into pseudo-convex ones
    """
    return lambd * ((1 - alpha) * norm1(m) + alpha * norm2(m))


def sign_of(x):
    """
    The sign function for a real or integer parameter
    Return -1, 0 or 1 depending of the sign of x
    """
    return (x and (1, -1)[x < 0])


def sign(m):
    """
    Return a vector filled by the signs of m, component by component
    """
    result = {}
    for (name, value) in m.items():
        result[name] = sign_of(value)

    return result

def sqrt(m):
    """
    Return a vector filled by the square roots of m, component by component
    """
    result = {}
    for (name, value) in m.items():
        result[name] = math.sqrt(value)

    return result

def copy_and_fill(m, v):
    """
    Return a vector with the same component as m, filled with v
    """
    result = {}
    for (name, foo) in m.items():
        result[name] = v

    return result

def pretty(m):
    """
    Return a string representation of m
    """
    s = "{ "
    for name in sorted(m):
        s += name + " ="
        if m[name] >= 0: s += " "
        s += str("%.4f" % m[name]) + "; "
    s += "}"

    return s

def apply_limits(m, is_factor=True):
    """
    Set the value of a dict to a maximum if it is more than max.
    Set the value of a dict to a minimum if it is below min.

    m is a dict of dict. Example:
    {'queen_opening': {'value': 950, 'min': 700, 'max': 1200, 'factor': 1000},
    'rook_opening': {'value': 500, 'min': 300, 'max': 600, 'factor': 1000}}

    :param m: a dict of dict
    :return: updated m
    """
    for k, v in m.items():
        factor = v['factor']
        val = v['value']
        if is_factor:
            minv, maxv = v['min']/factor, v['max']/factor
        else:
            minv, maxv = v['min'], v['max']
        if val < minv:
            m[k]['value'] = minv
        if val > maxv:
            m[k]['value'] = maxv

    return m


def true_param(m):
    # Todo: Determine if original param value is a float or integer.
    # Now it is assumed that it is integer.
    ret = copy.deepcopy(m)
    for k, v in m.items():
        ret[k]['value'] = int(m[k]['value'] * m[k]['factor'])

    return ret
