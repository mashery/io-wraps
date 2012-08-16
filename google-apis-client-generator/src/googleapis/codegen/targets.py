#!/usr/bin/python
#
# Copyright 2011 Google Inc. All Rights Reserved.

"""Targets class describes which languages/platforms we support."""

__author__ = 'wclarkso@google.com (Will Clarkson)'

import os

from googleapis.codegen.anyjson import simplejson


class Selection(object):
  """Represents a selection of one target."""

  def __init__(self, api_name, api_version, language, platform,
               language_variant):
    self.api_name = api_name
    self.api_version = api_version
    self.language = language
    self.platform = platform
    self.language_variant = language_variant

  @staticmethod
  def FromRequest(request):
    """Construct a Selection from App Engine Request query parameters.

    The query parameters must be 'api', 'version', 'language', 'platform', and
    'language_variant'.

    Args:
      request: (dict) A dictionary of parsed query parameters.

    Returns:
      Selection object populated from query parameters.
    """
    return Selection(request.get('api'), request.get('version'),
                     request.get('language'), request.get('platform'),
                     request.get('language_variant'))

  def ToName(self):
    """Return a nice name for this selection, usable as a file name."""
    return '%s-%s-%s-%s-%s' % (self.api_name, self.api_version, self.language,
                               self.platform, self.language_variant)


class Targets(object):
  """Targets maintains the list of possible target options.

  Reads targets.json file in local directory. This file is formatted
  as:
  {
  'languages': {
    'languageA': {
      'surface_option1': {
        'releaseVersion': 'v1.0'
        'path': 'stable',
        'description': 'something about language A',
        'displayName': 'SurfaceOption1',
        'platforms': ['cmd-line', 'appengine'],
        'skeleton': false,
        'library': true,
      },
      'surface_option2': {
        'releaseVersion': 'v2.0'
        'path': 'experimental',
        'description': 'something about language A',
        'displayName': 'SurfaceOption2',
        'platforms': ['cmd-line'],
        'skeleton': true
        'library': false,
      }
     },
    'languageB': {
      ...
    }, ...
    },
  'platforms': {
    'platform': {
      'displayName': 'Pretty Platform Name',
    }
   }
  }
  """

  def __init__(self, targets_path=None):
    """Constructor.

    Loads targets file.

    Args:
      targets_path: (str) Path to targets file. Defaults to './targets.json'

    Raises:
      ValueError: if the targets file does not contain the required sections.
    """
    if not targets_path:
      targets_path = os.path.join(os.path.dirname(__file__), 'targets.json')
    targets_file = open(targets_path)
    self._targets_dict = simplejson.loads(targets_file.read())
    targets_file.close()

    # Do some basic validation that this has the required fields
    if ('languages' not in self._targets_dict or
        'platforms' not in self._targets_dict):
      raise ValueError('languages or platforms is not in targets.json')

  def IsValid(self, selection):
    """Returns True if the selection is valid."""
    try:
      language_variants = self.TargetsForLanguage(selection.language)
      variant_features = language_variants[selection.language_variant]
      return selection.platform in variant_features['platforms']
    except KeyError:
      return False

  def Dict(self):
    """The targets.json file as a dictionary."""
    return self._targets_dict

  def TargetsForLanguage(self, language):
    return self._targets_dict['languages'][language]['surface_options']

  def GetLanguage(self, language):
    return self._targets_dict['languages'][language]

  def Languages(self):
    return self._targets_dict['languages']

  def Platforms(self):
    return self._targets_dict['platforms']

  def SupportsSkeletons(self, selection):
    """Returns True if the selected target supports skeletons."""
    language_variants = self.TargetsForLanguage(selection.language)
    variant_features = language_variants.get(selection.language_variant, {})
    return variant_features.get('skeleton', False)

  def Path(self, selection):
    """Returns the path of the selected target."""
    language_variants = self.TargetsForLanguage(selection.language)
    variant_features = language_variants.get(selection.language_variant, {})
    return variant_features.get('path', '')
