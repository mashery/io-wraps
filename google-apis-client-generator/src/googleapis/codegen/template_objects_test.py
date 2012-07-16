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

"""Tests for template_objects.py."""

__author__ = 'aiuto@google.com (Tony Aiuto)'

from google.apputils import basetest

from googleapis.codegen import template_objects
from googleapis.codegen.language_model import LanguageModel


class TemplateObjectsTest(basetest.TestCase):

  def setUp(self):
    super(TemplateObjectsTest, self).setUp()
    self.language_model = LanguageModel(class_name_delimiter='|')

  def testFullyQualifiedClassName(self):
    foo = template_objects.CodeObject({'className': 'Foo'}, None,
                                      language_model=self.language_model)
    bar = template_objects.CodeObject({'className': 'Bar'}, None, parent=foo)
    baz = template_objects.CodeObject({'className': 'Baz'}, None, parent=bar)

    self.assertEquals('Foo|Bar|Baz', baz.fullClassName)
    self.assertEquals('', baz.RelativeClassName(baz))
    self.assertEquals('Baz', baz.RelativeClassName(bar))
    self.assertEquals('Bar|Baz', baz.RelativeClassName(foo))

  def testPackage(self):
    p = template_objects.Package('hello/world',
                                 language_model=self.language_model)
    self.assertEquals('hello|world', p.name)
    self.assertEquals('hello/world', p.path)

  def testPackageParenting(self):
    p = template_objects.Package('hello/world',
                                 language_model=self.language_model)
    child = template_objects.Package('everyone', parent=p)
    self.assertEquals('hello|world|everyone', child.name)
    self.assertEquals('hello/world/everyone', child.path)

  def testPackageNaming(self):
    p = template_objects.Package('hello/world',
                                 language_model=self.language_model)
    foo = template_objects.CodeObject({'className': 'Foo'}, None,
                                      language_model=self.language_model)
    foo.SetTemplateValue('package', p)
    bar = template_objects.CodeObject({'className': 'Bar'}, None, parent=foo)
    baz = template_objects.CodeObject({'className': 'Baz'}, None, parent=bar)

    self.assertEquals('Foo|Bar|Baz', baz.packageRelativeClassName)
    self.assertEquals('hello|world|Foo|Bar|Baz', baz.fullClassName)


if __name__ == '__main__':
  basetest.main()
