# -*- coding: utf-8 -*-

u"""Unittests for helper functions.

.. :module: test_helpers
   :synopsis: Unittests for helper functions.
"""
from decimal import Decimal

from lxml import etree
import datetime

import mock
import pytest

from mappet import helpers


class TestHelpers(object):
    u"""Unittests for helper functions."""

    def test_to_bool(self):
        u"""Tests for conversion of mnemonic values to boolean values."""
        # Defined mnemonics should have a boolean value.
        assert helpers.to_bool('1')
        assert helpers.to_bool('true')
        assert helpers.to_bool('True')
        assert helpers.to_bool('YES')
        assert helpers.to_bool(u'yes')
        assert not helpers.to_bool('0')
        assert not helpers.to_bool('false')
        assert not helpers.to_bool(u'False')
        assert not helpers.to_bool('NO')
        assert not helpers.to_bool('no')

        # Undefined mnemonics should have value equal to ``bool(mnemonic)``.
        assert helpers.to_bool('whatever')
        assert not helpers.to_bool('')
        assert not helpers.to_bool(())

    def test_to_str(self):
        u"""Tests for conversion of values to str."""
        assert helpers.to_str('') == ''
        assert helpers.to_str(5) == '5'
        assert helpers.to_str({'a': 3}) == "{'a': 3}"

    def test__to_str__given_encoded_diacritics__should_return_unicode_string(self):
        u"""Tests for conversion of unicode literals to unicode."""
        assert helpers.to_str(u'ążśęćółń') == u'ążśęćółń'
        assert helpers.to_str(u'\u0105') == u'ą'
        assert helpers.to_str(u'\u0105\u017c\u017a\u0107') == u'ążźć'
        assert helpers.to_str({'a': 3}) == "{'a': 3}"

    def test_to_int(self):
        u"""Tests for conversion of values to int."""
        assert helpers.to_int(5) == 5
        assert helpers.to_int(-3.0) == -3

    def test_to_float(self):
        u"""Tests for conversion of values to float."""
        assert helpers.to_float(-3) == -3.0
        assert helpers.to_float(5) == 5.0
        assert helpers.to_float(3.14) == 3.14

    def test_to_decimal(self):
        assert helpers.to_decimal(0.0) == Decimal(0)
        assert helpers.to_decimal(-10.15) == Decimal(-10.15)
        assert helpers.to_decimal('+10') == Decimal(10)

    def test_to_time(self):
        u"""Tests for conversion of ISO time to ``datetime.time`` objects."""
        with pytest.raises(Exception) as exec_empty:
            # Empty value is forbidden.
            assert helpers.to_time('') == ''

        assert 'Empty value not allowed' in str(exec_empty.value)

        # ISO time returns a correct ``datetime.time`` object.
        assert helpers.to_time('13') == datetime.time(13)
        assert helpers.to_time('13:45') == datetime.time(13, 45)
        assert helpers.to_time('13:45:46L') == datetime.time(13, 45, 46)

    def test_to_datetime(self):
        u"""Tests for conversion of ISO dates and times to ``datetime.datetime`` objects."""
        with pytest.raises(Exception) as execinfo:
            # Empty value is forbidden.
            assert helpers.to_datetime('') == ''

        assert 'Empty value not allowed' in execinfo.value

        with pytest.raises(Exception) as exec_format:
            # Only ISO format is allowed.
            assert helpers.to_datetime('12022014 12:00')

        assert 'month must be in 1..12' in str(exec_format)

        # Correct ISO format.
        assert helpers.to_datetime('2014-02-12T12:30:00')

    def test_to_date(self):
        u"""Tests for conversion of ISO dates to ``datetime.date`` objects."""
        with pytest.raises(Exception) as execinfo:
            # Empty value is forbidden.
            assert helpers.to_date('') == ''

        assert 'Empty value not allowed' in execinfo.value

        with pytest.raises(Exception) as exec_format:
            # Only ISO 8601 or RFC 3339 format allowed.
            assert helpers.to_date('28022014')

        assert 'month must be in 1..12' in str(exec_format)

        # ISO date format.
        assert helpers.to_date('2014-02-12') == datetime.datetime(2014, 02, 12)

    def test_from_bool(self):
        u"""Test for conversion of True and False to a mnemonic value."""
        assert helpers.from_bool(True) == 'YES'
        assert helpers.from_bool(False) == 'NO'

        # Undefined values are interpreted by ``bool()``.
        assert helpers.from_bool(()) == False
        assert helpers.from_bool('sth') == True

        # Returns False if exception is thrown.
        assert helpers.from_bool([]) == False

    @pytest.mark.parametrize("value, expected", [
        ('', ''),
        ('sth', 'sth'),
        (u'unicode', u'unicode'),
        (-4, '-4'),
        (0, '0'),
        (-3.14, '-3.14'),
        (-0.0, '-0.0'),
    ])
    def test__converting_str_unicode_int_and_float__should_use_str_formatter(self, value, expected):
        converter = helpers.CAST_DICT[type(value)]
        assert converter(value) == expected

    def test_from_time(self):
        u"""Tests for ``datetime.time`` to ``str`` conversion."""
        with pytest.raises(Exception) as exc_type:
            # Only datetime.time objects allowed.
            assert helpers.from_time(datetime.date(2014, 12, 14))

        assert 'is not datetime.time object' in str(exc_type)

        assert helpers.from_time(datetime.time(14, 11, 10)) == '14:11:10'

    @mock.patch('mappet.helpers.dateutil.tz')
    def test_from_datetime(self, mock_tz):
        u"""Tests for ``datetime.datetime`` to ``str`` conversion."""
        with pytest.raises(Exception) as exc_empty:
            # Empty value is forbidden.
            assert helpers.from_datetime('')

        assert 'Empty value not allowed' in str(exc_empty.value)

        with pytest.raises(Exception) as exc_type:
            # Only datetime.datetime objects are allowed.
            assert helpers.from_datetime(datetime.time(14, 10))

        assert 'Unexpected type' in str(exc_type.value)

        # We don't want to be dependant on a timezone.
        mock_tz.tzlocal.return_value = None
        assert helpers.from_datetime(datetime.datetime(2013, 10, 05, 14, 11, 10)) == '2013-10-05T14:11:10'

    @mock.patch('mappet.helpers.dateutil.tz')
    def test_from_date(self, mock_tz):
        u"""Tests for ``datetime.date`` to ``str`` conversion."""
        with pytest.raises(Exception) as exc_empty:
            # Empty value is forbidden.
            assert helpers.from_date('')

        assert 'Empty value not allowed' in str(exc_empty.value)

        with pytest.raises(Exception) as exc_type:
            # Only ``datetime.date`` and ``datetime.datetime`` objects are allowed.
            assert helpers.from_date(datetime.time(14, 10))

        assert 'Not datetime.date object' in str(exc_type.value)

        assert helpers.from_date(datetime.date(2013, 10, 05)) == '2013-10-05'

        # We don't want to be dependant on a timezone.
        mock_tz.tzlocal.return_value = None
        assert helpers.from_datetime(datetime.datetime(2013, 10, 05, 14, 11, 10)) == '2013-10-05T14:11:10'


