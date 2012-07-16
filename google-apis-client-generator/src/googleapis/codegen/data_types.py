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

"""Template objects which represent data types.

This module contains objects which usable in templates and represent data type
idioms.
"""

__author__ = 'aiuto@google.com (Tony Aiuto)'

from googleapis.codegen import template_objects


class DataType(template_objects.CodeObject):
  """Template object which represents a data type.

  This is the base class for things which might be data type definitions, such
  as Schema objects derived from JSONSchema blocks or primitive types.
  """

  def __init__(self, def_dict, api, parent=None, language_model=None):
    """Construct a DataType.

    Args:
      def_dict: (dict) The discovery dictionary for this element.
      api: (Api) The Api instance which owns this element.
      parent: (CodeObject) The parent of this element.
      language_model: (LanguageModel) The language we are targetting.
        Dynamically defaults to the parent's language model.
    """
    super(DataType, self).__init__(def_dict, api, parent=parent,
                                   language_model=language_model)
    self.SetTemplateValue('wireName', 'DATA_TYPE_FOO')

  @property
  def code_type(self):
    """Returns the string representing this datatype."""
    return self.values.get('codeType', self.values.get('className'))

  @property
  def class_name(self):
    return self.GetTemplateValue('className')

  @property
  def codeType(self):  # pylint: disable-msg=C6409
    """Expose this in template using the template naming convention.

    Just redirect to code_type. Subclasses should not implement codeType
    themselves. They should implement code_type.

    Returns:
      (str) The evaluated code type.
    """
    return self.code_type

  @property
  def safeClassName(self):  # pylint: disable-msg=C6409
    """Returns a language appropriate name for this object.

    This property should only be used during template expansion. It is computed
    once, using the LanguageModel in play, and then that value is cached.

    Returns:
      (str) a name for an instance of this object.
    """
    safe_class_name = self.GetTemplateValue('safe_class_name')
    if not safe_class_name:
      safe_class_name = self.values['wireName']
      language_model = self._FindNearestLanguageModel()
      if language_model:
        safe_class_name = language_model.ToSafeClassName(safe_class_name,
                                                         self._api)
      self.SetTemplateValue('safeClassName', safe_class_name)
    return safe_class_name


class BuiltInDataType(DataType):
  """DataType which represents a "built in" data type.

  BuiltIn types are those which are provided by the language or one of its
  packages, rather than those defined by the API.  A language specific
  generater should annotate BuiltInDataType objects with a specific codeType
  before using them to generate code.
  """

  def __init__(self, def_dict, api, parent=None):
    """Construct a BuiltInDataType.

    Args:
      def_dict: (dict) The discovery dictionary for this element.
      api: (Api) The Api instance which owns this element.
      parent: (TemplateObject) The parent of this object.
    """
    super(BuiltInDataType, self).__init__(def_dict, api, parent=parent)
    self.SetTemplateValue('builtIn', True)

  @property
  def code_type(self):
    language_model = self._FindNearestLanguageModel()
    if language_model:
      s = language_model.GetCodeTypeFromDictionary(self._def_dict)
      return s
    return self.values.get('type')

  @property
  def format(self):
    """Expose the format element from the JSON Schema type definition."""
    return self.values.get('format')

  @property
  def type(self):
    """Expose the type element from the JSON Schema type definition."""
    return self.values.get('type')


class ArrayDataType(DataType):
  """DataType which represents a array of another DataType."""

  def __init__(self, base_type, parent=None):
    """Construct an ArrayDataType.

    Args:
      base_type: (DataType) The DataType to represent an array of.
      parent: (TemplateObject) The parent of this object.
    """
    # Access to protected _language_model OK here. pylint: disable-msg=W0212
    super(ArrayDataType, self).__init__(
        {}, base_type.api, parent=parent,
        language_model=base_type._language_model)
    self._base_type = base_type
    if isinstance(base_type, BuiltInDataType):
      self._base_type.SetParent(self)
    self.SetTemplateValue('arrayOf', base_type.class_name)
    self.SetTemplateValue('className', 'Array-do not generate')

  @property
  def code_type(self):
    """Returns the string representing the datatype of this variable.

    Note: This may should only be called after the language model is set.

    Returns:
      (str) A printable representation of this data type.
    """
    language_model = self._FindNearestLanguageModel()
    return language_model.CodeTypeForArrayOf(self._base_type.code_type)


