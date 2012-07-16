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

"""Custom template tags and filters for Google APIs code generator.

These are Django template filters for reformatting blocks of code.
"""

__author__ = 'aiuto@google.com (Tony Aiuto)'


import os
import re
import string
import textwrap

import django.template as django_template
from django.template.loader import render_to_string


register = django_template.Library()

# NOTE: Do not edit this text unless you understand the ramifications.
_COPYRIGHT_TEXT = """
Copyright (c) 2010 Google Inc.

Licensed under the Apache License, Version 2.0 (the "License"); you may
not use this file except in compliance with the License. You may obtain
a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
License for the specific language governing permissions and limitations
under the License.
"""

# Names of the parameters used for formatting generated code.  These are keys
# to the actual values, which are stored in the generation context.
_LANGUAGE = '_LANGUAGE'
_LINE_BREAK_INDENT = '_LINE_BREAK_INDENT'
_LINE_WIDTH = '_LINE_WIDTH'
_PARAMETER_INDENT = '_PARAMETER_INDENT'
_LEVEL_INDENT = '_LEVEL_INDENT'
_COMMENT_START = '_COMMENT_START'
_COMMENT_CONTINUE = '_COMMENT_CONTINUE'
_COMMENT_END = '_COMMENT_END'
_DOC_COMMENT_START = '_DOC_COMMENT_START'
_DOC_COMMENT_CONTINUE = '_DOC_COMMENT_CONTINUE'
_DOC_COMMENT_END = '_DOC_COMMENT_END'
# The begin/end tags are parts of a doc comment that surround the text, but
# are not really part of the comment tags
_DOC_COMMENT_BEGIN_TAG = '_DOC_COMMENT_BEGIN_TAG'
_DOC_COMMENT_END_TAG = '_DOC_COMMENT_END_TAG'

_CURRENT_INDENT = '_CURRENT_INDENT'  # The actual indent we are at
_CURRENT_LEVEL = '_CURRENT_LEVEL'  # The current indent level we are at
_PARAMETER_DOC_INDENT = '_PARAMETER_DOC_INDENT'
_IMPORT_REGEX = '_IMPORT_REGEX'
_IMPORT_TEMPLATE = '_IMPORT_TEMPLATE'

_defaults = {
    _LINE_BREAK_INDENT: 2,
    _LINE_WIDTH: 40,
    _PARAMETER_INDENT: 4,
    _LEVEL_INDENT: 2,
    _COMMENT_START: '# ',
    _COMMENT_CONTINUE: '# ',
    _COMMENT_END: '',
    _DOC_COMMENT_START: '# ',
    _PARAMETER_DOC_INDENT: 6,
    _DOC_COMMENT_CONTINUE: '# ',
    _DOC_COMMENT_END: '',
    _DOC_COMMENT_BEGIN_TAG: '',
    _DOC_COMMENT_END_TAG: '',
    _IMPORT_REGEX: r'^\s*import\s+(?P<import>[a-zA-Z0-9.]+)',
    _IMPORT_TEMPLATE: 'import %s',
    }

_language_defaults = {
    'csharp': {
        _LINE_WIDTH: 120,
        _PARAMETER_INDENT: 4,
        _LEVEL_INDENT: 4,
        _COMMENT_START: '// ',
        _COMMENT_CONTINUE: '// ',
        _COMMENT_END: '',
        _DOC_COMMENT_START: '/// ',
        _DOC_COMMENT_CONTINUE: '/// ',
        _DOC_COMMENT_BEGIN_TAG: '<summary>',
        _DOC_COMMENT_END_TAG: '</summary>',
        },
    'go': {
        _LINE_WIDTH: 120,
        _PARAMETER_INDENT: 4,
        _LEVEL_INDENT: 8,
        _COMMENT_START: '// ',
        _COMMENT_CONTINUE: '// ',
        _COMMENT_END: '',
        _DOC_COMMENT_START: '// ',
        _DOC_COMMENT_CONTINUE: '// '
        },
    'java': {
        _LINE_WIDTH: 100,
        _COMMENT_START: '/* ',
        _COMMENT_CONTINUE: ' * ',
        _COMMENT_END: ' */',
        _DOC_COMMENT_START: '/** ',
        _PARAMETER_DOC_INDENT: 6,
        _IMPORT_REGEX: r'^\s*import\s+(?P<import>[a-zA-Z0-9.]+);',
        _IMPORT_TEMPLATE: 'import %s;',
        },
    'objc': {
        _LINE_WIDTH: 80,
        _COMMENT_START: '/* ',
        _COMMENT_CONTINUE: ' * ',
        _COMMENT_END: ' */',
        _DOC_COMMENT_START: '// ',
        _DOC_COMMENT_CONTINUE: '// ',
        },
    'php': {
        _LINE_WIDTH: 80,
        _COMMENT_START: '/* ',
        _COMMENT_CONTINUE: ' * ',
        _COMMENT_END: ' */',
        _DOC_COMMENT_START: '/** ',
        },
    }


