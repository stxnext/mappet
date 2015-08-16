.. image:: https://travis-ci.org/stxnext/mappet.svg
   :target: https://travis-ci.org/stxnext/mappet
   :alt: Travis CI

.. image:: http://codecov.io/github/stxnext/mappet/coverage.svg?branch=master
   :target: http://codecov.io/github/stxnext/mappet?branch=master
   :alt: Codecov

.. image:: https://codeclimate.com/github/stxnext/mappet/badges/gpa.svg
   :target: https://codeclimate.com/github/stxnext/mappet
   :alt: Code Climate

.. image:: http://www.quantifiedcode.com/api/v1/project/4f798b7ea0954d8790f3fe420a5fde0e/badge.svg
   :target: http://www.quantifiedcode.com/app/project/4f798b7ea0954d8790f3fe420a5fde0e
   :alt: Code issues

.. image:: https://www.codacy.com/project/badge/4ea440e5fa5045acb376e6461e804179
   :target: https://www.codacy.com/app/radoslaw-szalski/mappet
   :alt: Codacy

.. image:: https://readthedocs.org/projects/mappet/badge/?version=latest
   :target: https://readthedocs.org/projects/mappet/?badge=latest
   :alt: Documentation Status


==========
``mappet``
==========

``Mappet`` has been created to enable an easy an intuitive way to work with XML
structures in Python code.

A well known ``lxml`` module has been used under the hood, mainly due to XML parsing performance.


Mappet accepts a string with valid XML, an ``lxml.etree._Element`` object or a dict
representing the XML tree.

>>> import mappet
>>> f = open('example.xml', 'r')
>>> m = mappet.Mappet(f.read())

As an example, an XML document of the following structure has been used:

.. code-block:: xml

    <?xml version='1.0' encoding='iso-8859-2'?>
    <a-message>
        <head>
            <id seq="20" tstamp="2015-07-13T10:55:25+02:00"/>
            <initiator>Mr Sender</initiator>
            <date>2015-07-13T10:56:05.597420+02:00</date>
            <type>reply-type</type>
        </head>
        <auth>
            <user first-name="Name" last-name="LastName">id</user>
        </auth>
        <status>
            <result>OK</result>
        </status>
        <reply>
            <cars>
                <Car>
                    <id>12345</id>
                    <Manufacturer>BMW</Manufacturer>
                    <Model_Name>X6</Model_Name>
                    <Body>SUV</Body>
                    <Fuel>Diesel</Fuel>
                    <Doors>5</Doors>
                    <ccm>3000</ccm>
                    <HP>256</HP>
                    <TransType>Automatic</TransType>
                    <seats>5</seats>
                    <weight>3690</weight>
                </Car>
                <Car>
                    <id>54321</id>
                    <Manufacturer>BMW</Manufacturer>
                    <Model_Name>X1</Model_Name>
                    <Body>SUV</Body>
                    <Fuel>Diesel</Fuel>
                    <Doors>5</Doors>
                    <ccm>3000</ccm>
                    <HP>198</HP>
                    <TransType>Automatic</TransType>
                    <seats>5</seats>
                    <weight>2890</weight>
                </Car>
            </cars>
        </reply>
    </a-message>


Conventions
===========

Every XML node can be accessed in two ways: by attribute and item access.


Dictionary access:
------------------

Dictionary access is possible thanks to XML document being represented as a
Python dictionary. Conversion of values is done explicitly.

By default, values are returned as ``str``.

>>> m['reply']['cars']['Car'][0]['Manufacturer']
'BMW'

Nodes' names are case-sensitive.


Attribute access:
-----------------

Due to restrictions in Python variable names, tag names are normalized for attribute access.
Tag names are normalized to lowercase and hyphens to underlines.

Same example using attribute access (__repr__ is responsible for representing the tag):

>>> m.reply.cars.car[0].manufacturer
BMW

To get a string representation use ``get()``.

>>> m.reply.cars.car[0].manufacturer.get()
'BMW'

``get()`` has two parameters, *default* and *callback*. The first one is returned when then node's value is empty, the
second is a function to be called upon the returned value.

>>> m.reply.cars.car[0].ccm.get(callback=int)
3000

Alternatively, one can use built-in helper functions, defined in helpers.py

>>> m.reply.cars.car[0].ccm.to_int()
3000

Helper functions
================

- to_bool
- to_int
- to_str
- to_string
- to_float
- to_time
- to_datetime
- to_date