class MapDataType(DataType):
  """DataType which represents a map of string to another DataType.

  This is the base class for things which might be data type definitions, such
  as Schema objects derived from JSONSchema blocks or primitive types.
  """

  def __init__(self, base_type, parent=None):
    """Construct a MapDataType.

    Args:
      base_type: (DataType) The DataType to represent an map of string to.
      parent: (TemplateObject) The parent of this object.
    """
    # Access to protected _language_model OK here. pylint: disable-msg=W0212
    super(MapDataType, self).__init__({}, base_type.api, parent=parent,
                                      language_model=base_type._language_model)
    self._base_type = base_type
    self._base_type.SetParent(self)
    # Mark me as not generatable
    self.SetTemplateValue('builtIn', True)
    self.SetTemplateValue('className', 'MAP-do not generate')

  @property
  def code_type(self):
    """Returns the string representing the datatype of this variable.

    Note: This may should only be called after the language model is set.

    Returns:
      (str) A printable representation of this data type.
    """
    language_model = self._FindNearestLanguageModel()
    return language_model.CodeTypeForMapOf(self._base_type.code_type)


class SchemaReference(DataType):
  """DataType which represents a type alias to named schema.

  Provides a lazy reference to schema by name.
  """

  def __init__(self, referenced_schema, api):
    """Construct a SchemaReference.

    Args:
      referenced_schema: (str) The name of the schema we are referencing.
      api: (Api) The Api instance which owns this element.

    Returns:
      SchemaReference
    """
    super(SchemaReference, self).__init__({}, api)
    self._referenced_schema = referenced_schema
    # Mark me as not generatable
    self.SetTemplateValue('builtIn', True)
    self.SetTemplateValue('className', referenced_schema)

  @property
  def values(self):
    """Forwards the 'values' property of this object to the referenced object.

    This enables GetTemplateValue called on a Ref to effectively return
    the value for the truly desired schema.

    This may be safely called at any time, but may not produce expected
    results until after the entire API has been parsed. In practice, this
    means that anything done during template expansion is fine.

    Returns:
      dict of values which can be used in template.
    """
    s = self.api.SchemaByName(self._referenced_schema)
    if s:
      return s.values
    return self._def_dict

  @property
  def code_type(self):
    """Returns the string representing the datatype of this variable."""
    s = self.api.SchemaByName(self._referenced_schema)
    if s:
      return s.code_type
    return self._def_dict.get('codeType', self._def_dict.get('className'))

  @property
  def parent(self):
    """Returns the parent of the schema I reference."""
    return self.api.SchemaByName(self._referenced_schema).parent


class Void(DataType):
  """DataType which represents a 'void'.

  Some API methods have no response. To provide some consistency in assigning
  a responseType to these methods, we use the Void data type. When it is
  referenced in a template, it forwards requests for it's code_type to a
  langauge model specific emitter.
  """

  def __init__(self, api):
    """Construct a Void.

    Args:
      api: (Api) The Api instance which owns this element. This is used for
        a parent chain so that we can pick up the language model at template
        generation time.

    Returns:
      Void
    """
    super(Void, self).__init__({}, api, parent=api)
    # Mark me as not generatable
    self.SetTemplateValue('builtIn', True)

  @property
  def code_type(self):
    """Returns the string representing the datatype of this variable."""
    language_model = self._FindNearestLanguageModel()
    if language_model:
      return language_model.CodeTypeForVoid()
    return 'void'

  @property
  def fullClassName(self):  # pylint: disable-msg=C6409
    return self.code_type
