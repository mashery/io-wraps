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

"""Go library generator.

Specializations to the code Generator for Go bindings.
"""

__author__ = 'wgg@google.com (Wolfgang Grieskamp)'

from googleapis.codegen import api
from googleapis.codegen import generator
from googleapis.codegen import language_model
from googleapis.codegen import utilities


class GoGenerator(generator.ApiLibraryGenerator):
  """The Go code generator."""

  def __init__(self, discovery, options=dict()):
    super(GoGenerator, self).__init__(GoApi, discovery,
                                      language='go',
                                      language_model=GoLanguageModel(),
                                      options=options)

    # Main class name is package (and file) name in Go. Make it lower character
    self._api.values['className'] = self._api.values['className'].lower()

    # Annotate resources with field name
    for resource in self._api.values['resources']:
      resource.values['accessorName'] = utilities.CamelCase(
          resource.values['wireName'])

  def AnnotateMethod(self, the_api, method, resource):
    """Annotate a Method with Go specific elements."""
    # Let the default behavior annotate all our parameters.
    super(GoGenerator, self).AnnotateMethod(the_api, method, resource)
    method.SetTemplateValue('className', '%sCall' % method.values['className'])

  def AnnotateParameter(self, unused_method, parameter):
    """Annotate a Parameter with Go specific elements."""
    parameter.SetTemplateValue('codeName', self.UncapFirst(parameter.codeName))

  @staticmethod
  def UncapFirst(text):
    return text[0].lower() + text[1:]


class GoApi(api.Api):
  """An Api with Go annotations."""

  def __init__(self, discovery_doc, **unused_kwargs):
    super(GoApi, self).__init__(discovery_doc)

  def ToClassName(self, s, element_type=None):  # pylint: disable-msg=W0613
    """Convert a discovery name to a suitable Go type name.

    Overrides the default.

    Args:
      s: (str) A rosy name of data element.
      element_type: (str) The kind of object we need a class name for.
    Returns:
      A name suitable for use as a class in the generator's target language.
    """
    if s.lower() in GoLanguageModel.RESERVED_NAMES:
      class_name = '%s%s' % (utilities.CamelCase(self.values['name']),
                             utilities.CamelCase(s))
    else:
      class_name = utilities.CamelCase(s)
    if element_type == 'resource':
      class_name = '%sResource' % class_name
    return class_name


class GoLanguageModel(language_model.LanguageModel):
  """A LanguageModel for Go."""

  _SCHEMA_TYPE_TO_GO_TYPE = {
      'any': 'interface{}',
      'boolean': 'bool',
      'integer': 'int32',
      'long': 'int64',
      'number': 'float64',
      'string': 'string',
      'object': 'interface{}',
      'uint32': 'uint32',
      'uint64': 'uint64',
      'int32': 'int32',
      'int64': 'int64',
      'double': 'float64',
      'float': 'float32',
      }

  _GO_KEYWORDS = [
      'break', 'case', 'chan', 'const', 'continue',
      'default', 'defer', 'else', 'fallthrough', 'for',
      'func', 'go', 'goto', 'if', 'import',
      'interface', 'map', 'package', 'range', 'return',
      'select', 'struct', 'switch', 'type', 'var'
      ]

  # We can not create names which match a Go keyword or predeclared types
  RESERVED_NAMES = _GO_KEYWORDS + [
      'bool', 'uint8', 'uint16', 'uint32', 'uint64',
      'int8', 'int16', 'int32', 'int64', 'float32', 'float64',
      'complex64', 'complex128', 'byte', 'uint', 'uintptr',
      'string'
      ]

  def __init__(self):
    super(GoLanguageModel, self).__init__(class_name_delimiter='.')

  def GetCodeTypeFromDictionary(self, def_dict):
    # pylint: disable-msg=W0613
    """Convert a json primitive type to a suitable Go type name.

    Overrides the default.

    Args:
      def_dict: (dict) A dictionary describing Json schema for this Property.
    Returns:
      A name suitable for use as a type in the generator's target language.
    """
    json_type = def_dict.get('type', 'string')
    json_format = def_dict.get('format')
    native_format = self._SCHEMA_TYPE_TO_GO_TYPE.get(json_type, json_format)
    return native_format

  def CodeTypeForArrayOf(self, type_name):
    """Take a type name and return the syntax for an array of them.

    Overrides the default.

    Args:
      type_name: (str) A type name.
    Returns:
      A language specific string meaning "an array of type_name".
    """
    return '[]%s' % type_name

  def CodeTypeForMapOf(self, type_name):
    """Take a type name and return the syntax for a map of String to them.

    Overrides the default.

    Args:
      type_name: (str) A type name.
    Returns:
      A language specific string meaning "an array of type_name".
    """
    return 'map[string] %s' % type_name

  def ToMemberName(self, s, the_api):
    """CamelCase a wire format name into a suitable Go variable name."""
    if s.lower() in GoLanguageModel.RESERVED_NAMES:
      # Prepend the service name
      return '%s%s' % (utilities.CamelCase(the_api.values['name']),
                       utilities.CamelCase(s))
    return utilities.CamelCase(s)
