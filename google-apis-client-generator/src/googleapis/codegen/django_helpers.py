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

"""Wrapper methods to insulate us from Django nuances.

Provide Django setup and some utility methods.
"""

__author__ = 'aiuto@google.com (Tony Aiuto)'


import os
from django.conf import settings
settings.configure(
  TEMPLATE_DIRS=('/', os.path.join(os.path.dirname(__file__))))
from django.template.loader import render_to_string

from django import template as django_template

# This is Django magic to add builtin tags and filters.  They don't really
# support that use case.  Instead you are supposed to put a package of filters
# in a specific place and the Django web server finds them for you. We are a
# standalone app, not running in their context, so we have to go under the hood
# a little.
django_template.add_to_builtins(
    'googleapis.codegen.template_helpers')


def DjangoRenderTemplate(template_path, context_dict):
  return render_to_string(template_path, context_dict)
