#!/usr/bin/python2.6
#
# Copyright 2010 Google Inc. All Rights Reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

"""Tests for api.py."""

__author__ = 'aiuto@google.com (Tony Aiuto)'

import os

from google.apputils import basetest

from googleapis.codegen import data_types
from googleapis.codegen import language_model
from googleapis.codegen.anyjson import simplejson
from googleapis.codegen.api import Api
from googleapis.codegen.api import ApiException
from googleapis.codegen.api import Method
from googleapis.codegen.api import Resource
from googleapis.codegen.api import Schema


class ApiTest(basetest.TestCase):

  # The base discovery doc for most tests.
  __TEST_DISCOVERY_DOC = 'sample_discovery.json'

  def ApiFromDiscoveryDoc(self, path):
    """Load a discovery doc from a file and creates a library Api.

    Args:
      path: (str) The path to the document.

    Returns:
      An Api for that document.
    """

    f = open(os.path.join(os.path.dirname(__file__), 'testdata', path))
    discovery_doc = simplejson.loads(f.read())
    f.close()
    return Api(discovery_doc)

  def testLazySchemaForCreation(self):
    """Check loading schemas which are known to have a forward reference.

    In the test data, "Activity" refers to "Commment", and the nature
    (sorted) of the loading code causes "Activity" to be processed
    before "Commment".  We want to make sure that SchemaFor does the right
    thing with the lazy creation of activity.
    """
    api = self.ApiFromDiscoveryDoc(self.__TEST_DISCOVERY_DOC)
    for schema in ['Activity', 'Comment', 'ActivityObject']:
      self.assertTrue(isinstance(api._schemas[schema], Schema))

  def SchemaRefInProperties(self):
    """Make sure that an object ref works in a schema properties list."""
    api = self.ApiFromDiscoveryDoc(self.__TEST_DISCOVERY_DOC)
    activity_schema = api._schemas['Activity']
    for prop in activity_schema.values['properties']:
      if prop.values['wireName'] == 'object':
        self.assertTrue(prop.object_type)
        self.assertEquals('ActivityObject',
                          prop.object_type.values['className'])

  def testMakeDefaultSchemaNameFromTheDictTag(self):
    """Use the outer tag as id for schemas which have no id in their dict."""
    discovery_doc = simplejson.loads(
        """
        {
         "name": "fake",
         "version": "v1",
         "schemas": {
           "should_use_id": {
             "id": "named",
             "type": "object",
             "properties": { "dummy": { "type": "string" } }
           },
           "unnamed": {
             "type": "object",
             "properties": { "dummy": { "type": "string" } }
           }
         },
         "resources": {}
        }
        """)
    gen = Api(discovery_doc)
    self.assertTrue('Named' in gen._schemas)
    self.assertTrue('Unnamed' in gen._schemas)

  def testUnknownHttpMethod(self):
    """Make sure we get an exception on unknown HTTP types."""
    api = Api({'name': 'dummy', 'version': 'v1', 'resources': {}})
    unused_resource = Resource(api, 'temp', {'methods': {}})
    self.assertRaises(ApiException,
                      Method, api, 'bad', {
                          'rpcMethod': 'rpc',
                          'httpMethod': 'Not GET/POST/PUT/DELETE',
                          'parameters': {}
                          })

  def testRequiredParameterList(self):
    """Make sure we are computing required parameters correctly."""
    api = self.ApiFromDiscoveryDoc(self.__TEST_DISCOVERY_DOC)

    tests_executed = 0

    for resource in api.values['resources']:
      if resource.values['wireName'] == 'activities':
        for method in resource.values['methods']:
          if method.required_parameters:
            required_names = [p.values['wireName']
                              for p in method.required_parameters]
            self.assertEquals(method.values['parameterOrder'], required_names)
            tests_executed += 1

          if method.values['wireName'] == 'get':
            optional_names = [p.values['wireName']
                              for p in method.optional_parameters]
            self.assertEquals(['truncateAtom', 'max-comments', 'hl',
                               'max-liked'],
                              optional_names)
            tests_executed += 1
    self.assertEquals(6, tests_executed)

  def testSchemaLoadingAsString(self):
    """Test for the "schema as strings" representation."""
    api = self.ApiFromDiscoveryDoc('latitude.v1.json')
    self.assertEquals(4, len(api._schemas))

  def testSubResources(self):
    """Test for the APIs with subresources."""

    def CountResourceTree(resource):
      ret = 0
      for r in resource._resources:
        ret += 1 + CountResourceTree(r)
      return ret

    api = self.ApiFromDiscoveryDoc('moderator.v1.json')
    top_level_resources = 0
    total_resources = 0
    non_method_resources = 0
    have_sub_resources = 0
    have_sub_resources_and_methods = 0
    for r in api._resources:
      top_level_resources += 1
      total_resources += 1 + CountResourceTree(r)
      if not r._methods:
        non_method_resources += 1
      if r._resources:
        have_sub_resources += 1
      if r._resources and r._methods:
        have_sub_resources_and_methods += 1
    # Hand counted 18 resources in the file.
    self.assertEquals(18, total_resources)
    self.assertEquals(11, top_level_resources)
    # 4 of them have no methods, only sub resources
    self.assertEquals(4, non_method_resources)
    # 6 of them have sub resources.
    self.assertEquals(6, have_sub_resources)
    # And, of course, 2 should have both sub resources and methods
    self.assertEquals(2, have_sub_resources_and_methods)

  def testArrayOfArray(self):

    class FakeLanguageModel(language_model.LanguageModel):
      def GetCodeTypeFromDictionary(self, def_dict):
        return def_dict.get('type')

      def CodeTypeForArrayOf(self, s):
        return 'Array[%s]' % s

    discovery_doc = {
        'name': 'fake',
        'version': 'v1',
        'schemas': {
            'AdsenseReportsGenerateResponse': {
                'id': 'AdsenseReportsGenerateResponse',
                'type': 'object',
                'properties': {
                    'basic': {
                        'type': 'string'
                        },
                    'simple_array': {
                        'type': 'array',
                        'items': {'type': 'string'}
                        },
                    'array_of_arrays': {
                        'type': 'array',
                        'items': {'type': 'array', 'items': {'type': 'string'}}
                        }
                    }
                }
            },
        'resources': {}
        }
    api = Api(discovery_doc)
    self.language_model = FakeLanguageModel()
    api.VisitAll(lambda o: o.SetLanguageModel(self.language_model))
    response_schema = api._schemas.get('AdsenseReportsGenerateResponse')
    self.assertTrue(response_schema)
    prop = [prop for prop in response_schema.values['properties']
            if prop.values['wireName'] == 'array_of_arrays']
    self.assertTrue(len(prop) == 1)
    prop = prop[0]
    self.assertEquals('Array[Array[string]]', prop.codeType)

  def testDetectInvalidSchema(self):
    base_discovery = {'name': 'fake', 'version': 'v1', 'resources': {}}
    bad_discovery = dict(base_discovery)
    bad_discovery['schemas'] = {
        'NoItemsInArray': {'id': 'noitems', 'type': 'array'}
        }
    self.assertRaises(ApiException, Api, bad_discovery)
    bad_discovery['schemas'] = {
        'NoPropertiesInObject': {'id': 'noprops', 'type': 'object'}
        }
    self.assertRaises(ApiException, Api, bad_discovery)

  def testUndefinedSchema(self):
    # This should generated an empty "Bar" class.
    discovery_doc = {
        'name': 'fake',
        'version': 'v1',
        'schemas': {
            'foo': {
                'id': 'foo',
                'type': 'object',
                'properties': {'basic': {'$ref': 'bar'}}
                }
            },
        'resources': {}
        }
    gen = Api(discovery_doc)
    # We expect foo to be in the list because the id is 'foo'
    self.assertTrue('foo' in gen._schemas.keys())
    # We expect 'Foo' to be in the list because that is the class name we would
    # create for foo
    self.assertTrue('Foo' in gen._schemas.keys())
    # We do not expect Bar to be in the list because we only have a ref to it
    # but no definition.
    self.assertFalse('Bar' in gen._schemas.keys())

  def testEnums(self):
    gen = self.ApiFromDiscoveryDoc('enums.json')
    # Find the method with the enums
    r1 = FindByWireName(gen.values['resources'], 'r1')
    methods = r1.values['methods']
    m1 = FindByWireName(methods, 'm1')
    language = [p for p in m1.values['parameters']
                if p.values['wireName'] == 'language'][0]
    e = language.values['enumType']
    for name, value, desc in e.values['pairs']:
      self.assertTrue(name in ['ENGLISH', 'ITALIAN', 'LANG_ZH_CN',
                               'LANG_ZH_TW'])
      self.assertTrue(value in ['english', 'italian', 'lang_zh-CN',
                                'lang_zh-TW'])
      self.assertTrue(desc in ['English (US)', 'Italian',
                               'Chinese (Simplified)', 'Chinese (Traditional)'])

  def testPostVariations(self):
    gen = self.ApiFromDiscoveryDoc('post_variations.json')
    # Check a normal GET method to make sure it has no request and does have
    # a response
    r1 = FindByWireName(gen.values['resources'], 'r1')
    methods = r1.values['methods']
    m = FindByWireName(methods, 'get')
    self.assertIsNone(m.values['requestType'])
    self.assertEquals('Task', m.values['responseType'].class_name)
    # A normal POST with both a request and response
    m = FindByWireName(methods, 'insert')
    self.assertEquals('Task', m.values['requestType'].class_name)
    self.assertEquals('Task', m.values['responseType'].class_name)
    # A POST with neither request nor response
    m = FindByWireName(methods, 'no_request_no_response')
    self.assertIsNone(m.values.get('requestType'))
    self.assertTrue(isinstance(m.values.get('responseType'), data_types.Void))
    # A POST with no request
    m = FindByWireName(methods, 'no_request')
    self.assertIsNone(m.values.get('requestType'))
    self.assertEquals('Task', m.values['responseType'].class_name)
    # A PUT with no response
    m = FindByWireName(methods, 'no_response')
    self.assertEquals('TaskList', m.values['requestType'].class_name)
    self.assertTrue(isinstance(m.values.get('responseType'), data_types.Void))

  def testSchemaParenting(self):
    gen = self.ApiFromDiscoveryDoc(self.__TEST_DISCOVERY_DOC)
    # Check that top level schemas have no parent
    for schema in ['Activity', 'Comment']:
      self.assertIsNone(gen._schemas[schema].parent)
    for schema in ['PersonUrls', 'ActivityObject', 'ActivityObjectAttachments']:
      self.assertTrue(gen._schemas[schema].parent)
    for name, schema in gen._schemas.items():
      if schema.parent and schema.parent != gen:
        self.assertTrue(name.startswith(schema.parent.values['className']))
        self.assertNotEquals(name, schema.parent.values['className'])


def FindByWireName(list_of_resource_or_method, wire_name):
  """Find an element in a list by its "wireName".

  The "wireName" is the name of the method "on the wire", which is the raw name
  as it appears in the JSON.

  Args:
    list_of_resource_or_method: A list of resource or methods as annotated by
      the Api.
    wire_name: (str): the name to fine.

  Returns:
    dict or None
  """
  for x in list_of_resource_or_method:
    if x.values['wireName'] == wire_name:
      return x
  return None

if __name__ == '__main__':
  basetest.main()
