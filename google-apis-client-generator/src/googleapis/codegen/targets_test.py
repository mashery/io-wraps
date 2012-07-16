#!/usr/bin/python2.6
# Copyright 2011 Google Inc. All Rights Reserved.


__author__ = 'jcgregorio@google.com (Joe Gregorio)'

import os

from google.apputils import basetest
from googleapis.codegen import targets


class TargetsTest(basetest.TestCase):
  def setUp(self):
    self.t = targets.Targets(os.path.join(os.path.dirname(__file__),
                                          'testdata', 'targets_test.json'))

  def testTargetsAccessors(self):
    rawdata = self.t.Dict()
    self.assertTrue('languages' in rawdata)

    self.assertTrue('preview' in self.t.TargetsForLanguage('java'))
    self.assertTrue('stable' in self.t.TargetsForLanguage('python'))
    self.assertTrue('displayName' in self.t.GetLanguage('java'))
    self.assertTrue('python' in self.t.Languages())
    self.assertTrue('cmd-line' in self.t.Platforms())

  def testTargetsSelectorAccessors(self):
    s = targets.Selection('plus', 'v1', 'python', 'cmd-line', 'stable')

    self.assertTrue(self.t.IsValid(s))
    self.assertTrue(self.t.SupportsSkeletons(s))
    self.assertEquals('stable', self.t.Path(s))

  def testTargetsSelectorAccessorsInvalid(self):
    # Currently no checking for validity of api name or version.
    s = targets.Selection('----', '--', 'python', 'cmd-line', 'stable')
    self.assertTrue(self.t.IsValid(s))

    # Everything else should be validated.
    s = targets.Selection('plus', 'v1', '------', 'cmd-line', 'stable')
    self.assertFalse(self.t.IsValid(s))
    s = targets.Selection('plus', 'v1', 'python', '--------', 'stable')
    self.assertFalse(self.t.IsValid(s))
    s = targets.Selection('plus', 'v1', 'python', 'cmd-line', '------')
    self.assertFalse(self.t.IsValid(s))


class SelectionTest(basetest.TestCase):
  def setUp(self):
    self.t = targets.Targets(os.path.join(os.path.dirname(__file__),
                                          'testdata', 'targets_test.json'))

  def testSelectionAccessors(self):
    s = targets.Selection('plus', 'v1', 'python', 'cmd-line', 'stable')
    self.assertEquals('plus-v1-python-cmd-line-stable', s.ToName())

  def testSelectionFromRequest(self):
    """Test constructing from an App Engine WebOb Request."""
    request = {
        'api': 'buzz',
        'version': 'v1',
        'language': 'java',
        'platform': 'cmd-line',
        'language_variant': 'preview',
        }
    s = targets.Selection.FromRequest(request)
    self.assertTrue(self.t.IsValid(s))

if __name__ == '__main__':
  basetest.main()