def _GetFromContext(context, *variable):
  """Safely get something from the context.

  Look for a variable (or an alternate variable) in the context. If it is not
  in the context, look in _defaults.

  Args:
    context: (Context) The Django render context
    *variable: (str) varargs list of variable names

  Returns:
    The requested value from the context or the defaults.
  """
  for v in variable:
    ret = context.get(v)
    if ret:
      return ret
  for v in variable:
    ret = _defaults.get(v)
    if ret:
      return ret
  return ''


#
# Basic Filters
#


def _DivideIntoBlocks(lines, prefix):
  """Dole out the input text in blocks separated by blank lines.

  A "blank line" in this case means a line that is actually zero length or
  just is the comment prefix. The common prefix, along with any spaces trailing
  the prefix are removed from each line.

  Args:
    lines: list of str
    prefix: a commmon prefix to remove from each line
  Yields:
    list of (list of str)
  """
  block = []
  prefix = prefix.rstrip()
  for line in lines:
    if line.startswith(prefix):
      line = line[len(prefix):].strip()
    if not line:
      if block:
        yield block
      block = []
      continue
    block.append(line)
  if block:
    yield block


def _ExtractCommentPrefix(line):
  """Examine a line of text and extract what would be a comment prefix.

  The pattern we are looking for is ' *[^ ::punctuation::]*'.  This covers most
  programming languages in common use.  Fortran and Basic are obviously not
  supported. :-)

  Args:
    line: (str) a sample line
  Returns:
    (str) The comment prefix
  """
  # look for spaces followed by a comment tag and break after that.
  got_tag = False
  prefix_length = 0
  # collect the prefix pattern
  for c in line:
    if c == ' ':
      if got_tag:
        break
      prefix_length += 1
    elif c in string.punctuation:
      got_tag = True
      prefix_length += 1
    else:
      break
  return line[:prefix_length]


# We disable the bad function name warning because we use Django style names
# rather than Google style names
@register.filter
def java_comment_fragment(value, indent):  # pylint: disable-msg=C6409
  """Template filter to wrap lines into Java comment style.

  Take a single long string and break it so that subsequent lines are prefixed
  by an approprate number of spaces and then a ' * '.  The filter invocation
  should begin on a line that is already indented suffciently.

  This is typically used after we have written the lead-in for a comment. E.g.

  |    // NOTE: The leading / is indented 4 spaces.
  |    /**
  |     * {{ variable|java_comment_fragment:4 }}
  |     */

  Args:
    value: (str) the string to wrap
    indent: (int) the number of spaces to indent the block.
  Returns:
    The rewrapped string.
  """
  if not indent:
    indent = 0
  prefix = '%s * ' % (' ' * indent)
  wrapper = textwrap.TextWrapper(width=_language_defaults['java'][_LINE_WIDTH],
                                 replace_whitespace=False,
                                 initial_indent=prefix,
                                 subsequent_indent=prefix)
  wrapped = wrapper.fill(value)
  if wrapped.startswith(prefix):
    wrapped = wrapped[len(prefix):]
  return wrapped


