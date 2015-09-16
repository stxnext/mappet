# -*- coding: utf-8 -*-

# pylint: disable=invalid-name, line-too-long

u"""Unittests for the Mappet module.

.. :module: test_mappet
   :synopsis: Unittests for the Mappet module.
"""

from lxml import etree
import pytest

from mappet import mappet


class TestNode(object):
    u"""Unittests for the class representing base node."""

    def setup(self):
        xml = etree.Element('root')
        xml.set('attr1', 'val1')
        xml.set('attr2', 'val2')
        etree.SubElement(xml, 'node1')
        etree.SubElement(xml, 'node2')
        self.node = mappet.Node(xml)

    def test__repr__(self):
        u"""Tests the representation of node with children and attributes."""
        assert repr(self.node) == '<root attr1="val1" attr2="val2"> (2)'

    def test__repr__no_children(self):
        xml = etree.Element('root')
        xml.set('attr1', 'val1')
        node = mappet.Node(xml)
        assert repr(node) == '<root attr1="val1"/> (0)'

    def test__repr__no_attributes(self):
        xml = etree.Element('root')
        etree.SubElement(xml, 'node1')
        etree.SubElement(xml, 'node2')
        node = mappet.Node(xml)
        # A node without attributes, with children, should have the number of
        # children shown in parentheses, without the ending '/>'.
        assert repr(node) == '<root> (2)'

    def test__getitem__(self):
        u"""Tests for XML node attribute access."""
        # Values should be returned for all defined attributes.
        assert self.node['@attr1'] == 'val1'
        assert self.node['@attr2'] == 'val2'
        # Unicode strings are allowed.
        assert self.node[u'@attr2'] == 'val2'

    def test__getitem__wrong_notation(self):
        # Access to attributes without the use of '@' symbol should result in an error.
        with pytest.raises(KeyError):
            assert self.node['attr1'] == 'val1'

        # The key has to be a string.
        with pytest.raises(KeyError):
            assert self.node[{'hai!'}] == 'val1'

    def test_getattr(self):
        u"""Tests for a direct attribute access."""
        # For given attributes, returns their value, just as __getitem__ does.
        assert self.node.getattr('attr1') == 'val1'
        assert self.node.getattr('attr2') == 'val2'

    def test_getattr_wrong_attr(self):
        # If a given attribute doesn't exist, None is returned.
        assert self.node.getattr('non-existing-attr') is None

    def test_getattr_with_callback(self):
        u"""Tests for attribute access with callback."""
        # If a callback is supplied, it should be called on the attribute value.
        assert self.node.getattr('attr1', callback=str.upper) == 'VAL1'

    def test_getattr_default(self):
        u"""Tests for attribute access with a default value."""
        # If an attribute doesn't exist, returns the default value if supplied.
        assert self.node.getattr('non-existing-attr', 'default') == 'default'

    def test_setattr(self):
        self.node.setattr('val1', '1lav')
        self.node.setattr('new-attr', 'new-val')

        # A change to an existing attribute should be successful.
        assert self.node.getattr('val1') == '1lav'
        # A new attribute should be added, if id doesn't exist.
        assert self.node.getattr('new-attr') == 'new-val'

    def test_tag(self):
        # ``tag`` should return the tag's tagname
        assert self.node.tag == 'root'

    def test_is_key_attr_or_text__given_attr_key__should_return_true(self):
        assert self.node.is_key_attr_or_text('@this_is_an_attr_key')
        assert self.node.is_key_attr_or_text(u'@this_is_a_unicode_attr_key')

    def test_is_key_attr_or_text__given_text_key__should_return_true(self):
        assert self.node.is_key_attr_or_text('#this_is_a_text_key')
        assert self.node.is_key_attr_or_text(u'#this_is_a_unicode_text_key')

    def test_is_key_attr_or_text__given_neither_text_nor_attr_key__should_return_false(self):
        assert not self.node.is_key_attr_or_text('this_is_not_a_text_key')
        assert not self.node.is_key_attr_or_text(u'this_isnt_either')


