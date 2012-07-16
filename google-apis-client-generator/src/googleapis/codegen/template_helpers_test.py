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

"""Tests for template_helpers."""

__author__ = 'aiuto@google.com (Tony Aiuto)'



import os

from google.apputils import basetest
from googleapis.codegen import template_helpers
from django import template as django_template

django_template.add_to_builtins(
    'googleapis.codegen.template_helpers')


class TemplateHelpersTest(basetest.TestCase):

  _TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), 'testdata')

  def testExtractCommentPrefix(self):
    self.assertEquals('   *',
                      template_helpers._ExtractCommentPrefix('   * hello'))
    self.assertEquals('   *',
                      template_helpers._ExtractCommentPrefix('   *hello'))
    self.assertEquals('//',
                      template_helpers._ExtractCommentPrefix('// hello'))
    self.assertEquals('#',
                      template_helpers._ExtractCommentPrefix('# hello'))
    self.assertEquals('  #',
                      template_helpers._ExtractCommentPrefix('  # hello'))

  def testDivideIntoBlocks(self):
    test = """
      // block 1
      //
      // block 2a
      // block 2a

      // block 3
      // """
    blocks = []
    for block in template_helpers._DivideIntoBlocks(test.split('\n'),
                                                    '      //'):
      blocks.append(block)
    self.assertEquals(3, len(blocks))
    self.assertEquals(1, len(blocks[0]))
    self.assertEquals(2, len(blocks[1]))
    self.assertEquals(1, len(blocks[2]))

  def testCommentFragment(self):
    value = '123456789 ' * 15
    indent = 6
    # What we expect is that 9 of the sequences above will fit on the first
    # line, then we wrap. It's only 89 because the trailing space is trimmed.
    expected = value[:89] + '\n' + (' ' * indent) + ' * ' + value[90:-1]
    self.assertEquals(expected,
                      template_helpers.java_comment_fragment(value, indent))

  def testCommentBlockJavaDoc(self):
    alphabet = 'abcdefghijklmnopqrstuvwxyz'
    value = """
       * %s %s
       * %s %s %s
       * """ % (alphabet, alphabet, alphabet, alphabet, alphabet)
    expected = """
       * %s %s %s
       * %s %s""" % (alphabet, alphabet, alphabet, alphabet, alphabet)
    self.assertEquals(expected, template_helpers.block_comment(value))
    value = """
       // %s %s
       // %s %s %s
       // """ % (alphabet, alphabet, alphabet, alphabet, alphabet)
    expected = """
       // %s %s %s
       // %s %s""" % (alphabet, alphabet, alphabet, alphabet, alphabet)
    self.assertEquals(expected, template_helpers.block_comment(value))

  def testNoblanklines(self):
    self.assertEquals('a\nb', template_helpers.noblanklines('a\nb'))
    self.assertEquals('a\nb', template_helpers.noblanklines('a\nb\n\n'))
    self.assertEquals('a\nb', template_helpers.noblanklines('\na\n\nb\n'))

  def testDocComments(self):
    def TryDocComment(language, input_text, expected):
      context = {}
      lang_node = template_helpers.LanguageNode(language)
      lang_node.render(context)
      context['_LINE_WIDTH'] = 50  # to make expected easier to read
      doc_comment_node = template_helpers.DocCommentNode(
          text=input_text, comment_type='doc')
      self.assertEquals(expected, doc_comment_node.render(context))

    alphabet = 'abcdefghijklmnopqrstuvwxyz'

    # single line java and php
    value = '%s' % alphabet
    expected = '/** %s */' % alphabet
    TryDocComment('java', value, expected)
    TryDocComment('php', value, expected)

    # multi line java and php
    value = '%s %s %s' % (alphabet, alphabet, alphabet)
    expected = '/**\n * %s\n * %s\n * %s\n */' % (alphabet, alphabet, alphabet)
    TryDocComment('java', value, expected)
    TryDocComment('php', value, expected)

    # single line csharp
    value = '%s' % alphabet
    expected = '/// <summary>%s</summary>' % alphabet
    TryDocComment('csharp', value, expected)

    # multi line csharp
    value = '%s %s %s' % (alphabet, alphabet, alphabet)
    expected = '/// <summary>%s\n/// %s\n/// %s</summary>' % (
        alphabet, alphabet, alphabet)
    TryDocComment('csharp', value, expected)

  def testCallTemplate(self):
    source = 'abc {% call_template _call_test foo bar %} def'
    template = django_template.Template(source)
    rendered = template.render({
        'template_dir': self._TEST_DATA_DIR,
        'api': {
            'xxx': 'yyy'
            },
        'bar': 'baz'
        })
    self.assertEquals('abc 1baz1 2yyy2 def', rendered)

  def testParamList(self):
    source = """method({% parameter_list %}
          {% parameter %}int a{% end_parameter%}
          {% parameter %}
            {% if false %}
               The condition fails, so the entire parameter is empty.
            {% endif %}
          {% end_parameter %}
          {% parameter %}string b{% end_parameter %}
        {% end_parameter_list %})"""
    template = django_template.Template(source)
    rendered = template.render({})
    self.assertEquals('method(int a, string b)', rendered)

  def testImportWithoutManager(self):
    expected = """import hello_world
                  import abc"""
    source = '{% imports x %}\n' + expected + '\n{% endimports %}'
    template = django_template.Template(source)
    rendered = template.render({'x': {}})
    self.assertEquals(expected, rendered)


if __name__ == '__main__':
  basetest.main()
