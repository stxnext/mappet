# -*- coding: utf-8 -*-

u"""Module for dynamic mapping of XML trees to Python objects.

.. :module: mappet
   :synopsis: Module for dynamic mapping of XML trees to Python objects.
"""

from copy import deepcopy
from lxml import etree

import re

import helpers

__all__ = [
    'Literal',
    'Mappet',
    'Node',
]


class Node(object):
    u"""Base class representing an XML node."""

    #: The lxml object representing parsed XML.
    _xml = None

    def __init__(self, xml):
        self._xml = xml

    def __repr__(self):
        u"""Represent an XML node as a string with child count.

        >>> xml = etree.Element('root')
        >>> xml.set('attr1', 'val1')
        >>> _ = etree.SubElement(xml, 'child')
        >>> repr(Node(xml))
        '<root attr1="val1"> (1)'
        """
        return '<{tagname}{attributes}{closing_paren}> ({children})'.format(
            tagname=self._xml.tag,
            attributes=''.join(
                [' {}="{}"'.format(
                    attr,
                    self._xml.attrib[attr]
                ) for attr in self._xml.attrib]
            ),
            closing_paren='' if len(self._xml) else '/',
            children=len(self._xml)
        )

    def __getitem__(self, key):
        u"""Call to a list element.

        Only calls to node attributes (i.e. starting with `@`) or
        text nodes (starting with `#`) are allowed.

        >>> xml = etree.Element('root')
        >>> xml.set('attr1', 'val1')
        >>> _ = etree.SubElement(xml, 'child')
        >>> Node(xml)[0]
        Traceback (most recent call last):
        ...
        KeyError: 0
        >>> Node(xml)['@attr1']
        'val1'
        """
        if isinstance(key, basestring) and (key.startswith('@') or key.startswith('#')):
            return self.getattr(key[1:])

        raise KeyError(key)

    def getattr(self, key, default=None, callback=None):
        u"""Getting the attribute of an element.

        >>> xml = etree.Element('root')
        >>> xml.text = 'text'
        >>> Node(xml).getattr('text')
        'text'
        >>> Node(xml).getattr('text', callback=str.upper)
        'TEXT'
        >>> Node(xml).getattr('wrong_attr', default='default')
        'default'
        """
        value = self._xml.text if key == 'text' else self._xml.get(key, default)
        return callback(value) if callback else value

    def setattr(self, key, value):
        u"""Sets an attribute on a node.

        >>> xml = etree.Element('root')
        >>> Node(xml).setattr('text', 'text2')
        >>> Node(xml).getattr('text')
        'text2'
        >>> Node(xml).setattr('attr', 'val')
        >>> Node(xml).getattr('attr')
        'val'
        """
        if key == 'text':
            self._xml.text = str(value)
        else:
            self._xml.set(key, str(value))


class Literal(Node):
    u"""Represents a leaf in an XML tree."""

    def __str__(self):
        u"""Represents a leaf as a str.

        Returns node's text as a string, if it's not None."""
        return str(self.get())

    #: Represents the leaf as unicode.
    __unicode__ = __str__

    def __repr__(self):
        u"""Represents the leaf as its textual value."""
        return str(self)

    def __int__(self):
        u"""Represents the literal as an int."""
        return self.to_int()

    def __float__(self):
        u"""Represents the literal as an float."""
        return self.to_float()

    def __nonzero__(self):
        u"""Represents the literal as an bool."""
        return True if self._xml.text else False

    def __eq__(self, other):
        u"""Compares two leafs.

        Assumes they are equal if the same are their:
            * tagname,
            * parent,
            * text,
            * attributes,
            * position among parent's children.
        """
        self_parent = self._xml.getparent()
        other_parent = other._xml.getparent()

        is_same_tag = self._xml.tag == other._xml.tag
        is_same_parent = self_parent == other_parent
        is_same_text = str(self) == str(other)
        are_attrs_equal = (self._xml.attrib == other._xml.attrib)
        is_same_position = self_parent.index(self._xml) == other_parent.index(other._xml)

        return all((
            is_same_tag,
            is_same_parent,
            is_same_text,
            are_attrs_equal,
            is_same_position,
        ))

    def __hash__(self):
        return hash(self._xml)

    def __len__(self):
        u"""Returns the length of node's text."""
        return len(self._xml.text)

    def __dir__(self):
        u"""Lists available casting methods."""
        return sorted(set([fnc for fnc in helpers.__all__ if fnc.startswith('to_')]))

    def __getattr__(self, name):
        u"""Returns a function for converting node's value.

        A leaf has no children, thus accessing its attributes returns a function.
        """
        if name.startswith('to_') and name in dir(helpers):
            fn = getattr(helpers, name)
            return lambda: fn(self._xml.text)
        raise AttributeError(name)

    def __setitem__(self, key, value):
        u"""Attribute assignment by dict access.

        Extending the leaf in this case is not possible, since a string is returned.
        """
        if isinstance(key, basestring) and (key.startswith('@') or key.startswith('#')):
            self.setattr(key[1:], value)

    def __add__(self, other):
        u"""String concatenation."""
        return self.to_str() + str(other)

    def __radd__(self, other):
        u"""Reverse string concatenation."""
        return str(other) + self.to_str()

    def get(self, default=None, callback=None):
        u"""Returns leaf's value."""
        value = self._xml.text if self._xml.text else default
        return callback(value) if callback else value


