#!/usr/bin/python2.6
#
# Copyright 2011 Google Inc. All Rights Reserved.

"""ObjC library generator.

This module generates a an Objective-C client library for a Discovery based API.
"""

__author__ = 'aiuto@google.com (Tony Aiuto)'

from googleapis.codegen import api
from googleapis.codegen import data_types
from googleapis.codegen import generator
from googleapis.codegen import language_model
from googleapis.codegen import template_objects
from googleapis.codegen import utilities


class ObjCGenerator(generator.ApiLibraryGenerator):
  """The ObjC code generator."""

  def __init__(self, discovery, options=dict()):
    super(ObjCGenerator, self).__init__(ObjCApi,
                                        discovery,
                                        language='objc',
                                        language_model=ObjCLanguageModel(),
                                        options=options)

  def AnnotateApi(self, the_api):
    package_path = 'google/api/services/%s' % the_api.values['name']
    self._package = template_objects.Package(package_path,
                                             language_model=self.language_model)
    the_api.SetTemplateValue('package', self._package)
    self._model_package = self._package

  def AnnotateSchema(self, unused_api, schema):
    schema.SetTemplateValue('superClass', 'GTLObject')

  def AnnotateProperty(self, unused_api, prop, schema):
    """Annotate a Property with ObjC specific elements."""
    if isinstance(prop.data_type, data_types.ArrayDataType):
      # Set my superclass correctly if I am an array
      schema.SetTemplateValue('superClass', 'GTLCollectionObject')


class ObjCLanguageModel(language_model.LanguageModel):
  """A LanguageModel for Objective-C."""

  _SCHEMA_TYPE_TO_OBJC_TYPE = {
      'any': 'String',
      'boolean': 'NSNumber',
      'integer': 'NSNumber',
      'long': 'NSNumber',
      'number': 'NSNumber',
      'string': 'NSString',
      'object': 'GTLObject',
      }

  _OBJC_KEYWORDS = [
      'any', 'boolean', 'bycopy', 'byref', 'char', 'const', 'double', 'float',
      'id', 'in', 'inout', 'int', 'integer', 'long', 'number', 'object',
      'oneway', 'out', 'self', 'short', 'signed', 'string', 'super', 'unsigned',
      'void', 'volatile',
      ]

  # We can not create classes which match a ObjC keyword or built in object
  # type.
  RESERVED_CLASS_NAMES = _OBJC_KEYWORDS + [
      'float', 'integer', 'object', 'string', 'true', 'false',
      ]

  # We can not create data members which are in GTLObject.
  RESERVED_MEMBER_NAMES = _OBJC_KEYWORDS + [
      'description', 'id'
      ]

  def GetCodeTypeFromDictionary(self, def_dict):
    """Convert a json primitive type to a suitable ObjC type name.

    Overrides the default.

    Args:
      def_dict: (dict) A dictionary describing Json schema for this Property.
    Returns:
      A name suitable for use as a class in the generator's target language.
    """
    json_type = def_dict.get('type', 'string')
    native_format = self._SCHEMA_TYPE_TO_OBJC_TYPE.get(json_type, json_type)
    return native_format

  def CodeTypeForArrayOf(self, unused_type_name):
    """Take a type name and return the syntax for an array of them.

    Overrides the default.

    Args:
      unused_type_name: (str) A type name.
    Returns:
      A language specific string meaning "an array of type_name".
    """
    return 'NSArray'

  def CodeTypeForMapOf(self, type_name):
    """Take a type name and return the syntax for an array of them.

    Overrides the default.

    Args:
      type_name: (str) A type name.
    Returns:
      A language specific string meaning "an array of type_name".
    """
    return 'NSMap<%s>' % type_name

  def ToMemberName(self, s, unused_api):
    """Convert a wire format name into a suitable ObjC variable name."""
    camel_s = utilities.CamelCase(s)
    ret = camel_s[0].lower() + camel_s[1:]
    if s.lower() in ObjCLanguageModel.RESERVED_MEMBER_NAMES:
      ret = '%sProperty' % ret
    return ret


class ObjCApi(api.Api):
  """An Api with Objective-C annotations."""

  def __init__(self, discovery_doc, **unused_kwargs):
    super(ObjCApi, self).__init__(discovery_doc)

  def ToClassName(self, s, element_type=None):
    """Convert a discovery name to a suitable ObjC class name.

    Overrides the default.

    Args:
      s: (str) A rosy name of data element.
      element_type: (str) The kind of element to name.
    Returns:
      A name suitable for use as a class in the generator's target language.
    """
    if ((s.lower() in ObjCLanguageModel.RESERVED_CLASS_NAMES)
        or (element_type == 'schema')):
      # Prepend the service name
      s = '%s%s' % (utilities.CamelCase(self.values['name']),
                    utilities.CamelCase(s))
    else:
      s = utilities.CamelCase(s)
    if not s.startswith('GTL'):
      return 'GTL' + s
    return s
