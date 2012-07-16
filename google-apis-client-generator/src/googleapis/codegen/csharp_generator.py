#!/usr/bin/python2.6
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

"""C# library generator.

This module generates C# code from a Google API discovery documents.
"""

__author__ = 'aiuto@google.com (Tony Aiuto)'

from googleapis.codegen import api
from googleapis.codegen import generator
from googleapis.codegen import language_model
from googleapis.codegen import template_objects
from googleapis.codegen import utilities


class CSharpLanguageModel(language_model.LanguageModel):
  """A LanguageModel for C#."""

  # TODO(user): Fix these 3 tables
  _SCHEMA_TYPE_TO_CSHARP_TYPE = {
      'any': 'object',
      'boolean': 'Boolean',
      'integer': 'Integer',
      'long': 'Long',
      'number': 'Double',
      'string': 'string',
      'object': 'object',
      }

  _CSHARP_KEYWORDS = [
      'abstract', 'as', 'base', 'bool', 'break', 'byte', 'case', 'catch',
      'char', 'checked', 'class', 'const', 'continue', 'decimal', 'default',
      'delegate', 'do', 'double', 'else', 'enum', 'event', 'explicit', 'extern',
      'false', 'finally', 'fixed', 'float', 'for', 'foreach', 'goto', 'if',
      'implicit', 'in', 'int', 'interface', 'internal', 'is', 'lock', 'long',
      'namespace', 'new', 'null', 'object', 'operator', 'out', 'override',
      'params', 'private', 'protected', 'public', 'readonly', 'ref', 'return',
      'sbyte', 'sealed', 'short', 'sizeof', 'stackalloc', 'static', 'string',
      'struct', 'switch', 'this', 'throw', 'true', 'try', 'typeof', 'uint',
      'ulong', 'unchecked', 'unsafe', 'ushort', 'using', 'virtual', 'void',
      'volatile', 'while',
      ]

  # We can not create classes which match a C# keyword or built in object
  # type.
  RESERVED_CLASS_NAMES = _CSHARP_KEYWORDS + [
      'float', 'integer', 'object', 'string', 'true', 'false',
      ]

  def __init__(self):
    super(CSharpLanguageModel, self).__init__(class_name_delimiter='.')

  def GetCodeTypeFromDictionary(self, def_dict):
    """Gets an element's data type from its JSON definition.

    Overrides the default.

    Args:
      def_dict: (dict) The defintion dictionary for this type
    Returns:
      A name suitable for use as a C# data type
    """
    json_type = def_dict.get('type', 'string')
    native_type = self._SCHEMA_TYPE_TO_CSHARP_TYPE.get(json_type)
    # TODO(user): Handle JsonString style for string/int64, which should
    # be a Long.
    return native_type

  def CodeTypeForArrayOf(self, type_name):
    """Take a type name and return the syntax for an array of them.

    Overrides the default.

    Args:
      type_name: (str) A type name.
    Returns:
      (str) A C# specific string meaning "an array of type_name".
    """
    return 'IList<%s>' % type_name

  def CodeTypeForMapOf(self, type_name):
    """Take a type name and return the syntax for an array of them.

    Overrides the default.

    Args:
      type_name: (str) A type name.
    Returns:
      (str) A C# specific string meaning "a Map of string to type_name".
    """
    return 'IMap<string, %s>' % type_name

  def ToMemberName(self, s, the_api):
    """CamelCase a wire format name into a suitable C# variable name."""
    camel_s = utilities.CamelCase(s)
    if s.lower() in self.RESERVED_CLASS_NAMES:
      # Prepend the service name
      return '%s%s' % (the_api.values['name'], camel_s)
    return camel_s[0].lower() + camel_s[1:]

CSHARP_LANGUAGE_MODEL = CSharpLanguageModel()


class CSharpGenerator(generator.ApiLibraryGenerator):
  """The C# code generator."""

  def __init__(self, discovery, options=dict()):
    super(CSharpGenerator, self).__init__(
        CSharpApi,
        discovery,
        language='csharp',
        language_model=CSHARP_LANGUAGE_MODEL,
        options=options)

  def AnnotateApi(self, the_api):
    """Overrides the default."""
    package_path = 'Google/Apis/%s' % the_api.values['className']
    if self._options.get('version_package'):
      package_path = '%s/%s' % (package_path, the_api.values['versionNoDots'])
    self._package = template_objects.Package(package_path,
                                             language_model=self.language_model)
    the_api.SetTemplateValue('package', self._package)
    self._model_package = template_objects.Package('Data',
                                                   parent=self._package)


class CSharpApi(api.Api):
  """An Api with C# annotations."""

  def __init__(self, discovery_doc, **unused_kwargs):
    super(CSharpApi, self).__init__(discovery_doc)

  def ToClassName(self, s, element_type=None):  # pylint: disable-msg=W0613
    """Convert a discovery name to a suitable C# class name.

    Overrides the default.

    Args:
      s: (str) A rosy name of data element.
      element_type: (str) The kind of element (resource|method) to name.
    Returns:
      A name suitable for use as a class in the generator's target language.
    """

    if s.lower() in CSharpLanguageModel.RESERVED_CLASS_NAMES:
      # Prepend the service name
      return '%s%s' % (utilities.CamelCase(self.values['name']),
                       utilities.CamelCase(s))
    return utilities.CamelCase(s)
