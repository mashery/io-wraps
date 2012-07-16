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

"""Base library generator.

This module holds the base classes used for all code generators
"""

__author__ = 'aiuto@google.com (Tony Aiuto)'

import datetime
import os
import re
import time
import urlparse



from googleapis.codegen.django_helpers import DjangoRenderTemplate
from googleapis.codegen.language_model import LanguageModel
from googleapis.codegen.template_objects import UseableInTemplates
from googleapis.codegen.zip_library_package import ZipLibraryPackage

# This block is static information about the generator which will get passed
# into templates.
_GENERATOR_INFORMATION = {
    'name': 'google-apis-code-generator',
    'version': '1.1.1',
    'buildDate': '2011-10-20',
    }
_DEFAULT_SERVICE_HOST = 'https://www.googleapis.com'

# app.yaml and other names that app engine refuses to open.
# TODO(user) Remove once templates are stored in BlobStore.
_SPECIAL_FILENAMES = ['app_yaml']


class TemplateGenerator(object):
  """Base class for walking a template tree to generate output files.

  This class provides methods for processing template trees to produce output
  trees.
  * Provides a common base dictionary of varirables for use in templates.
  * Callers can augment that with their own dictionary of variables.
  * Callers can provide a set of replacements to be made to file paths in
    the template tree
  """

  def __init__(self, language_model=None, options=dict()):
    self._tool_info = ToolInformation()
    self._options = options
    self._template_dir = None
    self._surface_features = {}
    self._language_model = language_model or LanguageModel()

  @property
  def language_model(self):
    return self._language_model

  def IncludeFileTree(self, path_to_tree, package):
    """Walk a file tree and copy files directly into an output package.

    Walks a file tree relative to the the target language, copying all files
    found into an output package.

    Args:
      path_to_tree: (str) path relative to the language template directory
      package: (LibraryPackage) output package.
    """
    top_of_tree = os.path.join(self._template_dir, path_to_tree)
    # Walk tree for jar files to directly include
    for root, unused_dirs, file_names in os.walk(top_of_tree):
      for file_name in file_names:
        path = os.path.join(root, file_name)
        relative_path = path[len(top_of_tree)+1:]
        package.IncludeFile(path, relative_path)

  def PathToTemplate(self, template_name):
    """Returns the full path to a template."""
    return os.path.join(self._template_dir, template_name)

  def RenderTemplate(self, template_path, context_dict=dict()):
    """Render a template.

    Renders a template with the standard dictionary of bindings.

    Args:
      template_path: (str) Full path to a template.
      context_dict: (dict) A dictionary to augment the standard template
        dictionary.
    Returns:
      (str) The fully rendered template string.
    """
    variables_dict = {
        'tool': self._tool_info,  # Information about the build tool
        'options': self._options,  # Options for this invocation
        'template_dir': self._template_dir,  # path to the template tree
        'surfaceFeatures': self._surface_features,  # sub language options
        }
    variables_dict.update(context_dict)
    return DjangoRenderTemplate(template_path, variables_dict)

  def WalkTemplateTree(self, path_to_tree, path_replacements, list_replacements,
                       variables, package):
    """Walk a file tree and copy files or process templates.

    Walks a file tree to write on output package, running all files ending in
    ".tmpl" through the template renderer, and directly copying all the other
    files.  While doing so, allow some transformations on the file path. E.g.
      '___package___' is replaced by the API package path
      '___api_className___' is replaced by API class name.

    Args:
      path_to_tree: (str) path relative to the language template directory.
      path_replacements: (dict) dict holding elements which should be replaced
        if found in a path.
      list_replacements: (dict) dict holding elements which should be replaced
        by many files when found in a path. The keys of the dict are strings
        to be found in a path. The values are a tuple of
           ([list of code objects], name_to_bind)
      variables: (dict) The dictionary of variable replacements to pass to the
         templates.
      package: (LibraryPackage) output package.
    """
    top_of_tree = os.path.join(self._template_dir, path_to_tree)
    # Walk tree for jar files to directly include
    variables.update({'template_dir': top_of_tree})
    for root, unused_dirs, file_names in os.walk(top_of_tree):
      for file_name in file_names:
        path = os.path.join(root, file_name)
        relative_path = root[len(top_of_tree)+1:]
        if not relative_path:
          relative_path = '.'

        # Perform the replacements on the path and file name
        for path_item, replacement in path_replacements.iteritems():
          relative_path = relative_path.replace(path_item, replacement)
        for path_item, replacement in path_replacements.iteritems():
          file_name = file_name.replace(path_item, replacement)
        for path_item, call_info in list_replacements.iteritems():
          if file_name.find(path_item) >= 0:
            self.GenerateListOfFiles(path_item, call_info, path, relative_path,
                                     file_name, variables, package)
            continue

        if file_name.startswith('_'):
          continue
        if file_name.endswith('.tmpl'):
          name_in_zip = file_name[:-5]  # strip '.tmpl'
          if name_in_zip in _SPECIAL_FILENAMES:
            name_in_zip = name_in_zip.replace('_', '.')
          out = package.StartFile('%s/%s' % (relative_path, name_in_zip))
          out.write(self.RenderTemplate(path, variables))
          package.EndFile()
        else:
          package.IncludeFile(path, '%s/%s' % (relative_path, file_name))

  def GeneratePackage(self, package_writer):
    """Generate the package.

    Subclasses must implement this.

    Args:
      package_writer: (LibraryPackage) output package
    """
    raise NotImplementedError(
        'GeneratePackage must be implmented by all subclasses')

  def DefaultGeneratePackage(self, package_writer, path_replacements,
                             variables):
    """Default operations to generate the package.

    Do all the default operations for generating a package.
    1. Walk the template tree to generate the source.
    2. Optionally copy in dependencies

    This is a utility method intended for subclasses of TemplateGenerator, so
    that they may implement the bulk of GeneratePackage by calling this.

    Args:
      package_writer: (LibraryPackage) output package.
      path_replacements: (dict) dict holding elements which should be replaced
         if found in a path.
      variables: (dict) The dictionary of variable replacements to pass to the
         templates.
    """
    self.WalkTemplateTree('templates', path_replacements, {}, variables,
                          package_writer)
    if self._options.get('include_dependencies'):
      self.IncludeFileTree('dependencies', package_writer)

  def SetSurfaceFeatures(self, surface_features):
    self._surface_features = surface_features

  def SetTemplateDir(self, template_dir):
    self._template_dir = template_dir

  def GenerateListOfFiles(self, path_prefix, call_info, template_path,
                          relative_path, template_file_name, variables,
                          package):
    """Generate many output files from a template.

    This method blends togther a list of CodeObjects (from call_info) with
    the template_file_name to produce an output file for each of the elements
    in the list. The names for each file are derived from a template variable
    of each element.

    Args:
      path_prefix: (str) The piece of path which triggers the replacement.
      call_info: (list) ['name to bind', [list of CodeObjects]]
      template_path: (str) The path of the template file.
      relative_path: (str) The relative path of the output file in the package.
      template_file_name: (str) the file name of the template for this list.
        The file name must contain the form '{path_prefix}{variable_name}'
        (without the braces). The pair is replaced by the value of variable_name
        from each successive element of the call list.
      variables: (dict) The dictionary of variable replacements to pass to the
         templates.
      package: (LibraryWriter) The output package stream to write to.

    Raises:
      ValueError: If the template_file_name does not match the call_info data.
    """
    path_and_var_regex = r'%s([a-z][A-Za-z]*)___' % path_prefix
    match_obj = re.compile(path_and_var_regex).match(template_file_name)
    if not match_obj:
      raise ValueError(
          'file names which match path item for GenerateListOfFiles must'
          ' contain a variable for substitution. E.g. "___models_codeName___"')
    variable_name = match_obj.group(1)
    file_name_piece_to_replace = path_prefix + variable_name + '___'
    for element in call_info[1]:
      file_name = template_file_name.replace(
          file_name_piece_to_replace, element.values[variable_name])
      name_in_zip = file_name[:-5]  # strip '.tmpl'
      out = package.StartFile('%s/%s' % (relative_path, name_in_zip))
      d = dict(variables)
      d[call_info[0]] = element
      out.write(self.RenderTemplate(template_path, d))
      package.EndFile()


