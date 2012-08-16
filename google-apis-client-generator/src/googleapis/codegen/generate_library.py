#!/usr/bin/python
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


"""Command line tool to run the Google API library generator.
Usage:
$ PYTHONPATH=$(/bin/pwd)/src \
  $(/bin/pwd)/src/googleapis/codegen/generate_library.py \
    --api_name=buzz --api_version=v1 --output_dir=buzz_lib
"""

__author__ = 'aiuto@google.com (Tony Aiuto)'

import os

import httplib2


import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

from google.apputils import app
import gflags as flags
from googleapis.codegen.anyjson import simplejson
from googleapis.codegen.csharp_generator import CSharpGenerator
from googleapis.codegen.filesystem_library_package import FilesystemLibraryPackage
from googleapis.codegen.go_generator import GoGenerator
from googleapis.codegen.gwt_generator import GwtGenerator
from googleapis.codegen.java_generator import JavaGenerator
from googleapis.codegen.objc_generator import ObjCGenerator
from googleapis.codegen.php_generator import PHPGenerator
from googleapis.codegen.targets import Targets
from googleapis.codegen.zip_library_package import ZipLibraryPackage

DISCOVERY_API_VERSION = 'v1'
FLAGS = flags.FLAGS

flags.DEFINE_string(
    'api_name',
    None,
    'API to generate for.  E.g. "buzz".')
flags.DEFINE_string(
    'api_version',
    None,
    'version of "api_name" to generate for.  E.g. "v1".')
flags.DEFINE_string(
    'discovery_server',
    'www.googleapis.com',
    'The discovery server to use for loading "api_name"')
flags.DEFINE_string(
    'discovery_version',
    DISCOVERY_API_VERSION,
    'The discovery version to use for loading "api_name"')
flags.DEFINE_boolean(
    'include_timestamp',
    False,
    'Adds a timestamp to the generated source files.')
flags.DEFINE_string(
    'input',
    None,
    'A discovery document captured from a discovery service.')
flags.DEFINE_enum(
    'language',
    'java',
    ['csharp', 'go', 'java', 'gwt', 'objc', 'php'],
    'Target language for the generated library')
flags.DEFINE_string(
    'language_variant',
    'default',
    'which variant of "language" to generate for. E.g. "stable" vs. "head".')
flags.DEFINE_string(
    'output_dir',
    None,
    'A path to a directory where the generated files will be created.')
flags.DEFINE_string(
    'output_file',
    None,
    'An output file path to contain the archive for the generated library.'
    ' The contents of the file are determined by the output_format parameter')
flags.DEFINE_enum(
    'output_type',
    'plain',
    ['plain', 'full'],
    'What kind of output to make.'
    ' plain=just the source,'
    ' full=turn on all the optional parts (useful for testing the generator).'
    )
flags.DEFINE_bool('version_package', False, 'Put API version in package paths')

flags.DECLARE_key_flag('api_name')
flags.DECLARE_key_flag('api_version')
flags.DECLARE_key_flag('discovery_server')
flags.DECLARE_key_flag('discovery_version')
flags.DECLARE_key_flag('include_timestamp')
flags.DECLARE_key_flag('input')
flags.DECLARE_key_flag('language')
flags.DECLARE_key_flag('language_variant')
flags.DECLARE_key_flag('output_dir')
flags.DECLARE_key_flag('output_file')
flags.DECLARE_key_flag('output_type')
flags.DECLARE_key_flag('version_package')


def main(unused_argv):
  if not (FLAGS.api_name or FLAGS.input):
    raise app.UsageError('You must specify one of --api_name or --input')
  if not (FLAGS.output_dir or FLAGS.output_file):
    raise app.UsageError(
        'You must specify one of --output_dir or --output_file')

  # Get the discovery document
  if FLAGS.api_name:
    if not FLAGS.api_version:
      raise app.UsageError('You must specify --api_version with --api_name')
    api_path = 'apis/%s/%s/rest' % (FLAGS.api_name, FLAGS.api_version)

    discovery_url = 'https://%s/discovery/%s/%s' % (
        FLAGS.discovery_server, FLAGS.discovery_version, api_path)
    http = httplib2.Http()
    unused_resp, content = http.request(discovery_url)
    discovery_doc = simplejson.loads(content)
    error = discovery_doc.get('error')
    if error:
      raise app.Error(error)
  else:
    f = open(FLAGS.input)
    discovery_doc = simplejson.loads(f.read())
    f.close()

  options = {
      # Emit a manifest file like a source jar
      'emit_manifest': False,
      # Include other files needed to compile (e.g. base jar files)
      'include_dependencies': True,  # WARNING - change to false before commit
      # Put all the sources into a source jar
      'include_source_jar': False,
      # Include the timestamp in the generated library
      'include_timestamp': FLAGS.include_timestamp,
      # Prefix paths in the output with the library name
      'use_library_name_in_path': False,
      # Put API version in the package
      'version_package': FLAGS.version_package,
      }
  if FLAGS.output_type == 'full':
    options['emit_manifest'] = True
    options['include_dependencies'] = True
    options['include_source_jar'] = True
    options['use_library_name_in_path'] = True

  # Instantiate the right code generator
  generators = {
      'csharp': CSharpGenerator,
      'go': GoGenerator,
      'gwt': GwtGenerator,
      'java': JavaGenerator,
      'objc': ObjCGenerator,
      'php': PHPGenerator,
      }
  if FLAGS.language in generators:
    generator = generators[FLAGS.language](discovery_doc, options=options)
  else:
    raise app.UsageError('Unsupported language option: %s' % FLAGS.language)

  # Get the path to the template set.
  language_variants = Targets().TargetsForLanguage(FLAGS.language)
  variant_features = language_variants[FLAGS.language_variant]
  template_dir = os.path.join(
      os.path.dirname(__file__), FLAGS.language, variant_features['path'])
  generator.SetTemplateDir(template_dir)
  generator.SetSurfaceFeatures(variant_features)

  # Get an output writer
  if FLAGS.output_dir:
    package_writer = FilesystemLibraryPackage(FLAGS.output_dir)
  else:
    out = open(FLAGS.output_file, 'w')
    package_writer = ZipLibraryPackage(out)

  if options.get('emit_manifest'):
    package_writer.IncludeMinimalJarManifest(
        created_by='1.0.0-googleapis-v1 (Google Inc.)')
  # do it
  generator.GeneratePackage(package_writer)
  package_writer.DoneWritingArchive()
  if FLAGS.output_file:
    out.close()
  return 0

if __name__ == '__main__':
  app.run()