class TestNoneNode(object):
    @pytest.fixture(scope='class')
    def none_node(self):
        return mappet.NONE_NODE

    def test__repr__(self, none_node):
        assert repr(none_node) == 'NONE_NODE'

    def test__nonzero__(self, none_node):
        assert bool(none_node) is False

    def test__dir__(self, none_node):
        assert dir(none_node) == [
            'to_bool',
            'to_date',
            'to_datetime',
            'to_dict',
            'to_float',
            'to_int',
            'to_str',
            'to_time',
        ]

    def test__getattr__given_existing_attr__should_return_none(self, none_node):
        assert none_node.to_bool() is None
        assert none_node.to_datetime() is None
        assert none_node.to_float() is None
        assert none_node.to_time() is None

    def test__getattr__given_nonexisting_attr__should_raise(self, none_node):
        with pytest.raises(AttributeError):
            none_node.to_infinity_and_beyond


class TestLiteral(object):
    u"""Tests for the class representing a XML leaf."""

    @pytest.fixture
    def literal(self):
        u"""Returns a simple Literal."""
        xml = etree.Element('root')
        literal_node = etree.SubElement(xml, 'literal_node')
        literal_node.text = 'literal-text'
        return mappet.Literal(literal_node)

    def test__str__(self, literal):
        u"""Tests for representing a leaf as a string."""
        # str() returns leaf's content as string.
        assert str(literal) == 'literal-text'

    def test__repr__(self, literal):
        u"""Tests for representing a leaf using __repr__."""
        # __repr__ returns a contents of a leaf.
        assert str(literal) == repr(literal)

    def test__unicode__(self, literal):
        u"""Tests for representing leaf's content as Unicode."""
        # unicode() returns contents of the leaf, just like str() does.
        assert unicode(literal) == 'literal-text'

    def test__int__(self, literal):
        u"""Tests conversion to int."""
        literal._xml.text = '1'
        assert int(literal) == 1

    def test__float__(self, literal):
        u"""Tests conversion to float."""
        literal._xml.text = '3.14'
        assert float(literal) == 3.14

    def test__nonzero__(self, literal):
        u"""Tests for representing a leaf as boolean."""
        # A leaf, which has any contents, should be truthy.
        assert bool(literal) is True

        # A leaf, which has no content, should be falsy.
        literal._xml.text = ''
        assert bool(literal) is False

    def test__eq__(self, literal):
        u"""Tests for equality of leafs."""
        assert mappet.Literal(literal._xml) == literal

    def test__hash__(self, literal):
        u"""Tests for hashing of leafs."""
        # A leaf's hash is a hash of XML structure it represents.
        assert hash(literal) == hash(literal._xml)

    def test__len__(self, literal):
        u"""Tests for leaf's text length"""
        # Leaf's length is its content's length.
        assert len(literal) == 12
        literal._xml.text = ''
        assert len(literal) == 0

    def test__dir__(self, literal):
        u"""Tests for listing of conversion methods available for leafs."""
        # dir() should return all the conversion methods (to_*) for leaves.
        assert dir(literal) == [
            'to_bool',
            'to_date',
            'to_datetime',
            'to_float',
            'to_int',
            'to_str',
            'to_time',
        ]

    def test__getattr__(self, literal):
        u"""Tests for conversion methods."""
        assert literal.to_str() == 'literal-text'

    def test_wrong__getattr__(self, literal):
        u"""Tests for calling non-existing conversion methods."""
        # If the method does not start with "to_", throws an exception.
        with pytest.raises(AttributeError):
            assert literal.my_helper() == 'node-text'

        # If a method starts with "to_", but does not exist in helpers module,
        # throws an exception.
        with pytest.raises(AttributeError):
            assert literal.to_unicode() == 'node-text'

    def test__setitem__(self, literal):
        u"""Tests for setting an attribute value."""
        literal['@attr'] = 'val'
        assert literal['@attr'] == 'val'

    def test_set_literal_text_explicitly(self):
        u"""Tests for assignment and extraction of leaf's text using '#text' key."""
        xml = '''<?xml version='1.0' encoding='iso-8859-2'?>
        <auth-request>
            <auth>
                <user type="admin" first-name="John" last-name="Johnny">123</user>
                <user type="admin" first-name="John" last-name="Johnny">123</user>
                <user type="editor" first-name="John" last-name="Johnny">123</user>
            </auth>
        </auth-request>'''

        m = mappet.Mappet(xml)

        # This is the only way to change leaf's text, that is returned by calling
        # 'user[1]'.
        m.auth.user[1]['#text'] = 'test'
        assert m.auth.user[1]['#text'] == 'test'
        assert m.auth.user[1].get() == 'test'

    def test__add__and__radd__(self, literal):
        u"""Tests for concatenation of leaves."""
        # A left join should return a full string.
        assert literal + 'sth' == 'literal-textsth'

        # A right join should also return a full string.
        assert 'sth' + literal == 'sthliteral-text'

    def test_get(self, literal):
        u"""Tests for extraction of leaves' values."""
        # A simple get() call should return the leaf's contents.
        assert literal.get() == 'literal-text'
        # If a callback was specified, it should have been used on the contents.
        assert literal.get(callback=str.upper) == 'LITERAL-TEXT'

    def test_get__simple_node_and_node_with_attrs__should_return_same_tag_text(self):
        u"""Tests for value extraction from node with and without attributes.

        A node without attributes has a different structure than a one with.
        However, for text-only node, same text should be returned.
        """
        xml = """<app>
            <data>
                <type>YEAR</type>
            </data>
        </app>"""
        xml_attr = """<app>
            <data>
                <type value="1">YEAR</type>
            </data>
        </app>"""
        m = mappet.Mappet(xml)
        m_attr = mappet.Mappet(xml_attr)

        # In both cases, the leaf's value is the same.
        assert m_attr.data.type.get() == m.data.type.get()
        # However, those nodes are not identical.
        assert m_attr.data.type != m.data.type

    def test_get_empty_text(self, literal):
        u"""Tests for returning of an empty leaf's contents."""
        # If leaf's content is not empty, ignore ``default`` argument.
        assert literal.get(default='alternative') == 'literal-text'

        # If a leaf does not have any text, a None should be returned.
        literal._xml.text = ''
        assert literal.get() is None

        # If leaf's text is empty, return the contents for ``default`` argument.
        assert literal.get(default='alternative') == 'alternative'

    def test_tag(self, literal):
        # ``tag`` should return the Literal's tagname
        assert literal.tag == 'literal_node'