class ToolInformation(UseableInTemplates):
  """Defines information about this generator tool itself."""

  def __init__(self):
    super(ToolInformation, self).__init__(_GENERATOR_INFORMATION)
    now = datetime.datetime.utcnow()
    self.SetTemplateValue('runDate',
                          '%4d-%02d-%02d' % (now.year, now.month, now.day))
    self.SetTemplateValue(
        'runTime',
        '%02d:%02d:%02d UTC' % (now.hour, now.minute, now.second))


class ApiLibraryGenerator(TemplateGenerator):
  """TemplateGenerator specialization which produces an API library."""

  def __init__(self, api_loader, discovery, language, language_model=None,
               options=dict()):
    """Construct an ApiLibraryGenerator.

    Args:
      api_loader: (Api) Method which can construct an Api from discovery.
      discovery: (dict) A discovery definition.
      language: (str) The target language name. This has no semantic meaning
          other than to specify the template set to use.
      language_model: (LanguageModel) The target language data model.
      options: (dict) Code generator options.
    """
    super(ApiLibraryGenerator, self).__init__(language_model=language_model,
                                              options=options)
    # Load the API definition and an prepare it for generating code.
    self._api = api_loader(discovery)
    self._language = language

    # top level package for the generated code. The 'path' of the package is
    # used to expand '___package___' instances in file names found in the
    # template tree.
    self._package = None
    # package for generated models, defaults to top level package
    self._model_package = None

  @property
  def package(self):
    return self._package

  @property
  def model_package(self):
    return self._model_package or self._package

  def SetPackage(self, package):
    """Sets the package this code tree should be generated into.


    Args:
      package: (template_objects.Package) The package this code belongs in.
    """
    self._package = package

  def GeneratePackage(self, package_writer):
    """Generate the entire package of an API library.

    Overrides superclass.

    Args:
      package_writer: (LibraryPackage) output package
    """
    api = self._api
    self.AnnotateApiForLanguage(api)
    if self._options.get('use_library_name_in_path'):
      package_writer.SetFilePathPrefix(
          '%s-%s' % (api.values['libraryNameBase'], self._language))
    source_package_writer = package_writer
    if self._options.get('include_source_jar'):
      source_out = package_writer.StartFile(
          '%s-%s-src.jar' % (api.values['libraryNameBase'], self._language))
      source_package_writer = ZipLibraryPackage(source_out)
      source_package_writer.IncludeMinimalJarManifest(
          created_by='1.0.0-googleapis-v1 (Google Inc.)')
    self.GenerateLibrarySource(api, source_package_writer)
    if package_writer != source_package_writer:
      source_package_writer.DoneWritingArchive()
    if self._options.get('include_dependencies'):
      self.IncludeFileTree('dependencies', package_writer)

  def GenerateLibrarySource(self, api, source_package_writer):
    """Default operations to generate the package.

    Do all the default operations for generating a package.
    1. Walk the template tree to generate the source.
    2. Add in per-langauge additions to the source
    3. Optionally copy in dependencies
    4. (Side effect) Closes the source_package_writer.

    Args:
      api: (Api) The Api instance we are writing a libary for.
      source_package_writer: (LibraryPackage) source output package.
    """
    if self._package:
      package_path = self._package.path
    else:
      package_path = '.'
    path_replacements = {
        '___package___': package_path,
        '___api_className___': api.values['className'],
        }
    list_replacements = {
        '___models_': ['model', api.ModelClasses()],
        '___topLevelModels_': ['model', api.TopLevelModelClasses()],
        }
    self.WalkTemplateTree('templates', path_replacements, list_replacements,
                          {'api': api.values}, source_package_writer)
    # Call back to the language specific generator to give it a chance to emit
    # special case elements.
    self.GenerateExtraSourceOutput(source_package_writer)

  def GenerateExtraSourceOutput(self, source_package_writer):
    """Extension point for subclasses to add extra data to the output.

    A language generator may provide an implementation of this to emit elements
    which cannot be handled by GenerateLibraryPackage.

    Args:
      source_package_writer: (LibraryPackage) An output package writer.
    """
    pass

  def _SetPathAndHost(self, api):
    """Calculate and set the basePath and serviceHost.

    Args:
      api: (Api) The api definition to modify
    """
    # TODO(user): Create a unit test for this.
    base_path = api.values.get('basePath') or api.values.get('restBasePath')
    if not base_path:
      # Do not set template value if paths not specified.
      return

    # Eg: If base_path = 'https://batman.appspot.com/joker/laughs'
    # urlparse.urlparse(base_path) returns
    # (scheme='https', netloc='batman.appspot.com', path='/joker/laughs',
    #  params='', query='', fragment='')
    parse_result = urlparse.urlparse(base_path)
    if parse_result.scheme:
      # Eg: If base_path = 'https://superman.appspot.com/krypton/hurts'
      # urlparse.urljoin(base_path, '/') returns
      # 'https://superman.appspot.com/'
      service_host = urlparse.urljoin(base_path, '/')[:-1]
      base_path = parse_result.path
    else:
      # TODO(user): Make this configurable by passing a discovery_server
      # input into the generator.
      service_host = _DEFAULT_SERVICE_HOST

    api.SetTemplateValue('basePath', base_path)
    api.SetTemplateValue('serviceHost', service_host)

  def AnnotateApiForLanguage(self, the_api):
    """Add the language specific annotations to an api.

    Does all the language specific additions to an API so it is ready to use
    for generation a library surface. This is essentially an impedence match
    between what is expressed in the API definition and how a language specific
    binding can be expressed using only templates.

    Args:
      the_api: (Api) The API to annotate.
    """
    the_api.VisitAll(lambda o: o.SetLanguageModel(self.language_model))
    the_api.void_type.SetLanguageModel(self.language_model)
    the_api.SetTemplateValue(
        'libraryNameBase',
        'google-api-%s-%s' % (the_api.values['name'],
                              the_api.values['version']))
    self._SetPathAndHost(the_api)
    self._AnnotateTree(the_api)

  def _AnnotateTree(self, api):
    """Decorate the API tree with languge model specific elements.

    Walks the tree and calls annotators on the Methods and Properties.  This
    may be used to supply language specfic transforms to an API between the
    time the API is loaded and before we generate code through the templates.

    should be called after the API is constructed and before we generate
    any code.

    Args:
      api: (Api) The Api.
    """
    self.AnnotateApi(api)
    for schema in api.all_schemas.values():
      schema.SetTemplateValue('package', self.model_package)
      self.AnnotateSchema(api, schema)
      for prop in schema.values.get('properties', []):
        self.AnnotateProperty(api, prop, schema)
    for resource in api.values['resources']:
      self.AnnotateResource(api, resource)
    for method in api.values['methods']:
      self.AnnotateMethod(api, method, None)

  def AnnotateApi(self, api):
    """Extension point for subclasses to annotate the API node itself.

    A language generator may provide an implementation for this.

    Args:
      api: (Api) The Api.
    """
    pass

  def AnnotateMethod(self, unused_api, method, unused_resource):
    """Extension point for subclasses to annotate Resources.

    A language generator may provide an implementation for this.

    Args:
      unused_api: (Api) The Api.
      method: (Method) The Method to annotate.
      unused_resource: (Resource) The Resource which owns this Method.
    """
    for parameter in method.parameters:
      self.AnnotateParameter(method, parameter)

  def AnnotateParameter(self, method, parameter):
    """Extension point for subclasses to annotate method Parameters.

    A language generator may provide an implementation for this.

    Args:
      method: (Method) The Method this parameter belongs to.
      parameter: (Parameter) The Paramater to annotate.
    """
    pass

  def AnnotateProperty(self, api, prop, schema=None):
    """Extension point for subclasses to annotate Properties.

    A language generator may provide an implementation for this.

    Args:
      api: (Api) The Api.
      prop: (Property) The Property to annotate.
      schema: (Schema) The Schema this Property belongs to.
    """
    pass

  def AnnotateResource(self, api, resource):
    """Extension point for subclasses to annotate Resources.

    A language generator may provide an implementation for this. The default
    walks the Resources methods and sub-resources to annotate those.

    Args:
      api: (Api) The Api which owns this resource.
      resource: (Resource) The Resource to annotate.
    """
    for method in resource.values['methods']:
      self.AnnotateMethod(api, method, resource)
    for r in resource.values['resources']:
      self.AnnotateResource(api, r)

  def AnnotateSchema(self, api, schema):
    """Extension point for subclasses to annotate Schemas.

    A language generator may provide an implementation for this.

    Args:
      api: (Api) The Api.
      schema: (Schema) The Schema to annotate
    """
    pass


class NullLibraryGenerator(ApiLibraryGenerator):
  """Used to flag a language that doesn't do library generation."""
  pass