@register.filter
def java_parameter_wrap(value):  # pylint: disable-msg=C6409
  """Templatefilter to wrap lines of parameter documentation.

  Take a single long string and breaks it up so that subsequent lines are
  prefixed by an appropriate number of spaces (and preceded by a ' * '.

  Args:
   value: (str) the string to wrap

  Returns:
  the rewrapped string.
  """
  # TODO(user): add 'parameter_doc' option to the DocCommentBlock
  indent = _language_defaults['java'][_PARAMETER_DOC_INDENT]
  prefix = ' * %s ' % (' ' * indent)
  wrapper = textwrap.TextWrapper(width=_language_defaults['java'][_LINE_WIDTH],
                                 replace_whitespace=False,
                                 initial_indent='',
                                 subsequent_indent=prefix)
  wrapped = wrapper.fill(value)
  return wrapped


# We disable the bad function name warning because we use Django style names
# rather than Google style names (disable-msg=C6409)
@register.filter
def block_comment(value):  # pylint: disable-msg=C6409
  """Template filter to line wrap a typical block comment.

  Take a block of text where each line has a common comment prefix, divide it
  into multiple sections, line wrap each section and string them back together.
  Sections are defined as blank lines or lines containing only the comment
  prefix.

  Example template usage:
    /**{% filter block_comment %}
     * wwelrj wlejrwerl jrl (very long line ...) rwrwr.
     *
     * more text
     * and more
     * {% endfilter %}
     */

  Args:
    value: (str) a block of text to line wrap.
  Returns:
    (str) the wrapped text.
  """
  if not value:
    return ''
  lines = value.split('\n')
  # Ignore a leading blank line while figuring out the comment tag. This allows
  # us to put the filter tag above the content, rather than flush left before
  # it. It makes the template easier to read.
  leading_blank = False
  if not lines[0]:
    leading_blank = True
    comment_prefix = _ExtractCommentPrefix(lines[1])
  else:
    comment_prefix = _ExtractCommentPrefix(lines[0])
  wrapper = textwrap.TextWrapper(width=_language_defaults['java'][_LINE_WIDTH],
                                 replace_whitespace=False,
                                 initial_indent=('%s ' % comment_prefix),
                                 subsequent_indent=('%s ' % comment_prefix))
  wrapped_blocks = []
  for block in _DivideIntoBlocks(lines, comment_prefix):
    wrapped_blocks.append(wrapper.fill(' '.join(block)))
  ret = ''
  if leading_blank:
    ret = '\n'
  return ret + ('\n%s\n' % comment_prefix).join(wrapped_blocks)


@register.filter
def noblanklines(value):  # pylint: disable-msg=C6409
  """Template filter to remove blank lines."""
  return '\n'.join([line for line in value.split('\n') if line.strip()])


@register.filter
def collapse_blanklines(value):  # pylint: disable-msg=C6409
  """Template filter to collapse successive blank lines into a single one."""
  lines = []
  previous_blank = False
  for line in value.split('\n'):
    if not line.strip():
      if not previous_blank:
        lines.append(line)
        previous_blank = True
      else:
        pass
    else:
      lines.append(line)
      previous_blank = False
  return '\n'.join(lines)

#
# Tags for programming language concepts
#


class LanguageNode(django_template.Node):
  """Node for language settting."""

  def __init__(self, language):
    self._language = language

  def render(self, context):  # pylint: disable-msg=C6409
    """Render the 'language' tag.

    For the language setting we render nothing, but we take advantage of being
    passed the context to set language specific things there, so they are
    usable later.

    Args:
      context: (Context) the render context.
    Returns:
      An empty string.
    """
    # This is a hack to support django 0.96 and 1.2.  In 1.something and above
    # we want to turn off autoescape. For 0.96, setting context.autoescape
    # fails. This allows it to work in both situations.
    try:
      context.autoescape = False
    except AttributeError:
      pass
    # end - hack for django 0.96 support
    context[_LANGUAGE] = self._language
    per_language_defaults = _language_defaults.get(self._language)
    if per_language_defaults:
      context.update(per_language_defaults)
    context[_CURRENT_INDENT] = 0
    context[_CURRENT_LEVEL] = 0
    return ''


@register.tag(name='language')
def DoLanguage(unused_parser, token):
  """Specify the language we are emitting code in.

  Usage:
    {% language java %}

  Args:
    unused parser: (parser) the Django parser context.
    token: (django.template.Token) the token holding this tag

  Returns:
    a LanguageNode
  """
  try:
    unused_tag_name, language = token.split_contents()
  except ValueError:
    raise django_template.TemplateSyntaxError(
        'language tag requires a single argument: %s' % token.contents)
  return LanguageNode(language)


