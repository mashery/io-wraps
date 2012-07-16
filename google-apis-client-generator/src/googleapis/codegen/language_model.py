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

"""A class holding utilities and concepts specific to a programming language.

The LanguageModel class contains conceptual elements which are common to
programming languages, but differ in the details. For example, this class
had the concept of the delimiter between parts of a package. In Java this
would be a '.', in C++ a '::'.
"""
__author__ = 'aiuto@google.com (Tony Aiuto)'

from googleapis.codegen import utilities


class LanguageModel(object):
  """The base class for all LanguageModels."""

  def __init__(self,
               class_name_delimiter='.',
               package_name_delimiter=None):
    """Create a LanguageModel.

    Args:
      class_name_delimiter: (str) The string which delimits parts of a class
          name in code.
      package_name_delimiter: (str) The string which delimits parts of a package
          name in code. Defaults to class_name_delimiter
    """
    super(LanguageModel, self).__init__()
    self._class_name_delimiter = class_name_delimiter
    self._package_name_delimiter = (
        package_name_delimiter or class_name_delimiter)

  @property
  def class_name_delimiter(self):
    return self._class_name_delimiter

  @property
  def package_name_delimiter(self):
    return self._package_name_delimiter

  def GetCodeTypeFromDictionary(self, json_schema):
    """Convert a json schema primitive type into the most suitable class name.

    Subclasses should override as appropriate.

    Args:
      json_schema: (dict) The defintion dictionary for this type
    Returns:
      A name suitable for use as a class in the generator's target language.
    """
    raise NotImplementedError(
        'Subclasses of LanguageModel must implement GetCodeTypeFromDictionary')

  def CodeTypeForArrayOf(self, type_name):
    """Take a type name and return the syntax for an array of them.

    Subclasses must override as appropriate. The base definition is only OK for
    debugging.

    Args:
      type_name: (str) A type name.
    Returns:
      A language specific string meaning "an array of type_name".
    """
    print 'Array[%s]' % type_name
    raise NotImplementedError(
        'Subclasses of LanguageModel must implement CodeTypeForArrayOf')

  def CodeTypeForMapOf(self, type_name):
    """Take a type name and return the syntax for a map of strings of them.

    Subclasses must override as appropriate. The base definition is only OK for
    debugging.

    Args:
      type_name: (str) A type name.
    Returns:
      A language specific string meaning "an array of type_name".
    """
    print 'Map<string, %s>' % type_name
    raise NotImplementedError(
        'Subclasses of LanguageModel must implement CodeTypeForMapOf')

  def CodeTypeForVoid(self):
    """Return the type name for a void.

    Subclasses may override this default implementation.

    Returns:
      (str) 'void'
    """
    return 'void'

  def ToMemberName(self, s, api):  # pylint: disable-msg=W0613
    """Convert a name to a suitable member name in the target language.

    Subclasses should override as appropriate.

    Args:
      s: (str) A canonical name for data element. (Usually the API wire format)
      api: (Api) The API this element is part of. For use as a hint when the
        name cannot be used directly.
    Returns:
      A name suitable for use as an element in the generator's target language.
    """
    return s

  def ToSafeClassName(self, s, api):  # pylint: disable-msg=W0613
    """Convert a name to a suitable class name in the target language.

    Subclasses should override as appropriate.

    Args:
      s: (str) A canonical name for data element. (Usually the API wire format)
      api: (Api) The API this element is part of. For use as a hint when the
        name cannot be used directly.
    Returns:
      A name suitable for use as an element in the generator's target language.
    """
    return utilities.CamelCase(s)
