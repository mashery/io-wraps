#!/usr/bin/python
# Copyright 2011 Google Inc. All Rights Reserved.

"""Command-line application to push skeleton templates to BlobStore.

Allows easy updating of skeleton templates to BlobStore. Pass in the name of the
file and it will be uploaded. You just need to supply the hostname of the server
to receive the downloads, the app knows the right URIs to upload to. Uploads are
limited to the size that the App Engine Blobstore API, currently 32MB.

The output of the application is a JSON object with the filename of the file
that was uploaded.
"""

__author__ = 'jcgregorio@google.com (Joe Gregorio)'

import mimetypes
import urllib2

from google.apputils import app
import gflags as flags
from google.apputils import http_over_rpc
from google.apputils import logging

FLAGS = flags.FLAGS


flags.DEFINE_string(
    'hostname',
    'localhost:8080',
    'Hostname and port of instance to upload to files to.')


def main(argv):
  url = 'http://' + FLAGS.hostname + '/blob_upload/start'
  upload_url = http_over_rpc.urlopen(url, timeout=10, http_retry=True).read()

  logging.debug('URL to POST uploads to: %s', upload_url)

  req = urllib2.Request(upload_url)
  files = []
  for filename in argv[1:]:
    logging.info('File: %s', filename)
    f = file(filename, 'r')
    contents = f.read()
    f.close()
    files.append((filename, contents))
  content_type, post_data = EncodeMultipartFormdata(files)
  logging.debug('Content-type header: %s', content_type)
  logging.info('POST message size: %d', len(post_data))
  req.add_header('Content-Type', content_type)
  req.add_header('Content-Length', str(len(post_data)))
  data = http_over_rpc.urlopen(req, post_data, timeout=60,
                               http_retry=True).read()
  print data


def GetContentType(filename):
  """Get the mime content type for a file."""
  return mimetypes.guess_type(filename)[0] or 'application/octet-stream'


def EncodeMultipartFormdata(files):
  """Encodes the input data into something which can be sent.

  Args:
    files:  A sequence of (filename, value) elements for data to be
            uploaded as files
  Returns:
    (content_type, body) ready for httplib.HTTP instance
  """
  boundary = '----------ThIs_Is_tHe_bouNdaRY_$'
  newline = '\r\n'
  a = []
  for (filename, value) in files:
    a.append('--' + boundary)
    a.append('Content-Disposition: form-data; name="file"; filename="%s"' %
             filename)
    a.append('Content-Type: application/octet-stream')
    a.append('')
    a.append(value)
  a.append('--' + boundary + '--')
  a.append('')
  body = newline.join(a)
  content_type = 'multipart/form-data; boundary=%s' % boundary
  return content_type, body


if __name__ == '__main__':
  app.run()
