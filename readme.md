# Mashery I/O Wraps Client Library Generator
###Native language client library (SDK) builder for platforms using I/O Docs

## What is I/O Wraps?
Mashery clients using I/O Docs have defined their APIs using the I/O Docs schema. I/O Wraps is a bundle of open-source tools that provides a path of taking that configuration schema and building native-language client libraries. The primary component in the bundle is the [Google APIs Client Library Generator](http://code.google.com/p/google-apis-client-generator/), an open-source tool created by Google that can take an API described in the [Google Discovery Document Format](https://developers.google.com/discovery/v1/reference#resource_discovery) and generate client libraries.

First, Mashery I/O Docs configurations are converted into the Google Discovery Resource format using a conversion tool (included). Second, the Google generator is run against the newly converted configuration. And third, the corresponding Google native language client uses the generated library. PHP and Java are currently supported.

## How do client libraries help developers?
Client libraries make life easier by bringing the API into your native language environment. So, rather than making curl calls, piping the output into a variable, and parsing through the variable -- the client library handles the network connectivity, authorization and API call execution with syntax you're familiar with:

    // Initialize the client library
    $client = new apiClient();

    // Set your API key
    $client->setDeveloperKey("YOUR_KEY_HERE");

    // Connect client to the API
    $api = new apiService($client);

    // Make an API call and store the response in an object
    $StoryList = new StoryList($api->ArticleMethods->TopNews(
        "json",
        "sports"
    ));

    // Iterate through the list of stories, and echo the titles
    foreach ($StoryList->getStories() as $story) {
       echo("Title: " . $story->getTitle());
    }

Above is just a pseudo-PHP-code example of how this library works.

## Requirements
1. Python (2.6+)
2. [Google App Utils](http://code.google.com/p/google-apputils-python/downloads/detail?name=google-apputils-0.3.0.tar.gz&can=2&q=)
3. Django templates (1.1 or newer) - either through django or Google AppEngine SDKs
4. httplib2 - http://code.google.com/p/httplib2/
5. python-gflags - http://code.google.com/p/python-gflags/
6. setuptools - http://pypi.python.org/pypi/setuptools/


## Installation / Quick Start
The steps below are for Linux, Mac OS X or other UNIX-variant operating systems.

1. Deploy this distro to /usr/src/

2. Unpack Google App utils to /usr/src/ - check README and build/install. 

3. Install Django templates, httplib2, python-gflags and setuptools.

4. Point your browser to: /usr/src/io-wraps/iodocs_json_converter.html
     a. Paste in an I/O Docs configuration from the Mashery Dashboard configuration
     b. Click Convert to Google Discovery Format button
     c. Save output in Google Discovery Format textarea to: /usr/src/io-wraps/new_api.json

5. From shell: export PYTHONPATH=/usr/src/io-wraps/google-apis-client-generator/src:/usr/src/google-apputils-0.3.0/build/lib:/usr/lib/python2.6:$PYTHONPATH (assuming Python 2.6 is your current version)

6. From shell: cd /usr/src/io-wraps/google-apis-client-generator/src/googleapis/codegen

7. From shell: ./generate_library.py --language=php --language_variant=stable --output_dir=/usr/src/io-wraps/new_api_php --input=/usr/src/io-wraps/new_api.json

## PHP - Next Steps
If you have followed the instructions above and generated a PHP library, you will find it in:    
/usr/src/io-wraps/new_api_php.

The next steps:

1. Deploy the [Google API PHP Client fork from the Mashery Github repo](https://github.com/mashery/google-api-php-client) into /usr/src/io-wraps

2. Move the newly generated PHP file from /usr/src/io-wraps/new_api_php directory into:    
/usr/src/io-wraps/google-api-php-client/contrib 

3. Edit the file /usr/src/io-wraps/google-api-php-client/config.php - in particular, set the 'key_name' and 'basePath' 

At this point, you're ready to start linking the client libraries into your code. To see built/bundled I/O Wraps SDKs with example apps, check out these repos:

 [https://github.com/mashery/io-wraps-rovi-php](https://github.com/mashery/io-wraps-rovi-php)    
 [https://github.com/mashery/io-wraps-usatoday-php](https://github.com/mashery/io-wraps-usatoday-php)    
 [https://github.com/mashery/io-wraps-whitli-php](https://github.com/mashery/io-wraps-whitli-php)

## Java - Next Steps
If you have generated a Java library, you simply need to build the Maven project. For example, if you set the --output_dir to /usr/src/io-wraps/new_api_java, follow these simple steps:

1. From shell: cd /usr/src/io-wraps/new_api_java

2. From shell: maven install

You do need to have Java and Maven installed. At this point, you're ready to start linking the client libraries into your code.

## Caveats - YMMV (Your Mileage May Vary)
Building client libraries with a generator such as this may not produce the perfect SDK out of the box. In fact, there are plenty of improvements, optimizations and features that this project could use. The entire process is open-source from end to end, meaning that from the schema, to the generator, generator templates, and of course, the generated SDK, you are free to make any style and design modifications.

If your JSON configuration schema came directly from an I/O Docs implementation and you have very long resource and method names, that translates to very long function names in your code.

For payload responses to be fully objectified, you must describe the response object in the Google Resource format. Otherwise, the response data will need to be traversed as a regular object/hash/array. See the [Google Discovery Document Resource reference](https://developers.google.com/discovery/v1/reference#resource_discovery), and in particular the "schemas" and "response" properties. 

## To Do (TODO)
* Autoload and namespaces for PHP - one of high-priority followups for the google-api-php-client fork
* Mashery I/O Docs Node.js (on Github) JSON schema support - the current Javascript converter only supports the Mashery I/O Docs production/enterprise schema


## About / License
* No warranty expressed or implied. Software as is.
* [MIT License](http://www.opensource.org/licenses/mit-license.html)
* Lovingly created by [Mashery Dev](http://dev.mashery.com)