class IndentNode(django_template.Node):
  """A node which indents its contents based on indent nesting levels.

  The interior text is re-indented by the existing indent + the indent nesting
      level * the LEVEL_INDENT
  """

  def __init__(self, nodelist, levels):
    self._nodelist = nodelist
    self._levels = int(levels)

  def render(self, context):  # pylint: disable-msg=C6409
    """Reindent the block inside the tag scope."""
    current_indent = context.get(_CURRENT_INDENT, 0)
    current_indent_level = context.get(_CURRENT_LEVEL, 0)
    # How much extra indent will this level add
    extra = (_GetFromContext(context, _LEVEL_INDENT) * self._levels)
    # Set the new effective indent of this block.  Tags which wrap text to
    # the line limit must use this value to determine their actual indentation.
    context[_CURRENT_INDENT] = current_indent + extra
    context[_CURRENT_LEVEL] = current_indent_level + self._levels
    lines = self._nodelist.render(context)
    context[_CURRENT_INDENT] = current_indent
    context[_CURRENT_LEVEL] = current_indent_level
    # We only have to prefix the lines in this row by the extra indent, because
    # the outer scope will be adding its own indent as well.
    prefix = ' ' * extra

    def _PrefixNonBlank(s):
      x = s.rstrip()
      if x:
        x = '%s%s' % (prefix, x)
      return x
    return '\n'.join([_PrefixNonBlank(line) for line in lines.split('\n')])


@register.tag(name='indent')
def DoIndent(parser, token):
  """Increase the indent level for indenting.

  Usage:
    {% indent [levels] %} text... {% endindent %}
    Increase the indent on all lines of text by levels * LEVEL_INDENT

  Args:
    parser: (parser) the Django parser context.
    token: (django.template.Token) the token holding this tag

  Returns:
    a IndentNode
  """
  try:
    unused_tag_name, levels = token.split_contents()
  except ValueError:
    # No level, default to 1
    levels = 1
  nodelist = parser.parse(('endindent',))
  parser.delete_first_token()
  return IndentNode(nodelist, levels)


class DocCommentNode(django_template.Node):
  """Node for comments which should be formatted as doc-style comments."""

  def __init__(self, text=None, comment_type=None):
    self._text = text
    self._comment_type = comment_type

  def render(self, context):  # pylint: disable-msg=C6409
    """Render the node."""
    return self.RenderText(self._text, context)

  def RenderText(self, text, context):  # pylint: disable-msg=C6409
    """Format text according to the context.

    The strategy is to divide the text into blocks (on blank lines), then
    to format the blocks individually, then reassemble.

    Args:
      text: (str) The text to format.
      context: (django_template.Context) The rendering context.

    Returns:
      The rendered comment.
    """
    if self._comment_type == 'doc':
      start_prefix = _GetFromContext(context, _DOC_COMMENT_START,
                                     _COMMENT_START)
      continue_prefix = _GetFromContext(context, _DOC_COMMENT_CONTINUE,
                                        _COMMENT_CONTINUE)
      comment_end = _GetFromContext(context, _DOC_COMMENT_END, _COMMENT_END)
      begin_tag = _GetFromContext(context, _DOC_COMMENT_BEGIN_TAG)
      end_tag = _GetFromContext(context, _DOC_COMMENT_END_TAG)
    else:
      start_prefix = _GetFromContext(context, _COMMENT_START)
      continue_prefix = _GetFromContext(context, _COMMENT_CONTINUE)
      comment_end = _GetFromContext(context, _COMMENT_END)
      begin_tag = ''
      end_tag = ''

    available_width = (_GetFromContext(context, _LINE_WIDTH) -
                       context.get(_CURRENT_INDENT, 0))
    one_line = '%s%s%s%s%s' % (start_prefix, begin_tag, text, end_tag,
                               comment_end)
    if len(one_line) < available_width:
      return one_line

    wrapper = textwrap.TextWrapper(width=available_width,
                                   replace_whitespace=False,
                                   initial_indent=continue_prefix,
                                   subsequent_indent=continue_prefix)
    wrapped_blocks = []
    text = '%s%s%s' % (begin_tag, text, end_tag)
    for block in _DivideIntoBlocks(text.split('\n'), ''):
      wrapped_blocks.append(wrapper.fill(' '.join(block)))
    ret = ''
    if start_prefix != continue_prefix:
      ret = '%s\n' % start_prefix.rstrip()
    stripped_prefix = continue_prefix.rstrip()
    ret += ('\n%s\n' % stripped_prefix).join(wrapped_blocks)
    if comment_end:
      ret += '\n%s' % comment_end
    return ret


