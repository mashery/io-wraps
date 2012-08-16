#!/usr/bin/python
#
# Copyright 2011 Google Inc. All Rights Reserved.
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

"""Tests for go_generator."""

__author__ = 'wgg@google.com (Wolfgang Grieskamp)'

from google.apputils import basetest
from googleapis.codegen import go_generator


class GoApiTest(basetest.TestCase):

  def testToClassName(self):
    """Test creating safe class and member names from object names."""
    api = go_generator.GoApi(
        {'name': 'dummy', 'version': 'v1', 'resources': {}})
    self.assertEquals('Foo', api.ToClassName('foo'))
    self.assertEquals('FooResource', api.ToClassName('foo', 'resource'))
    self.assertEquals('Class', api.ToClassName('class'))
    self.assertEquals('DummyDefault', api.ToClassName('default'))
    self.assertEquals('DummyInt32', api.ToClassName('int32'))
    self.assertEquals('DummyImport', api.ToClassName('import'))
    self.assertEquals('Object', api.ToClassName('object'))
    self.assertEquals('DummyString', api.ToClassName('string'))
    self.assertEquals('DummyInterface', api.ToClassName('interface'))

  def testGetCodeTypeFromDictionary(self):
    """Test mapping of JSON schema types to Go class names."""
    language_model = go_generator.GoLanguageModel()

    test_cases = [
        ['interface{}', {'type': 'any'}],
        ['bool', {'type': 'boolean'}],
        ['int32', {'type': 'integer'}],
        ['float64', {'type': 'number'}],
        ['string', {'type': 'string'}],
    ]

    for test_case in test_cases:
      self.assertEquals(test_case[0],
                        language_model.GetCodeTypeFromDictionary(test_case[1]))

if __name__ == '__main__':
  basetest.main()
