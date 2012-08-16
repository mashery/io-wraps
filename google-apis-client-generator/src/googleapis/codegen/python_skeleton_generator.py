#!/usr/bin/python
# Copyright 2011 Google Inc. All Rights Reserved.

"""Python Skeleton Generator.

Generates code sample skeletons for Python.
"""

__author__ = 'jcgregorio@google.com (Joe Gregorio)'

from googleapis.codegen import generator


class PythonSkeletonGenerator(generator.TemplateGenerator):
  """Python skeleton generator."""

  def __init__(self, language_model=None, options=None):
    if options is None:
      options = dict()
    super(PythonSkeletonGenerator, self).__init__(language_model, options)

  def GeneratePackage(self, package_writer):
    dev_console = {
        'client_secret_url': self._options['client_secret_url']
        }
    variables = {
        'api': self._language_model,
        'dev_console': dev_console
        }
    self.WalkTemplateTree('skeleton', {}, variables, None, package_writer)