class TestTreeHelpers(object):
    u"""Unittests for Mappet utils"""

    def setup(self):
        self.root = etree.Element('root')

    def test_normalize_tag(self):
        # Tagname is normalized to lowercase and '-' are changed to '_'.
        assert helpers.normalize_tag('tag') == 'tag'
        assert helpers.normalize_tag('xml_tag') == 'xml_tag'
        assert helpers.normalize_tag('Xml_Tag') == 'xml_tag'
        assert helpers.normalize_tag('Xml-Tag') == 'xml_tag'
        assert helpers.normalize_tag('XML-TAG_1') == 'xml_tag_1'

    def test_etree_to_dict(self):
        u"""Tests lxml.etree tree conversion to Python dict."""
        # A single node.
        assert helpers.etree_to_dict(self.root) == {'root': None}

        # Children without text.
        child1 = etree.SubElement(self.root, 'child1')
        child2 = etree.SubElement(self.root, 'child2')
        assert helpers.etree_to_dict(self.root) == {'root': {'child1': None, 'child2': None}}

        # Attributes should be represented with the '@' symbol.
        child2.set('is_orphan', 'Not yet')
        assert helpers.etree_to_dict(self.root) == {
            'root': {
                'child1': None,
                'child2': {'@is_orphan': 'Not yet'}
            }
        }

        # Node values should be carried over to the dict.
        child1.text = 'hello'
        assert helpers.etree_to_dict(self.root) == {
            'root': {
                'child1': 'hello',
                'child2': {'@is_orphan': 'Not yet'}
            }
        }


        # A node with both attributes and text should have text assigned to the
        # '#text' key in the dict.
        tag = etree.Element('root')
        tag.set('attr1', 'value1')
        tag.text = 'some_text'
        assert helpers.etree_to_dict(tag) == {
            'root': {
                '@attr1': 'value1',
                '#text': 'some_text',
            }
        }

    def test_etree_to_dict_comments_handling(self):
        u"""Tests lxml.etree tree conversion to Python dict with comment handling."""
        comment_node = etree.Comment('a_comment_node')
        self.root.insert(0, comment_node)
        assert helpers.etree_to_dict(self.root) == {
            'root': {
                '#comments': 'a_comment_node'
            }
        }
        assert helpers.etree_to_dict(self.root, without_comments=True) == {
            'root': {}
        }

    def test__dict_to_etree__given_node_with_whitespace__should_preserve_it(self):
        tag = etree.Element('root')
        tag.text = ' '

        assert helpers.etree_to_dict(tag, trim=False) == {
            'root': ' ',
        }
        tag = etree.Element('root')
        tag.set('attr1', 'value1')
        tag.text = ' '

        assert helpers.etree_to_dict(tag, trim=False) == {
            'root': {
                '@attr1': 'value1',
                '#text': ' ',
            }
        }

    def test__dict_to_etree__given_node_with_trim(self):
        tag = etree.Element('root')
        tag.text = ' '

        assert helpers.etree_to_dict(tag) == {
            'root': None,
        }
        tag = etree.Element('root')
        tag.set('attr1', 'value1')
        tag.text = ' '

        assert helpers.etree_to_dict(tag,) == {
            'root': {
                '@attr1': 'value1',
            }
        }

    def test_dict_to_etree(self):
        u"""Tests the conversion of dict to ``lxml.etree`` structure."""
        with pytest.raises(AttributeError) as exc:
            helpers.dict_to_etree(['node'], self.root)

        assert 'Argument is neither dict nor basestring' in str(exc.value)

        helpers.dict_to_etree({'single_node': None}, self.root)
        # A dict with one empty key should be converted to an etree element with one child.
        assert etree.iselement(self.root)
        assert len(self.root) == 1
        assert self.root[0].tag == 'single_node'

    def test_dict_to_etree_nodes_with_text(self):
        node1_text = 'Hai, I R node1!'
        node2_text = 'I do not talk to strangers'
        nodes_with_text = {
            'node1': node1_text,
            'node2': node2_text,
        }
        helpers.dict_to_etree(nodes_with_text, self.root)
        mapped_nodes = {node.tag for node in self.root}
        assert etree.iselement(self.root)
        assert len(self.root) == 2
        assert set(nodes_with_text.keys()) == mapped_nodes
        assert self.root[0].text == node1_text
        assert self.root[1].text == node2_text

    def test_dict_to_etree_nodes_with_attr_and_text(self):
        node1_text = 'Hai, I R node1!'
        node2_text = 'I do not talk to strangers'
        nodes_with_attr_and_text = {
            'node1': {
                '@personality': 'brave',
                '#text': node1_text,
            },
            'node2': {
                '@personality': 'shy',
                '#text': node2_text,
                '@age': '21',
            }
        }
        helpers.dict_to_etree(nodes_with_attr_and_text, self.root)
        mapped_nodes = {node.tag for node in self.root}
        assert etree.iselement(self.root)
        assert len(self.root) == 2
        assert set(nodes_with_attr_and_text.keys()) == mapped_nodes
        assert self.root[0].text == node1_text
        assert self.root[1].text == node2_text
        assert self.root[0].get('personality') == 'brave'
        assert self.root[1].get('personality') == 'shy'
        assert self.root[1].get('age') == '21'
        assert 'age' not in self.root[0].attrib

    def test_dict_to_etree_list_of_nodes(self):
        list_of_nodes = {
            'node1': [
                {'subnode11': None},
            ],
            'node2': [
                {'subnode21': None},
                {'subnode22': None},
            ],
            'node3': [
                {'subnode31': None},
            ],
            'node4': [
                'simple text',
                None,
                None
            ]
        }
        helpers.dict_to_etree(list_of_nodes, self.root)
        mapped_nodes = {node.tag for node in self.root}
        assert etree.iselement(self.root)
        assert len(self.root) == 6
        assert set(list_of_nodes.keys()) == mapped_nodes
        assert len(self.root[0]) == 1
        assert len(self.root[1]) == 1
        assert len(self.root[2]) == 2

    def test_dict_to_etree_lists_with_none(self):
        u"""Tests the conversion of dict with empty children to an lxml tree."""
        xml_dict = {
            'node1': [
                None,
                None,
            ]
        }
        etree_from_dict = helpers.dict_to_etree(xml_dict, self.root)
        assert etree.iselement(etree_from_dict)
        assert etree.tostring(etree_from_dict) == '<root><node1/><node1/></root>'

    def test_dict_to_etree_lists_with_mixed_children(self):
        u"""Tests the conversion of dicts with different children to an lxml tree."""
        xml_dict = {
            'node1': [
                None,
                None,
                {
                    '#text': 'text_node',
                }
            ]
        }
        etree_from_dict = helpers.dict_to_etree(xml_dict, self.root)
        assert etree.iselement(etree_from_dict)
        assert etree.tostring(etree_from_dict) == '<root><node1/><node1/><node1>text_node</node1></root>'