class TestMappet(object):
    u"""Unittests for the actual mappet module."""

    def setup(self):
        xml = etree.Element('root')
        xml.set('attr1', 'val1')
        xml.set('attr2', 'val2')
        node1 = etree.SubElement(xml, 'node1')
        etree.SubElement(xml, 'node2')
        etree.SubElement(xml, 'node3')
        etree.SubElement(node1, 'subnode1')
        etree.SubElement(node1, 'subnode1')
        subnode2 = etree.SubElement(node1, 'subnode2')
        subnode2.text = 'subnode2_text'
        node_list = etree.SubElement(xml, 'node_list')
        subnode = etree.SubElement(node_list, 'subnode')
        subnode.set('attr1', 'val1')
        etree.SubElement(node_list, 'subnode')
        etree.SubElement(node_list, 'subnode')
        subnode.text = 'subnode_text'
        self.xml = xml
        self.m = mappet.Mappet(xml)

    def test_init_with_wrong_object(self):
        # Passing in a tuple should raise an exception.
        wrong_xml = ('node1', 'node2')
        with pytest.raises(AttributeError) as exc:
            mappet.Mappet(wrong_xml)

        assert 'Specified data cannot be used to construct a Mappet object' in str(exc.value)

    def test_init_with_string(self):
        u"""Tests for initialization of mappet object with XML string."""
        xml_str = '<root><node1 node_attr="val1"><leaf leaf_attr="val2">leaf_text</leaf></node1></root>'
        m = mappet.Mappet(xml_str)
        assert m.to_str() == xml_str

    def test_init_with_dict(self):
        u"""Tests for initialization of mappet object with dict representing a XML tree."""
        xml_dict = self.m.to_dict()
        m = mappet.Mappet(xml_dict)
        assert m.to_dict() == xml_dict

        assert mappet.Mappet({'a': {'#text': 'list_elem_1', '@attr1': 'val1'}}).to_str() == '<a attr1="val1">list_elem_1</a>'
        assert mappet.Mappet({'#text': 'list_elem_1', '@attr1': 'val1'}).to_str() == '<root attr1="val1">list_elem_1</root>'

    def test__nonzero__(self):
        u"""Tests for bool() function called on mappet objects."""
        assert bool(self.m)
        # subnode1 has no children and should return false.
        assert not bool(self.m.node1.subnode1[0])

    def test__len__(self):
        u"""Tests for counting the children."""
        # 'root' node is ignored.
        assert len(self.m) == 4
        assert len(self.m.node1) == 3

        # Empty element should have no children.
        assert len(mappet.Mappet(etree.Element('root'))) == 0

    def test__dir__(self):
        u"""Tests for returning a list of node's children."""
        # dir() should return names of all the children as well as helper methods.
        assert set(dir(self.m)) == {'node1', 'node2', 'node3', 'node_list'} | {'to_str', 'to_dict'}

    def test__getattr__(self):
        u"""Tests for returning node's children."""
        # node1 has two children called subnode1.
        n1 = self.m.node1.subnode1[0]
        assert n1 == self.m.node1.subnode1[0]
        assert set(self.m.node1.subnode1) == {self.m.node1.subnode1[0], self.m.node1.subnode1[1]}

        # If a node has only one child, it should be returned.
        one_child_node = etree.Element('root')
        subelement = etree.SubElement(one_child_node, 'subelement')
        assert mappet.Mappet(one_child_node).subelement == mappet.Literal(subelement)

        # Non-existing key should raise an exception.
        with pytest.raises(KeyError):
            self.m.node1.wrong_child

    def test__setattr__(self):
        u"""Tests for attribute assignment."""
        # An attribute, which does not exist in the class, should be created as an XML node.
        self.m.a = 'c'
        assert self.m.a.get() == 'c'

        # Access to Mappet class attribute should be transparent.
        self.m._xml = 'my_xml'
        assert self.m._xml == 'my_xml'

    def test__delattr__(self):
        u"""Tests for attribute removal."""
        assert len(self.m.node1) == 3
        # Removing all nodes called `subnode` (2).
        del self.m.node1.subnode1
        # After deletion of 2 nodes, only 1 should remain in total.
        assert len(self.m.node1) == 1

    def test__getitem__(self):
        u"""Tests for access to objects using indices."""
        #  if we access a single leaf, its value should be returned.
        assert self.m.node1['subnode2'] == 'subnode2_text'
        # For many leafs, the result should be them all.
        assert isinstance(self.m.node1['subnode1'], list)
        assert set(self.m.node1['subnode1']) == {self.m.node1.subnode1[0], self.m.node1.subnode1[1]}

    def test__delitem__(self):
        u"""Tests for removal of nodes by key."""
        assert len(self.m.node1) == 3
        # Removing all nodes called `subnode1` (2).
        del self.m.node1['subnode1']
        # Only 1 node should remain in total.
        assert len(self.m.node1) == 1

    def test__eq__(self):
        u"""Tests for Mappet object equality."""
        from copy import deepcopy
        copy_m = deepcopy(self.m)
        # Deep-copied mappet objects should be equal.
        assert self.m == copy_m
        assert self.m.to_dict() == copy_m.to_dict()

        self.m.node1.subnode2 = 'new_text'
        # Mappet instances with different subtrees should not be equal.
        assert self.m != copy_m
        assert self.m.to_dict() != copy_m.to_dict()

    def test__getstate__(self):
        u"""Tests for Mappet pickling."""
        import pickle
        picklestring = pickle.dumps(self.m)
        assert etree.tostring(self.m._xml) in picklestring

    def test__setstate__(self):
        u"""Tests for Mappet unpickling."""
        import pickle
        picklestring = pickle.dumps(self.m)
        # Unplicked XML structure should be identical to the original one.
        assert mappet.Mappet(self.m._xml) == pickle.loads(picklestring)

    def test__iter__(self):
        u"""Tests for method returning an iterator."""
        import collections
        # A Mappet object should be an iterator.
        assert isinstance(self.m, collections.Iterable)
        assert isinstance(self.m.__iter__(), collections.Iterable)

    def test_to_str(self):
        u"""Tests for method formatting a Mappet tree as a string."""
        xml_str = '<root attr1="val1" attr2="val2"><node1><subnode1/><subnode1/><subnode2>subnode2_text</subnode2></node1><node2/><node3/><node_list><subnode attr1="val1">subnode_text</subnode><subnode/><subnode/></node_list></root>'
        pretty_xml_str = '''<root attr1="val1" attr2="val2">
  <node1>
    <subnode1/>
    <subnode1/>
    <subnode2>subnode2_text</subnode2>
  </node1>
  <node2/>
  <node3/>
  <node_list>
    <subnode attr1="val1">subnode_text</subnode>
    <subnode/>
    <subnode/>
  </node_list>
</root>
'''
        assert self.m.to_str() == xml_str
        assert self.m.to_str(pretty_print=True) == pretty_xml_str

    def test_to_str_without_comments(self):
        u"""Tests for method formatting a Mappet tree as a string without comment."""
        comment_node = etree.Comment('a_comment_node')
        self.xml.insert(0, comment_node)
        # 'without_comments' uses c14n method the output is canonicalized
        xml_str = '<root attr1="val1" attr2="val2"><node1><subnode1>' \
                  '</subnode1><subnode1></subnode1><subnode2>subnode2_text' \
                  '</subnode2></node1><node2></node2><node3></node3>' \
                  '<node_list><subnode attr1="val1">subnode_text</subnode>' \
                  '<subnode></subnode><subnode></subnode></node_list></root>'
        assert self.m.to_str(without_comments=True) == xml_str

    def test_to_str_with_comments(self):
        u"""Tests for method formatting a Mappet tree as a string with comment."""
        comment_node = etree.Comment('a_comment_node')
        self.xml.insert(0, comment_node)
        xml_str = '<root attr1="val1" attr2="val2"><!--a_comment_node-->' \
                  '<node1><subnode1/><subnode1/><subnode2>subnode2_text' \
                  '</subnode2></node1><node2/><node3/><node_list>' \
                  '<subnode attr1="val1">subnode_text</subnode><subnode/>' \
                  '<subnode/></node_list></root>'
        pretty_xml_str = '''<root attr1="val1" attr2="val2">
  <!--a_comment_node-->
  <node1>
    <subnode1/>
    <subnode1/>
    <subnode2>subnode2_text</subnode2>
  </node1>
  <node2/>
  <node3/>
  <node_list>
    <subnode attr1="val1">subnode_text</subnode>
    <subnode/>
    <subnode/>
  </node_list>
</root>
'''
        assert self.m.to_str() == xml_str
        assert self.m.to_str(pretty_print=True) == pretty_xml_str

    def test_has_children(self):
        u"""Tests for checking if a node has any children."""
        assert self.m.has_children()

    def test_children(self):
        u"""Tests for a method that returns nodes children."""
        children_set = {self.m.node1.subnode1[0], self.m.node1.subnode1[1], self.m.node1.subnode2}
        assert set(self.m.node1.children()) == children_set

    def test_update(self):
        u"""Updating a subtree and creating new nodes."""
        new_dict = {
            'new_node': 'new_node_text',
            'subnode2': 'subnode2_new_text',
        }
        assert self.m.node1.subnode2.get() == 'subnode2_text'
        self.m.node1.update(**new_dict)
        # After the update, the new element should exist.
        assert self.m.node1.new_node.get() == 'new_node_text'
        # After the update `subnode2` should have new content.
        assert self.m.node1.subnode2.get() == 'subnode2_new_text'

    def test_sget__accessing_attribute__return_that_attribute(self):
        u"""Tests for safe node access using a specified path."""
        assert self.m.sget('node1.subnode2') == self.m.node1.subnode2
        assert self.m.sget('@attr1') == self.m['@attr1']
        assert self.m.sget('node1.subnode2.#text') == self.m.node1.subnode2.to_str()
        assert self.m.sget('node_list.subnode.0') == self.m.node_list.subnode[0]

    def test_sget__accessing_nonexistent_attribute__return_default(self):
        u"""Tests for safe getting nonexistent paths."""
        assert self.m.sget('node1.subnode666') is mappet.NONE_NODE
        assert self.m.sget('fake_node.subnode2') is mappet.NONE_NODE
        assert self.m.sget('fake_node.subnode2.@no_attr') is None
        assert self.m.sget('fake_node.subnode2.#text') is None
        assert self.m.sget('node1.#text') is None
        assert self.m.sget('node1.subnode1.0.#text') is None
        # Special case of accessing attribute of leafs list without specified index.
        assert self.m.sget('node1.subnode1.#text') is None

    def test_sget__given_default__it_should_be_returned(self):
        u"""Tests for providing default value for sget."""
        assert self.m.sget('node1.subnode666', 'default_value') == 'default_value'
        assert self.m.sget('fake_node.#text', 'default_value') == 'default_value'
        assert self.m.sget('fake_node.@attr', 'default_value') == 'default_value'

    def test_sget_none_converters(self):
        u"""Tests for invoking converters from sget for nonexistent paths."""
        assert self.m.sget('fake_node.subnode2').to_dict() is None
        assert self.m.sget('fake_node.subnode2').to_bool() is None
        assert self.m.sget('fake_node.subnode2').to_date() is None
        assert self.m.sget('fake_node.subnode2').to_datetime() is None
        assert self.m.sget('fake_node.subnode2').to_float() is None
        assert self.m.sget('fake_node.subnode2').to_int() is None
        assert self.m.sget('fake_node.subnode2').to_str() is None
        assert self.m.sget('fake_node.subnode2').to_time() is None

    def test_set(self):
        u"""Tests for subtree modification."""
        self.m.node1 = {'a': 'A'}
        # A dict should be correctly changed into a XML tree.
        assert self.m.node1.to_str() == '<node1><a>A</a></node1>'
        # Aliases for updated node should be purged.
        assert self.m.node1._aliases is None

        self.m.node1 = [{'a': i} for i in 'ABC']
        # A list should be correctly changed into a XML tree.
        assert self.m.node1.to_str() == '<node1><a>A</a><a>B</a><a>C</a></node1>'
        # Aliases for updated node should be purged.
        assert self.m.node1._aliases is None

        self.m.node1 = 'some_text'
        # Assignment of text should correctly update the node.
        assert self.m.node1.get() == 'some_text'

        self.m.node1 = 4
        # Assigned number should be convertible.
        assert self.m.node1.to_int() == 4

    def test_set_new_element(self):
        u"""Tests for creating new XML nodes."""
        # A created node should be correctly represented in the parent's XML structure.
        self.m.node1.new_element = 'new_element_text'

        assert self.m.node1.to_dict() == {
            'subnode1': [None, None],
            'subnode2': 'subnode2_text',
            'new_element': 'new_element_text',
        }

    def test_set_list_as_new_element(self):
        u"""Tests for creating now XML nodes from a list."""
        # If a node does not exists, it should be created after we assign a list to i.
        # Assigning a list to a literal.
        self.m.node1.new_element = [
            {'a': 'list_elem_1'},
            {'a': 'list_elem_2'},
        ]
        # Assigning a list to new element should create that element.
        assert self.m.node1.to_dict() == {
            'subnode1': [None, None],
            'subnode2': 'subnode2_text',
            'new_element': {
                'a': [
                    'list_elem_1',
                    'list_elem_2',
                ]
            }
        }
        # Assigning a list to node with attributes.
        self.m.node1.new_element = [
            {'a': {'#text': 'list_elem_1', '@attr1': 'val1'}},
            {'a': {'#text': 'list_elem_2', '@attr1': 'val2'}},
        ]
        # Assigning a list to a new element should create that element.
        assert self.m.node1.to_dict() == {
            'subnode1': [None, None],
            'subnode2': 'subnode2_text',
            'new_element': {
                'a': [
                    {'#text': 'list_elem_1', '@attr1': 'val1'},
                    {'#text': 'list_elem_2', '@attr1': 'val2'},
                ]
            }
        }
        # Assigning to an existing element with list, should result in those lists being replaced.
        self.m.node1.new_element = [{'a': i} for i in 'ABC']
        assert self.m.node1.new_element.to_str() == '<new_element><a>A</a><a>B</a><a>C</a></new_element>'

        # Assigning a list of empty nodes.
        self.m.node1.new_element = [{'leaf1': None}, {'leaf2': None}]
        assert self.m.node1.new_element.to_str() == '<new_element><leaf1/><leaf2/></new_element>'

    def test_set_new_element_at_root(self):
        u"""Tests for creating a new node, directly at the root node."""
        assert self.m.to_dict() == {
            'node1': {
                'subnode2': 'subnode2_text', 'subnode1': [None, None]
            },
            'node3': None,
            'node2': None,
            'node_list': {'subnode': [{'#text': 'subnode_text', '@attr1': 'val1'}, None, None]},
            '@attr1': 'val1',
            '@attr2': 'val2',
        }
        # Adds the new node to root.
        self.m.new_node = {'#text': 'new_node_text', '@new_attr': 'new_attr'}
        assert self.m.to_dict() == {
            'node1': {
                'subnode2': 'subnode2_text', 'subnode1': [None, None]
            },
            'node3': None,
            'node2': None,
            'node_list': {'subnode': [{'#text': 'subnode_text', '@attr1': 'val1'}, None, None]},
            '@attr1': 'val1',
            '@attr2': 'val2',
            'new_node': {'#text': 'new_node_text', '@new_attr': 'new_attr'},
        }

    def test_set_new_nested_element_at_root(self):
        u"""Tests for creating a new, complex node, directly at the root node."""
        assert self.m.to_dict() == {
            'node1': {
                'subnode2': 'subnode2_text', 'subnode1': [None, None]
            },
            'node3': None,
            'node2': None,
            'node_list': {'subnode': [{'#text': 'subnode_text', '@attr1': 'val1'}, None, None]},
            '@attr1': 'val1',
            '@attr2': 'val2',
        }
        # Adding the node to root node.
        self.m.new_node = {
            '#text': 'new_node_text',
            '@new_attr': 'new_attr',
            'new_node_subnode1': {
                '@sub_attr1': 'subattr1',
            },
            'new_node_subnode2': None,
        }
        assert self.m.to_dict() == {
            'node1': {
                'subnode2': 'subnode2_text', 'subnode1': [None, None]
            },
            'node3': None,
            'node2': None,
            'node_list': {'subnode': [{'#text': 'subnode_text', '@attr1': 'val1'}, None, None]},
            '@attr1': 'val1',
            '@attr2': 'val2',
            'new_node': {
                '#text': 'new_node_text',
                '@new_attr': 'new_attr',
                'new_node_subnode1': {
                    '@sub_attr1': 'subattr1',
                },
                'new_node_subnode2': None,
            }
        }

    def test_create__new_element_with_hyphens__will_be_created(self):
        u"""Tests for creating a node with hyphens in its name."""
        m = mappet.Mappet(self.xml)
        m.node1.create('new-element', 'new_element_text')

        assert m.node1.to_dict() == {
            'subnode1': [None, None],
            'subnode2': 'subnode2_text',
            'new-element': 'new_element_text',
        }

    def test_create__new_element_already_exists__will_raise(self):
        u"""Two identical elements cannot be created."""
        m = mappet.Mappet(self.xml)

        m.node1.create('new-element', 'new_element_text')

        with pytest.raises(KeyError) as exc:
            # Creates an element that already exists.
            m.node1.create('new-element', 'new_element_text2')

        assert 'Node {} already exists in XML'.format('new-element') in str(exc.value)

    def test_set_new_element_from_literal(self):
        u"""Tests for creation of new XML nodes from leafs."""
        self.m.node3 = 'text'
        assert self.m.to_dict() == {
            'node1': {
                'subnode2': 'subnode2_text', 'subnode1': [None, None]
            },
            'node3': 'text',
            'node2': None,
            'node_list': {'subnode': [{'#text': 'subnode_text', '@attr1': 'val1'}, None, None]},
            '@attr1': 'val1',
            '@attr2': 'val2',
        }
        # Assigning the new node to a leaf node.
        self.m.node3 = {
            '#text': 'node3_text',
            '@new_attr': 'new_attr',
            'node3_subnode': 'subnode_text',
        }
        # A leaf should be converted to a Mappet object (a full node).
        assert self.m.to_dict() == {
            'node1': {
                'subnode2': 'subnode2_text', 'subnode1': [None, None]
            },
            'node3': {
                '#text': 'node3_text',
                '@new_attr': 'new_attr',
                'node3_subnode': 'subnode_text',
            },
            'node2': None,
            'node_list': {'subnode': [{'#text': 'subnode_text', '@attr1': 'val1'}, None, None]},
            '@attr1': 'val1',
            '@attr2': 'val2',
        }

    def test_to_dict(self):
        u"""Tests for explicit conversion of a Mappet object to Python dict."""
        xml_dict = {
            '@attr1': 'val1',
            '@attr2': 'val2',
            'node1': {'subnode1': [None, None], 'subnode2': 'subnode2_text'},
            'node2': None,
            'node3': None,
            'node_list': {'subnode': [{'#text': 'subnode_text', '@attr1': 'val1'}, None, None]},
        }
        assert self.m.to_dict() == xml_dict

    def test__get_aliases(self):
        u"""Tests for generation of tagname aliases."""
        assert self.m._get_aliases() == {
            'node1': 'node1',
            'node2': 'node2',
            'node3': 'node3',
            'node_list': 'node_list',
        }
        assert len(self.m._aliases) == 4
        # A dict with aliases should return normalized names also.
        xml = etree.Element('root')
        etree.SubElement(xml, 'Normalize-Me')
        assert mappet.Mappet(xml)._get_aliases() == {
            'normalize_me': 'Normalize-Me',
        }

    def test_contains__existing_leaf__will_contain(self):
        u"""Test for checking if Mappet object contains leaf."""
        assert 'node1' in self.m
        assert 'node1.subnode1' in self.m

    def test_contains__nonexistent_leaf__wont_contain(self):
        u"""Checks if Mappet object doesn't contain leaf."""
        assert 'non-existent-node' not in self.m
        assert 'non-existent-node.subnode1' not in self.m
        assert 'node1.im-not-here' not in self.m

    def test_contains__existing_attr__will_contain(self):
        u"""Checks if Mappet object contains attr."""
        assert '@attr1' in self.m
        assert 'node_list.subnode.0.@attr1' in self.m

    def test_contains__nonexistent_attr__wont_contain(self):
        u"""Checks if Mappet object doesn't contain attr."""
        assert '@fake-attr' not in self.m
        assert 'node_list.subnode.0.@fake-attr' not in self.m
        assert 'node_list.subnode.1.@attr1' not in self.m

    def test_contains__existing_text__will_contain(self):
        u"""Checks if Mappet object contains text."""
        assert 'node1.subnode2.#text' in self.m

    def test_contains__nonexisting_text__wont_contain(self):
        u"""Checks if Mappet object doesn't contain text."""
        assert '#text' not in self.m
        assert 'node1.non-existent.#text' not in self.m
        assert 'node1.#text' not in self.m

    def test_tag(self):
        # ``tag`` should return the Mappet's tagname
        assert self.m.tag == 'root'
        assert self.m.node1.tag == 'node1'
        assert self.m.node1.subnode2.tag == 'subnode2'

    def test_xpath__given_existing_leaf__should_return_that_leaf(self):
        u"""An XML leaf should be returned as a Literal object."""
        node = self.m.xpath('node1/subnode2')
        assert node.get() == 'subnode2_text'

    def test_xpath__given_existing_node__should_return_that_node(self):
        u"""A node that has children should be returned as Mapper object."""
        self.xml.set('list', 'l1')
        self.xml.set('list', 'l1')
        self.xml.set('list', 'l2')
        self.xml.set('list', 'l3')
        etree.SubElement(self.xml, 'list')
        etree.SubElement(self.xml, 'list')
        m = mappet.Mappet(self.xml)
        xpath_evaluator_node = m.xpath('node1')
        xpath_node = m.xpath('node1', single_use=True)
        xpath_node_list = m.xpath('list/l1')
        assert xpath_evaluator_node.has_children()
        assert xpath_evaluator_node.to_dict() == m.node1.to_dict()
        assert xpath_evaluator_node == xpath_node
        assert isinstance(xpath_node_list, list)

    def test_create_xpath_evaluator(self):
        u"""Checks if mappet object can be converted to XPatchEvaluator"""
        assert isinstance(self.m.xpath_evaluator(), etree._XPathEvaluatorBase)

    def test_xpath_regexp(self):
        result = self.m.xpath(
            "//*[re:test(., '^sub.*', 'subnode')]",
            regexp=True,
        )
        assert len(result) == 5
        x_node = etree.SubElement(self.xml, 'x_node')
        x_node.text = 'xxxxx'
        self.m = mappet.Mappet(self.xml)
        result = self.m.xpath("//*[re:test(., 'x{5}')]", regexp=True)
        assert result[-1] == x_node

    def test_xpath_regexp_exslt(self):
        result = self.m.xpath(
            "//*[re:test(., '^sub.*', 'subnode')]",
            namespaces='exslt',
            regexp=True,
        )
        assert len(result) == 5