class CommentIfNode(DocCommentNode):
  """Node for comments which should only appear if they have text.

  A CommentIf is a pair of a comment style and a variable name.  If the variable
  has a value, then a comment will be emmited for it, otherwise nothing is
  emitted.
  """

  def __init__(self, variable_name, comment_type=None):
    super(CommentIfNode, self).__init__(comment_type=comment_type)
    self._variable_name = variable_name

  def render(self, context):  # pylint: disable-msg=C6409
    """Render the node."""
    try:
      text = django_template.resolve_variable(self._variable_name, context)
      if text:
        return self.RenderText(text, context)
    except django_template.VariableDoesNotExist:
      pass
    return ''


@register.tag(name='comment_if')
def DoCommentIf(unused_parser, token):
  """If a variable has content, emit it as a comment."""
  try:
    unused_tag_name, variable_name = token.split_contents()
  except ValueError:
    raise django_template.TemplateSyntaxError(
        'tag requires a single argument: %s' % token.contents)
  return CommentIfNode(variable_name)


@register.tag(name='doc_comment_if')
def DoDocCommentIf(unused_parser, token):
  """If a variable has content, emit it as a document compatible comment."""
  try:
    unused_tag_name, variable_name = token.split_contents()
  except ValueError:
    raise django_template.TemplateSyntaxError(
        'tag requires a single argument: %s' % token.contents)
  return CommentIfNode(variable_name, comment_type='doc')


class ImportsNode(django_template.Node):
  """Node for outputting language specific imports."""

  def __init__(self, nodelist, element):
    self._nodelist = nodelist
    self._element = element

  def render(self, context):  #pylint: disable-msg=C6409
    """Render the node."""

    explicit_import_text = self._nodelist.render(context)

    # Look for an importManager on the element.  If we find one:
    # - scan the import text for import statements
    # - add each to the manager
    # - get the complete import set
    import_lists = None
    try:
      import_manager = django_template.resolve_variable(
          '%s.importManager' % self._element, context)
      import_regex = _GetFromContext(context, _IMPORT_REGEX)
      for line in explicit_import_text.split('\n'):
        match_obj = re.match(import_regex, line)
        if match_obj:
          import_manager.AddImport(match_obj.group('import'))
      import_lists = import_manager.ImportLists()
    except django_template.VariableDoesNotExist:
      pass

    import_template = _GetFromContext(context, _IMPORT_TEMPLATE)
    if import_lists:
      ret_lists = []
      for import_list in import_lists:
        ret_lists.append(
            '\n'.join([import_template % x for x in import_list]))
      # Each import should be on its own line and each group of imports should
      # be separated by a new line.
      return '\n\n'.join([ret_list for ret_list in ret_lists if ret_list])
    else:
      # We could not find the import lists from an import manager, revert to
      # the original text
      return explicit_import_text.strip()


@register.tag(name='imports')
def Imports(parser, token):
  """If an element has importLists emit them, else emit existing imports."""
  try:
    unused_tag_name, element = token.split_contents()
  except ValueError:
    raise django_template.TemplateSyntaxError(
        'tag requires a single argument: %s' % token.contents)
  nodelist = parser.parse(('endimports',))
  parser.delete_first_token()
  return ImportsNode(nodelist, element)


