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


"""Tests for name_validator.py."""

__author__ = 'wclarkso@google.com (Will Clarkson)'

from google.apputils import basetest
from googleapis.codegen import name_validator


class NameValidatorTest(basetest.TestCase):

  def testVariableNameValidator(self):
    validator = name_validator.NameValidator()
    good_names = ['$ref', '_a', '_private', 'a_var.name', 't1', 'max-results']
    bad_names = ['$', '1st_result', '^test', '.variable', '1', '_',
                 'not_valid.', 'no spaces', 'no/slash']

    for varname in good_names:
      validator.Validate(varname)
    for varname in bad_names:
      print "'%s'" % varname
      self.assertRaises(ValueError, validator.Validate, varname)

  def testApiNameValidator(self):
    validator = name_validator.NameValidator()
    good_names = ['valid', 'isValid', 'is2Valid']
    bad_names = ['1noLeadingNumbers', '^test', 'NotValid', 'no-dash',
                 'dot.is.not.valid', 'no spaces', 'no/slash', 'no:colon']

    for varname in good_names:
      validator.ValidateApiName(varname)
    for varname in bad_names:
      print "'%s'" % varname
      self.assertRaises(ValueError, validator.ValidateApiName, varname)

  def testApiVersionValidator(self):
    validator = name_validator.NameValidator()
    good_names = ['v1', 'v1.2', '1.2']
    bad_names = ['.1', 'v1_2', '1 2', 'no-dash', 'no spaces', 'no/slash',
                 'no:colon']

    for varname in good_names:
      validator.ValidateApiVersion(varname)
    for varname in bad_names:
      print "'%s'" % varname
      self.assertRaises(ValueError, validator.ValidateApiVersion, varname)

  def testCommentValidator(self):
    validator = name_validator.NameValidator()
    good_comments = ['Responses with Content-Type',
                     'application/json',
                     ',',
                     '[minimum: 4.4.1]',
                     'API key. Your API key identifies your project',
                     'OAuth 2.0 token for the current user.']
    # A list of input comments, and their expected replacements
    bad_comments = [('/*', ''),
                    ('*/', ''),
                    ('\"""', ''),
                    ('///', ''),
                    ('\\*', ''),
                    ('/*Some Comment String*/', 'Some Comment String'),
                    ('\""" A long comment string """',
                     ' A long comment string '),
                    ('///Escaped comment string', 'Escaped comment string'),
                   ]

    for comment in good_comments:
      validator.ValidateAndSanitizeComment(comment)
    for comment, replacement in bad_comments:
      self.assertEqual(replacement,
                       validator.ValidateAndSanitizeComment(comment))


if __name__ == '__main__':
  basetest.main()
