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

"""Tests for java_generator."""

__author__ = 'aiuto@google.com (Tony Aiuto)'

from google.apputils import basetest
from googleapis.codegen import java_generator


class JavaApiTest(basetest.TestCase):

  def testToClassName(self):
    """Test creating safe class names from object names."""
    api = java_generator.JavaApi({
        'name': 'dummy',
        'version': 'v1',
        'resources': {}
        })
    self.assertEquals('Foo', api.ToClassName('foo'))
    self.assertEquals('DummyClass', api.ToClassName('class'))
    self.assertEquals('DummyDefault', api.ToClassName('default'))
    self.assertEquals('DummyImport', api.ToClassName('import'))
    self.assertEquals('DummyObject', api.ToClassName('object'))
    self.assertEquals('DummyString', api.ToClassName('string'))
    self.assertEquals('DummyTrue', api.ToClassName('true'))

  def testGetCodeTypeFromDictionary(self):
    """Test mapping of JSON schema types to Java class names."""
    language_model = java_generator.JavaLanguageModel()
    test_cases = [
        ['String', {'type': 'string', 'format': 'byte'}],
        ['DateTime', {'type': 'string', 'format': 'date-time'}],
        ['Double', {'type': 'number', 'format': 'double'}],
        ['Float', {'type': 'number', 'format': 'float'}],
        ['Short', {'type': 'integer', 'format': 'int16'}],
        ['Integer', {'type': 'integer', 'format': 'int32'}],
        ['Long', {'type': 'string', 'format': 'int64'}],
        ['Object', {'type': 'any'}],
        ['Boolean', {'type': 'boolean'}],
        ['String', {'type': 'string'}],
        ['Long', {'type': 'integer', 'format': 'uint32'}],
        ['BigInteger', {'type': 'string', 'format': 'uint64'}],
    ]

    for test_case in test_cases:
      self.assertEquals(
          test_case[0],
          language_model.GetCodeTypeFromDictionary(test_case[1]))

if __name__ == '__main__':
  basetest.main()