class ParameterListNode(django_template.Node):
  """Node for parameter_list blocks."""

  def __init__(self, nodelist, separator):
    super(ParameterListNode, self).__init__()
    self._nodelist = nodelist
    self._separator = separator

  def render(self, context):  # pylint: disable-msg=C6409
    """Render the node."""
    blocks = []
    # Split apart on paramater boundaries, getting rid of white space between
    # parameters
    for block in self._nodelist.render(context).split(ParameterNode.BEGIN):
      block = block.rstrip().replace(ParameterNode.END, '')
      if block:
        blocks.append(block)
    return self._separator.join(blocks)


class ParameterNode(django_template.Node):
  """Node for parameter tags."""

  # Makers so the parameter_list can find me.
  BEGIN = chr(1)
  END = chr(2)

  def __init__(self, nodelist):
    super(ParameterNode, self).__init__()
    self._nodelist = nodelist

  def render(self, context):  # pylint: disable-msg=C6409
    """Render the node."""
    # Attach markers so the enclosing parameter_list can find me
    return self.BEGIN + self._nodelist.render(context).strip() + self.END


@register.tag(name='parameter_list')
def DoParameterList(parser, token):
  """Gather a list of parameter declarations and join them with ','.

  Gathers all 'parameter' nodes until the 'end_parameter_list' tag and joins
  them together with a ', ' separator. Extra white space between nodes is
  removed, but other text is left intact, joined to the end of the preceeding
  parameter node. Blank parameters are omitted from the list.

  Usage:
    foo({% parameter_list separator %}{% for p in method.parameters %}
        {{ p.type }} {{ p.name }}
        {% endfor %}
        {% end_parameter_list %})

  Args:
    parser: (parser) the Django parser context.
    token: (django.template.Token) the token holding this tag

  Returns:
    a ParameterListNode
  """
  try:
    unused_tag_name, separator = token.split_contents()
  except ValueError:
    # No separator, set default.
    separator = ', '
  nodelist = parser.parse(('end_parameter_list',))
  parser.delete_first_token()
  return ParameterListNode(nodelist, separator)


@register.tag(name='parameter')
def DoParameter(parser, unused_token):
  """A single parameter in a parameter_list.

  See DoParameterList for a description.

  Args:
    parser: (parser) the Django parser context.
    unused_token: (django.template.Token) the token holding this tag

  Returns:
    a ParameterNode
  """
  nodelist = parser.parse(('end_parameter',))
  parser.delete_first_token()
  return ParameterNode(nodelist)


#
# Tags which include language specific templates
#


class TemplateNode(django_template.Node):
  """Django template Node holding data for writing a per language template.

  The TemplateNode is a variation of an include template that allows for
  per language lookup.  The node
  * Looks up the template name w.r.t. the template_dir variable of the current
    context.  The calling application must make sure template_dir is valid.
  * evaluates a variable in the current context and binds that value to a
    specific variable in the context
  * renders the template
  * restores the context.

  See individual tag definitions for usage.
  """

  def __init__(self, template_name, bound_variable, caller_variable):
    """Construct the TemplateNode.

    Args:
      template_name: (str) the name of the template file. This will be resolved
          relative to the 'template_dir' element of the context.
      bound_variable: (str) the name of a variable to set in the context when
          we invoke the template.
      caller_variable: (str) the variable the caller passes to the tag. When the
          node is rendered, bound_variable will be set to the value of
          caller_variable.
    """
    self._template_name = template_name
    self._bound_variable = bound_variable
    self._caller_variable = caller_variable

  def render(self, context):  # pylint: disable-msg=C6409
    """Render the node."""
    template_path = os.path.join(context['template_dir'], self._template_name)
    try:
      old_value = django_template.resolve_variable(self._bound_variable,
                                                   context)
    except django_template.VariableDoesNotExist:
      old_value = None
    var = django_template.resolve_variable(self._caller_variable, context)
    context[self._bound_variable] = var
    s = render_to_string(template_path, context).rstrip()
    if old_value:
      context[self._bound_variable] = old_value
    return s

  @staticmethod
  def CreateTemplateNode(token, template, bound_variable):
    """Helper function to create a TemplateNode by parsing a tag.

    Args:
      token: (django.template.Token) the token holding this tag
      template: (str) The template name
      bound_variable: (str) the name of a variable to set in the context when
          we invoke the template.

    Returns:
      a TemplateNode
    """
    try:
      unused_tag_name, variable_name = token.split_contents()
    except ValueError:
      raise django_template.TemplateSyntaxError(
          'tag requires a single argument: %s' % token.contents)
    return TemplateNode(template, bound_variable, variable_name)