class _NoneNode(object):
    u"""None like object with converting methods."""

    _mocked_functions = filter(lambda f: f.startswith('to_'), dir(helpers)) + ['to_dict']

    def __new__(cls, *args, **kwargs):
        u"""Singleton.

        Recipe 6.15 by Jurgen Hermann.
        """
        if '_inst' not in vars(cls):
            cls._inst = super(type, cls).__new__(cls, *args, **kwargs)
        return cls._inst

    def __repr__(self):
        return 'NoneNode'

    def __nonzero__(self):
        return False

    def __dir__(self):
        u"""Lists available casting methods."""
        return sorted(set(self._mocked_functions))

    def __getattr__(self, name):
        u"""Returns mocked function for converting node's value."""
        if name in self._mocked_functions:
            return lambda: None
        raise AttributeError(name)


NoneNode = _NoneNode()


class Mappet(Node):
    u"""A node that may have children."""

    _aliases = None
    u"""Dictionary with node aliases.

    The keys are normalized tagnames, values are the original tagnames.
    _aliases = {
        'car_model_desc': 'car-model-desc',
        'car': 'Car',
    }
    """

    def __init__(self, xml):
        u"""Creates the mappet object from either lxml object, a string or a dict.

        If you pass a dict without root element, one will be created for you with
        'root' as tag name.

        >>> Mappet({'a': {'#text': 'list_elem_1', '@attr1': 'val1'}}).to_str()
        '<a attr1="val1">list_elem_1</a>'
        >>> Mappet({'#text': 'list_elem_1', '@attr1': 'val1'}).to_str()
        '<root attr1="val1">list_elem_1</root>'
        """
        if etree.iselement(xml):
            self._xml = xml
        elif isinstance(xml, basestring):
            self._xml = etree.fromstring(xml)
        elif isinstance(xml, dict):
            if len(xml) == 1:
                root_name = xml.keys()[0]
                body = xml[root_name]
            else:
                root_name = 'root'
                body = xml
            self._xml = helpers.dict_to_etree(body, etree.Element(root_name))
        else:
            raise AttributeError('Specified data cannot be used to construct a Mappet object.')

    def __nonzero__(self):
        u"""Checks if this node has children, otherwise returns False."""
        return self.has_children()

    def __len__(self):
        u"""Returns the children count."""
        return len(self._xml)

    def __dir__(self):
        u"""Returns a list of children and available helper methods."""
        children = set(self._get_aliases().keys())
        return sorted(children | {m for m in dir(self.__class__) if m.startswith('to_')})

    def __deepcopy__(self, memodict={}):
        u"""Performs a deepcopy on the underlying XML tree."""
        return self.__class__(deepcopy(self._xml))

    def __getattr__(self, name):
        u"""Attribute access.

        Returns a list o children, if there is more than 1.
        Returns a child, if there is exactly 1.
        """
        children = self.children(name)

        if len(children) > 1:
            return children
        elif len(children) == 1:
            return children[0]

    def __setattr__(self, name, value):
        u"""Node attribute assignment.

        Calls ``set`` in the end.
        """
        # Only elements that aren't a part of class definition are overwritten.
        if name not in dir(self.__class__):
            return self.set(name, value)

        return super(Mappet, self).__setattr__(name, value)

    def __delattr__(self, name):
        u"""Node removal."""
        # Searches among aliases, if none is found returns the original name.
        tag = self._get_aliases().get(name, name)

        # Checks if name is not a part of class definition.
        if tag not in dir(self.__class__):
            # Removes all children with a given tagname.
            for child in self._xml.iterchildren(tag=tag):
                self._xml.remove(child)

    def __getitem__(self, key):
        u"""Dictionary access."""
        # Checks if the call isn't to an attribute.
        if isinstance(key, basestring) and not key.startswith('@'):
            children = self.children(key, exact=True)

            if len(children) == 1:
                children = children[0]

            # Return the value if it's a leaf.
            if isinstance(children, Literal):
                return children.get()

            return children

        return super(Mappet, self).__getitem__(key)

    def __delitem__(self, key):
        u"""Removes a node through dictionary access."""
        # Checks if name is not a part of class definition.
        if key not in dir(self.__class__):
            for child in self._xml.iterchildren(tag=key):
                self._xml.remove(child)

    def __eq__(self, other):
        u"""Compares mappet objects.

        Two mappet objects are deemed equal if the lxmls object they represent are equal.
        """
        return etree.tostring(self._xml) == etree.tostring(other._xml)

    def __contains__(self, path):
        u"""Check if object contains given path."""
        elem = self.sget(path)
        return not (elem is None or elem is NoneNode)

    def __getstate__(self):
        u"""Converts the lxml to string for Pickling."""
        return {
            '_xml': etree.tostring(self._xml, pretty_print=False)
        }

    def __setstate__(self, dict_):
        u"""Restores a Pickled mappet object."""
        self._xml = etree.fromstring(dict_['_xml'])

    def __iter__(self):
        u"""Returns children as an iterator."""
        return self.iter_children()

    def to_str(self, pretty_print=False, encoding=None, **kw):
        u"""Converts a node with all of it's children to a string.

        Remaining arguments are passed to etree.tostring as is.

        :param bool pretty_print: whether to format the output
        :param str encoding: which encoding to use (ASCII by default)
        :rtype: str
        :returns: node's representation as a string
        """
        return etree.tostring(self._xml, pretty_print=pretty_print, encoding=encoding, **kw)

    def has_children(self):
        u"""Returns true if a node has children."""
        return bool(len(self))

    def iter_children(self, key=None, exact=False):
        u"""Iterates over children.

        :param key: A key for filtering children by tagname.
        :param exact: A flag to disable searching among aliases.
        """
        tag = None
        if key:
            tag = key if exact else self._get_aliases().get(key, None)
            if not tag:
                raise KeyError(key)
        for child in self._xml.iterchildren(tag=tag):
            if len(child):
                yield self.__class__(child)
            else:
                yield Literal(child)

    def children(self, key=None, exact=False):
        u"""Returns node's children.

        :param key: A key for filtering children by tagname.
        :param exact: A flag to disable searching among aliases.
        """
        return list(self.iter_children(key, exact))

    def update(self, **kwargs):
        u"""Updating or creation of new simple nodes.

        Each dict key is used as a tagname and value as text.
        """
        for key, value in kwargs.items():
            helper = helpers.CAST_DICT.get(type(value), helpers.from_str)
            tag = self._get_aliases().get(key, key)

            elements = list(self._xml.iterchildren(tag=tag))
            if elements:
                for element in elements:
                    element.text = helper(value)
            else:
                element = etree.Element(key)
                element.text = helper(value)
                self._xml.append(element)
                self._aliases = None

    def sget(self, path, default=NoneNode):
        u"""Enables access to nodes if one or more of them don't exist.

        Example:
        >>> m = Mappet('<root><tag attr1="attr text">text value</tag></root>')
        >>> m.sget('tag')
        text value
        >>> m.sget('tag.@attr1')
        'attr text'
        >>> m.sget('tag.#text')
        'text value'
        >>> m.sget('reply.vms_model_cars.car.0.params.doors')
        NoneNode

        Accessing nonexistent path returns None-like object with mocked
        converting functions which returns None:
        >>> m.sget('reply.fake_node').to_dict() is None
        True
        """
        attrs = str(path).split(".")
        text_or_attr = None
        last_attr = attrs[-1]
        # Case of getting text or attribute
        if last_attr == '#text' or last_attr.startswith('@'):
            # #text => text, @attr => attr
            text_or_attr = last_attr[1:]
            attrs = attrs[:-1]
            # When getting #text and @attr we want default value to be None.
            if default is NoneNode:
                default = None

        my_object = self
        for attr in attrs:
            try:
                if isinstance(my_object, (list, tuple)) and re.match('^\-?\d+$', attr):
                    my_object_next = my_object[int(attr)]
                else:
                    my_object_next = getattr(my_object, attr)
                my_object = my_object_next
            except (AttributeError, KeyError, IndexError):
                return default

        # Return #text or @attr
        if text_or_attr:
            try:
                return my_object.getattr(text_or_attr)
            except AttributeError:
                # myObject can be a list.
                return None
        else:
            return my_object

    def create(self, tag, value):
        u"""Creates a node, if it doesn't exist yet.

        Unlike attribute access, this allows to pass a node's name with hyphens.
        Those hyphens will be normalized automatically.

        In case the required element already exists, raises an exception.
        Updating/overwriting should be done using `update``.
        """
        child_tags = {child.tag for child in self._xml}

        if tag in child_tags:
            raise KeyError('Node {} already exists in XML tree.'.format(tag))

        self.set(tag, value)

    def set(self, name, value):
        u"""Assigns a new XML structure to the node.

        A literal value, dict or list can be passed in. Works for all nested levels.

        Dictionary:
        >>> m = Mappet('<root/>')
        >>> m.head = {'a': 'A', 'b': {'#text': 'B', '@attr': 'val'}}
        >>> m.head.to_str()
        '<head><a>A</a><b attr="val">B</b></head>'

        List:
        >>> m.head = [{'a': i} for i in 'ABC']
        >>> m.head.to_str()
        '<head><a>A</a><a>B</a><a>C</a></head>'

        Literals:
        >>> m.head.leaf = 'A'
        >>> m.head.leaf.get()
        'A'
        """
        try:
            # Searches for a node to assign to.
            element = next(self._xml.iterchildren(tag=name))
        except StopIteration:
            # There is no such node in the XML tree. We create a new one
            # with current root as parent (self._xml).
            element = etree.SubElement(self._xml, name)

        if isinstance(value, dict):
            self.assign_dict(element, name, value)
        elif isinstance(value, (list, tuple, set)):
            self.assign_sequence_or_set(element, name, value)
        else:
            # Literal value.
            self.assign_literal(element, name, value)

        # Clear the aliases.
        self._aliases = None

    def assign_dict(self, element, tag_name, value):
        new_element = etree.Element(tag_name)
        # Replaces the previous node with the new one.
        self._xml.replace(element, new_element)

        # Copies #text and @attrs from the dict.
        helpers.dict_to_etree(value, new_element)

    def assign_sequence_or_set(self, element, tag_name, value):
        element.clear()

        for item in value:
            temp_element = etree.Element('temp')
            helpers.dict_to_etree(item, temp_element)
            for child in temp_element.iterchildren():
                element.append(child)
            del temp_element

    def assign_literal(self, element, tag_name, value):
        u"""Assigns a literal.

        If a given node doesn't exist, it will be created.

        :param etree.Element element: element to which we assign.
        :param string tag_name: element name, if it itself doesn't exists.
        :param value: the value to assign
        """
        # Searches for a conversion method specific to the type of value.
        helper = helpers.CAST_DICT.get(type(value), helpers.from_str)

        # Removes all children and attributes.
        element.clear()
        element.text = helper(value)

    def to_dict(self):
        u"""Converts the lxml object to a dict."""
        _, value = helpers.etree_to_dict(self._xml).popitem()
        return value

    def _get_aliases(self):
        u"""Creates a dict with aliases.

        The key is a normalized tagname, value the original tagname.
        """
        if self._aliases is None:
            self._aliases = {}

            if self._xml is not None:
                for child in self._xml.iterchildren():
                    self._aliases[helpers.normalize_tag(child.tag)] = child.tag

        return self._aliases
