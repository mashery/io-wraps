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

"""Tests for zip_library_package."""

__author__ = 'aiuto@google.com (Tony Aiuto)'

import cStringIO
import os
import zipfile

import gflags as flags
from google.apputils import basetest
from googleapis.codegen import zip_library_package

FLAGS = flags.FLAGS


class ZipLibraryPackageTest(basetest.TestCase):
  _FILE_NAME = 'a_test'
  _FILE_CONTENTS = 'this is a test'
  _TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), 'testdata')

  def setUp(self):
    self._output_stream = cStringIO.StringIO()
    self._package = zip_library_package.ZipLibraryPackage(self._output_stream)

  def tearDown(self):
    pass

  def testBasicWriteFile(self):
    stream = self._package.StartFile(self._FILE_NAME)
    stream.write(self._FILE_CONTENTS)
    self._package.EndFile()
    self._package.DoneWritingArchive()

    # read it back and verify
    archive = zipfile.ZipFile(
        cStringIO.StringIO(self._output_stream.getvalue()), 'r')
    info_list = archive.infolist()
    self.assertEquals(1, len(info_list))
    self.assertEquals(self._FILE_NAME, info_list[0].filename)
    self.assertEquals(len(self._FILE_CONTENTS), info_list[0].file_size)

  def testStartAutomaticallyClosesPreviousFile(self):
    stream = self._package.StartFile(self._FILE_NAME)
    stream.write(self._FILE_CONTENTS)
    file_name_2 = '%s_2' % self._FILE_NAME
    stream = self._package.StartFile(file_name_2)
    stream.write(self._FILE_CONTENTS)
    self._package.EndFile()
    self._package.DoneWritingArchive()
    # read it back and verify
    archive = zipfile.ZipFile(
        cStringIO.StringIO(self._output_stream.getvalue()), 'r')
    info_list = archive.infolist()
    self.assertEquals(2, len(info_list))
    self.assertEquals(self._FILE_NAME, info_list[0].filename)
    self.assertEquals(file_name_2, info_list[1].filename)

  def testDoneAutomaticallyEndsFile(self):
    stream = self._package.StartFile(self._FILE_NAME)
    stream.write(self._FILE_CONTENTS)
    self._package.DoneWritingArchive()

    # read it back and verify
    archive = zipfile.ZipFile(
        cStringIO.StringIO(self._output_stream.getvalue()), 'r')
    info_list = archive.infolist()
    self.assertEquals(1, len(info_list))
    self.assertEquals(self._FILE_NAME, info_list[0].filename)

  def testIncludeFile(self):
    made_up_path = 'new_directory/file1.txt'
    # testdata/file1.txt is 125 bytes long.
    expected_size = 125
    self._package.IncludeFile(os.path.join(self._TEST_DATA_DIR, 'file1.txt'),
                              made_up_path)
    self._package.DoneWritingArchive()

    # read it back and verify
    archive = zipfile.ZipFile(
        cStringIO.StringIO(self._output_stream.getvalue()), 'r')
    info_list = archive.infolist()
    self.assertEquals(1, len(info_list))
    self.assertEquals(made_up_path, info_list[0].filename)
    self.assertEquals(expected_size, info_list[0].file_size)

  def testManyFiles(self):
    top_of_tree = os.path.join(self._TEST_DATA_DIR, 'tree/')
    total_files_in_testdata_tree = 3  # determined by hand
    paths = []
    for root, unused_dirs, file_names in os.walk(top_of_tree):
      for file_name in file_names:
        paths.append(os.path.join(root, file_name))
    self._package.IncludeManyFiles(paths, top_of_tree)
    self._package.DoneWritingArchive()

    # check it
    archive = zipfile.ZipFile(
        cStringIO.StringIO(self._output_stream.getvalue()), 'r')
    info_list = archive.infolist()
    self.assertEquals(total_files_in_testdata_tree, len(info_list))

  def testManyFilesError(self):
    files = [os.path.join(self._TEST_DATA_DIR, file_name)
             for file_name in ['tree/abc', 'tree/def', 'file1.txt']]
    self.assertRaises(ValueError,
                      self._package.IncludeManyFiles,
                      files,
                      os.path.join(self._TEST_DATA_DIR, 'tree/'))

  def testOutputPrefix(self):
    prefix = 'abc/def'
    self._package.SetFilePathPrefix(prefix)
    stream = self._package.StartFile(self._FILE_NAME)
    stream.write(self._FILE_CONTENTS)
    self._package.EndFile()
    self._package.DoneWritingArchive()

    # read it back and verify
    archive = zipfile.ZipFile(
        cStringIO.StringIO(self._output_stream.getvalue()), 'r')
    info_list = archive.infolist()
    self.assertEquals(1, len(info_list))
    expected_name = '%s/%s' % (prefix, self._FILE_NAME)
    self.assertEquals(expected_name, info_list[0].filename)


if __name__ == '__main__':
  basetest.main()