@register.tag(name='call_template')
def CallTemplate(unused_parser, token):
  """Interpret a template with an additional set of variable bindings.

  Evalutes the template named 'template_name.tmpl' with the variable
  'bound_value_name' bound to value of the variable 'value_name'.

  Usage:
    {% call_template template_name bound_variable_name value_name %}

  Args:
    unused_parser: (parser) the Django parser context.
    token: (django.template.Token) the token holding this tag

  Returns:
    a TemplateNode
  """
  try:
    unused_tag, template, bound_var, value_var = token.split_contents()
  except ValueError:
    raise django_template.TemplateSyntaxError(
        'tag requires 3 arguments: %s' % token.contents)
  return TemplateNode('%s.tmpl' % template, bound_var, value_var)


@register.tag(name='emit_enum_def')
def DoEmitEnumDef(unused_parser, token):
  """Emit an enum definition through a language specific template.

  Evalutes the template named '_enum.tmpl' with the variable 'enum' bound
  to the specified value.

  Usage:
    {% emit_enum_def var %}

  Args:
    unused_parser: (parser) the Django parser context.
    token: (django.template.Token) the token holding this tag

  Returns:
    a TemplateNode
  """
  return TemplateNode.CreateTemplateNode(token, '_enum.tmpl', 'enum')


@register.tag(name='emit_method_def')
def DoEmitMethodDef(unused_parser, token):
  """Emit a method definition through a language specific template.

  Evalutes the template named '_method.tmpl' with the variable 'method' bound
  to the specified value.

  Usage:
    {% emit_method_def var %}

  Args:
    unused_parser: (parser) the Django parser context.
    token: (django.template.Token) the token holding this tag

  Returns:
    a TemplateNode
  """
  return TemplateNode.CreateTemplateNode(token, '_method.tmpl', 'method')


@register.tag(name='emit_model_def')
def DoEmitModelDef(unused_parser, token):
  """Emit a data model definition through a language specific template.

  Evaluates a template named '_model.tmpl' with the variable 'model'
  bound to the specified value.

  Usage:
    {% emit_model_def model %}

  Args:
    unused_parser: (parser) the Django parser context
    token: (django.template.Token) the token holding this tag

  Returns:
    a TemplateNode
  """
  return TemplateNode.CreateTemplateNode(token, '_model.tmpl', 'model')


@register.tag(name='emit_parameter_doc')
def DoEmitParameterDoc(unused_parser, token):
  """Emit a parameter definition through a language specific template.

  Evaluates a template named '_parameter.tmpl' with the variable 'parameter'
  bound to the specified value.

  Usage:
    {% emit_parameter_doc parameter %}

  Args:
    unused_parser: (parser) the Django parser context
    token: (django.template.Token) the token holding this tag

  Returns:
    a TemplateNode
  """
  return TemplateNode.CreateTemplateNode(token, '_parameter.tmpl', 'parameter')


@register.tag(name='emit_resource_def')
def DoEmitResourceDef(unused_parser, token):
  """Emit a resource definition through a language specific template.

  Evalutes the template named '_resource.tmpl' with the variable 'resource'
  bound to the specified value.

  Usage:
    {% emit_resource_def var %}

  Args:
    unused_parser: (parser) the Django parser context.
    token: (django.template.Token) the token holding this tag

  Returns:
    a TemplateNode
  """
  return TemplateNode.CreateTemplateNode(token, '_resource.tmpl', 'resource')


@register.tag(name='copyright_block')
def DoCopyrightBlock(unused_parser, unused_token):
  """Emit a copyright block through a language specific template.

  Evalutes the template named '_resource.tmpl' with the variable 'resource'
  bound to the specified value.

  Usage:
    {% copyright_block %}

  Args:
    unused_parser: (parser) the Django parser context.
    unused_token: (django.template.Token) the token holding this tag

  Returns:
    a DocCommentNode
  """
  return DocCommentNode(_COPYRIGHT_TEXT)
