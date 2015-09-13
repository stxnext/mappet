# -*- coding: utf-8 -*-

u"""Helper functions.

.. :module: helpers
   :synopsis: Helper functions.
"""
import datetime

from collections import defaultdict
from functools import partial

from lxml import etree

import dateutil.parser


__all__ = [
    'to_bool',
    'to_date',
    'to_datetime',
    'to_float',
    'to_int',
    'to_str',
    'to_time',

    'from_bool',
    'from_date',
    'from_datetime',
    'from_time',

    'CAST_DICT',
    'normalize_tag',
    'etree_to_dict',
    'dict_to_etree',
]


def no_empty_value(func):
    """Raises an exception if function argument is empty."""
    def wrapper(value):
        if not value:
            raise Exception("Empty value not allowed")
        return func(value)
    return wrapper


def to_bool(value):
    """Converts human boolean-like values to Python boolean.

    Falls back to :class:`bool` when ``value`` is not recognized.

    :param value: the value to convert
    :returns: ``True`` if value is truthy, ``False`` otherwise
    :rtype: bool
    """
    cases = {
        '0': False,
        'false': False,
        'no': False,

        '1': True,
        'true': True,
        'yes': True,
    }
    value = value.lower() if isinstance(value, basestring) else value
    return cases.get(value, bool(value))


def to_str(value):
    u"""Represents values as unicode strings to support diacritics."""
    return unicode(value)


def to_int(value):
    return int(value)


def to_float(value):
    return float(value)


@no_empty_value
def to_time(value):
    value = str(value)
    # dateutil.parse has problems parsing full hours without minutes
    sep = value[2:3]
    if not (sep == ':' or sep.isdigit()):
        value = value[:2] + ':00' + value[2:]

    return dateutil.parser.parse(value).time()


@no_empty_value
def to_datetime(value):
    value = str(value)
    return dateutil.parser.parse(value)


@no_empty_value
def to_date(value):
    value = str(value)
    return dateutil.parser.parse(value)


def from_bool(value):
    cases = {
        True: 'YES',
        False: 'NO',
    }
    try:
        return cases.get(value, bool(value))
    except Exception:
        return False


def from_time(value):
    if not isinstance(value, datetime.time):
        raise Exception('Value {} is not datetime.time object'.format(value))

    return value.isoformat()


@no_empty_value
def from_datetime(value):
    if not isinstance(value, datetime.datetime):
        raise Exception('Unexpected type {} of value {} (expected datetime.datetime)'.format(type(value), value))

    if value.tzinfo is None:
        value = value.replace(tzinfo=dateutil.tz.tzlocal())  # pragma: nocover
    return value.replace(microsecond=0).isoformat()


@no_empty_value
def from_date(value):
    if not isinstance(value, datetime.date) and not isinstance(value, datetime.datetime):
        raise Exception('Not datetime.date object but {}: {}'.format(type(value), value))

    return value.isoformat()


CAST_DICT = {
    bool: from_bool,
    int: str,
    str: str,
    unicode: str,
    float: str,
    datetime.time: from_time,
    datetime.datetime: from_datetime,
    datetime.date: from_date,
}


def normalize_tag(tag):
    u"""Normalizes tag name.

    :param str tag: tag name to normalize
    :rtype: str
    :returns: normalized tag name

    >>> normalize_tag('tag-NaMe')
    'tag_name'
    """
    return tag.lower().replace('-', '_')


def etree_to_dict(t, trim=True, **kw):
    u"""Converts an lxml.etree object to Python dict.

    >>> etree_to_dict(etree.Element('root'))
    {'root': None}

    :param etree.Element t: lxml tree to convert
    :returns d: a dict representing the lxml tree ``t``
    :rtype: dict
    """
    d = {t.tag: {} if t.attrib else None}
    children = list(t)

    if children:
        dd = defaultdict(list)
        for dc in map(partial(etree_to_dict, trim=trim, **kw), children):
            for k, v in dc.iteritems():
                # do not add Comment instance to the key
                if k is not etree.Comment:
                    dd[k].append(v)
        d = {t.tag: {k: v[0] if len(v) == 1 else v for k, v in dd.iteritems()}}

    if t.attrib:
        d[t.tag].update(('@' + k, v) for k, v in t.attrib.iteritems())
    if trim and t.text:
        t.text = t.text.strip()
    if t.text:
        if t.tag is etree.Comment and not kw.get('without_comments'):
            # adds a comments node
            d['#comments'] = t.text
        elif children or t.attrib:
            d[t.tag]['#text'] = t.text
        else:
            d[t.tag] = t.text
    return d


def dict_to_etree(d, root):
    u"""Converts a dict to lxml.etree object.

    >>> dict_to_etree({'root': {'#text': 'node_text', '@attr': 'val'}}, etree.Element('root')) # doctest: +ELLIPSIS
    <Element root at 0x...>

    :param dict d: dict representing the XML tree
    :param etree.Element root: XML node which will be assigned the resulting tree
    :returns: Textual representation of the XML tree
    :rtype: str
    """
    def _to_etree(d, node):
        if d is None or len(d) == 0:
            return
        elif isinstance(d, basestring):
            node.text = d
        elif isinstance(d, dict):
            for k, v in d.items():
                assert isinstance(k, basestring)
                if k.startswith('#'):
                    assert k == '#text'
                    assert isinstance(v, basestring)
                    node.text = v
                elif k.startswith('@'):
                    assert isinstance(v, basestring)
                    node.set(k[1:], v)
                elif isinstance(v, list):
                    # No matter the child count, their parent will be the same.
                    sub_elem = etree.SubElement(node, k)

                    for child_num, e in enumerate(v):
                        if e is None:
                            if child_num == 0:
                                # Found the first occurrence of an empty child,
                                # skip creating of its XML repr, since it would be
                                # the same as ``sub_element`` higher up.
                                continue
                            # A list with None element means an empty child node
                            # in its parent, thus, recreating tags we have to go
                            # up one level.
                            # <node><child/></child></node> <=> {'node': 'child': [None, None]}
                            _to_etree(node, k)
                        else:
                            # If this isn't first child and it's a complex
                            # value (dict), we need to check if it's value
                            # is equivalent to None.
                            if child_num != 0 and not (isinstance(e, dict) and not all(e.values())):
                                # At least one child was None, we have to create
                                # a new parent-node, which will not be empty.
                                sub_elem = etree.SubElement(node, k)
                            _to_etree(e, sub_elem)
                else:
                    _to_etree(v, etree.SubElement(node, k))
        elif etree.iselement(d):
            # Supports the case, when we got an empty child and want to recreate it.
            etree.SubElement(d, node)
        else:
            raise AttributeError('Argument is neither dict nor basestring.')

    _to_etree(d, root)
    return root
