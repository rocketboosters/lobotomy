# Lobotomy

[![PyPI version](https://badge.fury.io/py/lobotomy.svg)](https://pypi.org/project/lobotomy/)
[![build status](https://gitlab.com/rocket-boosters/lobotomy/badges/main/pipeline.svg)](https://gitlab.com/rocket-boosters/lobotomy/commits/main)
[![coverage report](https://gitlab.com/rocket-boosters/lobotomy/badges/main/coverage.svg)](https://gitlab.com/rocket-boosters/lobotomy/commits/main)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Code style: flake8](https://img.shields.io/badge/code%20style-flake8-white)](https://gitlab.com/pycqa/flake8)
[![Code style: mypy](https://img.shields.io/badge/code%20style-mypy-white)](http://mypy-lang.org/)
[![PyPI - License](https://img.shields.io/pypi/l/lobotomy)](https://pypi.org/project/lobotomy/)

- [Installation](#installation)
- [Tl;dr Usage](#tldr-usage)
- [Usage](#usage)
    - [Configuration Files](#configuration-files)
    - [Test Patching](#test-patching)
    - [YAML IO Modifiers](#yaml-io-modifiers)
      - [!lobotomy.to_json](#to_json)
      - [!lobotomy.inject_string](#inject_string)
    - [Command Line Interface](#command-line-interface)
- [Advanced Usage](#advanced-usage)
    - [Key Prefixes](#key-prefixes)
    - [Patching Targets](#patching-targets)
    - [Session Configuration](#session-configuration)
    - [Client Overrides](#client-overrides)
    - [Error Handling](#error-handling)
    - [Callable Responses](#callable-responses)

The *lo&#8226;**boto**&#8226;my* library allows one to mock the low-level boto3
client libraries efficiently, especially in more complex scenario testing 
situations, using configuration-based response definitions. The benefit is a
separation of the configuration from the test execution, which cleans up the
test invocation process.

## Installation

lobotomy is available on pypi and installable via pip:

```shell script
$ pip install lobotomy
```

or via poetry as a development dependency in a project:

```shell script
$ poetry add lobotomy -D
```

## Tl;dr Usage

Create a configuration file in YAML, TOML, or JSON format with a root *clients*
key. Beneath that key add the desired client calls mocked responses by service
as shown here for a `session.client('s3').get_object()` mocked response:

```yaml
clients:
  s3:
    get_object:
      Body: 'The contents of my S3 file.'
      LastModified: '2020-12-01T01:02:03Z'
```

Then in the test notice that the lobotomy patching process handles the
rest, including casting the configuration values specified in the call
above into the more complex data types returned for the specific call.

```python
import lobotomy
import pathlib
import boto3
import datetime

my_directory = pathlib.Path(__file__).parent

@lobotomy.patch(my_directory.joinpath("test_lobotomy.yaml"))
def test_lobotomy(lobotomized: lobotomy.Lobotomy):
    """
    Should return the mocked get_object response generated from the
    configuration data specified in the lobotomy patch above. By default
    the patch(...) applies to the boto3.Session object, so calling 
    boto3.Session() will create a lobotomy.Session instead of a normal
    boto3.Session. From there the low-level client interface is designed
    to match normal usage.
    """
    s3_client = boto3.Session().client("s3")
    
    # Lobotomy will validate that you have specified the required keys
    # in your request, so Bucket and Key have to be supplied here even though
    # they are not meaningful values in this particular test scenario.
    response = s3_client.get_object(Bucket="foo", Key="bar")

    expected = b"The contents of my S3 file."
    assert response["Body"].read() == expected, """
        Expected the mocked response body data to be returned as a
        StreamingBody object with blob/bytes contents. The lobotomy
        library introspects boto to properly convert the string body
        value in the configuration file into the expected return format
        for the particular call.
        """
    
    expected = datetime.datetime(2020, 12, 1, 1, 2, 3, 0, datetime.timezone.utc)
    assert response["LastModified"] == expected, """
        Expected the mocked response last modified value to be a timezone-aware
        datetime value generated from the string timestamp value in the
        configuration file to match how it would be returned by boto in
        an actual response.
        """

    call = lobotomized.get_service_call("s3", "get_object")
    assert call.request["Bucket"] == "foo", """
        Expected the s3.get_object method call arguments to have specified the bucket
        as "foo".
        """
    assert call.request["Key"] == "bar", """
        Expected the s3.get_object method call argumets to have specified the key as
        "bar".
        """
```

# Usage

## Configuration Files

Test scenarios can be written in YAML, TOML, or JSON formats. YAML or TOML are
recommended unless copying output responses from JSON calls is easier for a
given use-case. In the following example, we'll define the calls using YAML:

```yaml
clients:
  sts:
    get_caller_identity:
      Account: '987654321'
  s3:
    get_object:
      Body: 'The contents of my S3 file.'
      LastModified: '2020-11-01T12:23:34Z'
```

All call responses are stored within the root *clients* attribute with service
names as sub-attributes and then the service method call responses defined 
beneath the service name attributes. Multiple services and multiple methods
per service are specified in this way by the hierarchical key lists.

If the contents of a method response definition are not a list, the same
response will be returned for each call to that client method during the
test. Specifying a list of responses will alter the behavior such that each
successive call will iterate through that list of configured responses.

```yaml
clients:
  s3:
    get_object:
    - Body: 'The contents of my S3 file.'
      LastModified: '2020-11-01T12:23:34Z'
    - Body: 'Another S3 file.'
      LastModified: '2020-11-03T12:23:34Z'
```

The lobotomy library dynamically inspects boto for its response structure
and data types, such that they match the types for the normal boto response
for each client method call. In the case of the
`session.client('s3').get_object()` calls above, the `Body` would return
a `StreamingBody` object with the string converted to bytes to match the
normal output. Similarly, the `LastModified` would be converted to a
timezone-aware datetime object by lobotomy as well. This makes it easy
to specify primitive data types in the configuration file that are transformed
into their more complex counterparts when returned within the execution of
the actual code.

## Test Patching

Once the configuration file has been specified, it is used within a test
via a `lobotomy.patch` as shown below.

```python
import lobotomy
import pathlib
import boto3
import datetime

my_directory = pathlib.Path(__file__).parent

@lobotomy.patch(my_directory.joinpath("test_lobotomy.yaml"))
def test_lobotomy(lobotomized: lobotomy.Lobotomy):
    """
    Should return the mocked get_object response generated from the
    configuration data specified in the lobotomy patch above. By default
    the patch(...) applies to the boto3.Session object, so calling 
    boto3.Session() will create a lobotomy.Session instead of a normal
    boto3.Session. From there the low-level client interface is designed
    to match normal usage.
    """
    s3_client = boto3.Session().client("s3")
    
    # Lobotomy will validate that you have specified the required keys
    # in your request, so Bucket and Key have to be supplied here even though
    # they are not meaningful values in this particular test scenario.
    response = s3_client.get_object(Bucket="foo", Key="bar")

    expected = b"The contents of my S3 file."
    assert response['Body'].read() == expected, """
        Expect the mocked response body data to be returned as a
        StreamingBody object with blob/bytes contents. The lobotomy
        library introspects boto to properly convert the string body
        value in the configuration file into the expected return format
        for the particular call.
        """
    
    expected = datetime.datetime(2020, 12, 1, 1, 2, 3, 0, datetime.timezone.utc)
    assert response['LastModified'] == expected, """
        Expect the mocked response last modified value to be a timezeon-aware
        datetime value generated from the string timestamp value in the
        configuration file to match how it would be returned by boto in
        an actual response.
        """
```

The patching process replaces the `boto3.Session` class with a
`lobotomy.Lobotomy` object that contains the loaded configuration data.
When patched in this fashion, `boto3.Session()` calls will actually be
`lobotomy.Lobotomy()` calls that return `lobotomy.Session` objects. These
sessions have the interface of the `boto3.Session` object, but behave in
a way such that client responses are returned from the configuration data
instead of through interactivity with AWS.

For simple cases with little configuration, it is also possible to patch
data stored directly within the Python code. The above test could be rewritten
in this way as:

```python
import lobotomy

configuration = {
    "clients": {
        "s3": {
            "get_object": [
                { 
                    "Body": "The contents of my S3 file.",
                    "LastModified": "2020-11-01T12:23:34Z",
                },
                {
                    "Body": "Another S3 file.",
                    "LastModified": "2020-11-03T12:23:34Z",
                },
            ],
        },
    },
}


@lobotomy.patch(data=configuration)
def test_lobotomy(lobotomized: lobotomy.Lobotomy):
    """..."""
```

Although one of the benefits of lobotomy is the ability to streamline the
tests files by reducing the response configuration, which can be a bit
verbose inside Python files and that is the highly recommended approach.

A third option for simpler cases is to use the `Lobotomy.add_call()` method
to register calls and responses.

```python
import lobotomy


@lobotomy.patch()
def test_lobotomy(lobotomized: lobotomy.Lobotomy):
    """..."""
    lobotomized.add_call(
        service_name="s3", 
        method_name="get_object", 
        response={ 
            "Body": "The contents of my S3 file.",
            "LastModified": "2020-11-01T12:23:34Z",
        },
    )
    lobotomized.add_call(
        service_name="s3", 
        method_name="get_object", 
        response={
            "Body": "Another S3 file.",
            "LastModified": "2020-11-03T12:23:34Z",
        },
    )
```

In the case above no data or path was supplied to the `lobotomy.patch()` and instead
call responses were registered within the test function itself. The response argument
in the `Lobotomy.add_call()` method is optional. If omitted, a default one will be
created instead in the same fashion as one would be created via the CLI (see below).

Note that it is also possible to mix loading data and adding calls within the test
function.

## YAML IO Modifiers

When using YAML files, lobotomy comes with custom YAML classes that can provide
even more flexibility and ease in defining data. The following are the available
modifiers and how to use them:

### to_json

This modifier will convert YAML data into a JSON string in the creation of the
response, which makes it easier to represent complex JSON data in the scenario
data.

```yaml
clients:
  secretsmanager:
    get_secret_value:
      SecretString: !lobotomy.to_json
        first: first_value
        second: second_value
```

In this example the `!lobotomy.to_json` YAML modifier instructs the lobotomy to
converts the object data beneath the `SecretString` attribute into a JSON string
as part of the response object. In this case then in the associated Python test:

```python
import boto3
import lobotomy
import json


@lobotomy.patch(path="scenario.yaml")
def test_showing_to_json(lobotomized: lobotomy.Lobotomy):
    """Should expect a JSON string for the 'SecretString' value."""
    client = boto3.Session().client("secretsmanager")

    response = client.get_secret_value(SecretId="fake")
    
    expected = {"first": "first_value", "second": "second_value"}
    assert expected == json.loads(response["SecretValue"])
```

the value is returned as the expected JSON string.

### inject_string

This modifier is used to inject the string contents of another file into the value
of the associated attribute.

```yaml
clients:
  s3:
    get_object:
      Body: !lobotomy.inject_string './body.txt'
```

Here the `!lobotomy.inject_string` YAML modifier instructs lobotomy to load the
contents of the external file `./body.txt` into the `Body` attribute value where
the external file path is defined relative to the defining YAML file.

So in this case, if there's a `body.txt` file with the contents `Hello lobotomy!`,
the Python test would find this in reading the body:

```python
import boto3
import lobotomy
import json


@lobotomy.patch(path="scenario.yaml")
def test_showing_inject_string(lobotomized: lobotomy.Lobotomy):
    """Should expect the body.txt to be injected into the Body response attribute."""
    client = boto3.Session().client("s3")
    response = client.get_object(Bucket="fake", Key="fake")
    assert response["Body"].read() == b"Hello lobotomy!"
```

## Command Line Interface

The lobotomy library also has a command line interface to help streamline
the process of creating configuration files. The CLI has an `add` command
that can be used to auto-generate method call response configurations to
a new or existing configuration file. The values are meant to be replaced
and unused keys to be removed to streamline for testing, but it helps a lot
to get the full structure of the response in place and work from there instead
of having to look it up yourself.

For example, creating the file:

```yaml
clients:
  sts:
    get_caller_identity:
      Account: '987654321'
  s3:
    get_object:
    - Body: 'The contents of my S3 file.'
      LastModified: '2020-11-01T12:23:34Z'
    - Body: 'Another S3 file.'
      LastModified: '2020-11-03T12:23:34Z'
```

could be done first through the CLI commands:

```shell script
$ lobotomy add sts.get_caller_identity example.yaml
``` 

After that command is executed, the `example.yaml` file will be
created and populated initially with:

```yaml
clients:
  sts:
    get_caller_identity:
      Account: '...'
      Arn: '...'
      UserId: '...'
```

Notice the values are placeholders. We can adjust the values to what we want
and remove the unnecessary keys for our particular case such that the file
contents are then:

```yaml
clients:
  sts:
    get_caller_identity:
      Account: '987654321'
```

Next add the first `s3.get_object` call:

```shell script
$ lobotomy add s3.get_object example.yaml
```

The configuration file now looks like:

```yaml
clients:
  s3:
    get_object:
      AcceptRanges: '...'
      Body: '...'
      CacheControl: '...'
      ContentDisposition: '...'
      ContentEncoding: '...'
      ContentLanguage: '...'
      ContentLength: 1
      ContentRange: '...'
      ContentType: '...'
      DeleteMarker: null
      ETag: '...'
      Expiration: '...'
      Expires: '2020-11-04T14:37:18.042821Z'
      LastModified: '2020-11-04T14:37:18.042821Z'
      Metadata: null
      MissingMeta: 1
      ObjectLockLegalHoldStatus: '...'
      ObjectLockMode: '...'
      ObjectLockRetainUntilDate: '2020-11-04T14:37:18.042821Z'
      PartsCount: 1
      ReplicationStatus: '...'
      RequestCharged: '...'
      Restore: '...'
      SSECustomerAlgorithm: '...'
      SSECustomerKeyMD5: '...'
      SSEKMSKeyId: '...'
      ServerSideEncryption: '...'
      StorageClass: '...'
      TagCount: 1
      VersionId: '...'
      WebsiteRedirectLocation: '...'
  sts:
    get_caller_identity:
      Account: '987654321'
```

Of course, this is a simple case because we don't need much of the response
structure in our simplified use-case, but hopefully you can see the value
of being able to add the response structure so easily for more complex cases.
Once again, the new call is adjusted to fit our particular needs:

```yaml
clients:
  s3:
    get_object:
      Body: 'The contents of my S3 file.'
      LastModified: '2020-11-01T12:23:34Z'
  sts:
    get_caller_identity:
      Account: '987654321'
```

Adding the second `s3.get_object` call is identical:

```shell script
$ lobotomy add s3.get_object example.yaml
```

However, lobotomy notices the existing call there and so converts the
`get_object` response configuration to a list of responses for you:

```yaml
clients:
  s3:
    Body: 'The contents of my S3 file.'
    LastModified: '2020-11-01T12:23:34Z'
    get_object:
      AcceptRanges: '...'
      Body: '...'
      CacheControl: '...'
      ContentDisposition: '...'
      ContentEncoding: '...'
      ContentLanguage: '...'
      ContentLength: 1
      ContentRange: '...'
      ContentType: '...'
      DeleteMarker: null
      ETag: '...'
      Expiration: '...'
      Expires: '2020-11-04T14:42:51.077364Z'
      LastModified: '2020-11-04T14:42:51.077364Z'
      Metadata: null
      MissingMeta: 1
      ObjectLockLegalHoldStatus: '...'
      ObjectLockMode: '...'
      ObjectLockRetainUntilDate: '2020-11-04T14:42:51.077364Z'
      PartsCount: 1
      ReplicationStatus: '...'
      RequestCharged: '...'
      Restore: '...'
      SSECustomerAlgorithm: '...'
      SSECustomerKeyMD5: '...'
      SSEKMSKeyId: '...'
      ServerSideEncryption: '...'
      StorageClass: '...'
      TagCount: 1
      VersionId: '...'
      WebsiteRedirectLocation: '...'
  sts:
    get_caller_identity:
      Account: '987654321'
```

Finally, edit the new call response configuration and we end up with the
configuration we were looking for:

```yaml
clients:
  sts:
    get_caller_identity:
      Account: '987654321'
  s3:
    get_object:
    - Body: 'The contents of my S3 file.'
      LastModified: '2020-11-01T12:23:34Z'
    - Body: 'Another S3 file.'
      LastModified: '2020-11-03T12:23:34Z'
```

# Advanced Usage

## Key Prefixes

By default configuration files are rooted at the `clients` key within the
file. However, it is possible to specify a different root key prefix, which
is useful when co-locating lobotomy test configuration with other test
configuration data in the same file, or when co-locating multiple lobotomy
test configurations within the same file. To achieve that a prefix must be
specified during patching.

As an example, consider the configuration file:

```yaml
lobotomy:
  test_a:
    clients:
      sts:
        get_caller_identity:
          Account: '987654321'
  test_b:
    clients:
      sts:
        get_caller_identity:
          Account: '123456678'
          UserId: 'AIFASDJWISJAVHXME'
```

In this case the prefixes are `lobotomy.test_a` and `lobotomy.test_b`.
To use these in a test the *prefix* must be specified in the patch:

```python
import pathlib
import lobotomy

config_path = pathlib.Path(__file__).parent.joinpath("validation.yaml")


@lobotomy.patch(config_path, prefix="lobotomy.test_a")
def test_a(lobotomized: lobotomy.Lobotomy):
    """..."""


@lobotomy.patch(config_path, prefix="lobotomy.test_b")
def test_b(lobotomized: lobotomy.Lobotomy):
    """..."""
```

The prefix can be specified as a `.` delimited string, or as a list/tuple.
The list/tuple is needed if the keys themselves contains `.`.

## Patching Targets

By default, lobotomy will patch `boto3.Session`. There are scenarios where
a different patch would be desired either to limit the scope of the patch or
to patch another library wrapping the `boto3.Session` call. In those cases,
specify the patch path argument:

```python
import pathlib
import lobotomy

config_path = pathlib.Path(__file__).parent.joinpath("test.yaml")


@lobotomy.patch(config_path, patch_path="something.else.Session")
def test_another_patch_path(lobotomized: lobotomy.Lobotomy):
    """..."""
```

## Session Configuration

In addition to the clients configurations described above, it is also possible
to configure the session values as well with the `session:` attribute. The
available configuration settings for the session are:

```yaml
session:
  profile_name: some-profile
  region_name: us-west-2
  available_profiles:
    - some-profile
    - some-other-profile
  credentials:
    access_key: A123KEY
    secret_key: somesecretkeyvalue
    token: theaccesstokenifset
    method: how-the-credentials-were-loaded

clients:
  ...
```

All of these values are optional and in cases where they are omitted, but the session
requires having them, they will be defaulted.


## Client Overrides

There are cases where it is desirable to replace one or more service clients with
non-lobotomy objects. Lobotomy supports that by adding client overrides to the patched
lobotomy object:

```python
from unittest.mock import MagicMock

import lobotomy


@lobotomy.patch()
def test_example(lobotomized: lobotomy.Lobotomy):
    """Should do something..."""
    mock_dynamo_db_client = MagicMock()
    lobotomized.add_client_override("dynamodb", mock_dynamo_db_client)
    # continue testing...
```


## Error Handling

The lobotomy library mimics client error handling with a lobotomized version of the
same interface used by the live clients. As such, handling and capturing errors works
transparently. For example,

```python
import boto3
import pytest

import lobotomy


@lobotomy.patch()
def test_client_errors(lobotomized: lobotomy.Lobotomy):
    """Should raise the specified error."""
    lobotomized.add_call(
        service_name="s3",
        method_name="list_objects",
        response={"Error": {"Code": "NoSuchBucket", "Message": "Hello..."}},
    )

    session = boto3.Session()
    client = session.client("s3")

    with pytest.raises(client.exceptions.NoSuchBucket):
        client.list_objects(Bucket="foo")
```

Or the generic client error handling with response codes can be used as well:


```python
import boto3
import pytest

import lobotomy


@lobotomy.patch()
def test_client_errors(lobotomized: lobotomy.Lobotomy):
    """Should raise the specified error."""
    lobotomized.add_call(
        service_name="s3",
        method_name="list_objects",
        response={"Error": {"Code": "NoSuchBucket", "Message": "Hello..."}},
    )

    session = boto3.Session()
    client = session.client("s3")

    with pytest.raises(lobotomy.ClientError) as exception_info:
        client.list_objects(Bucket="foo")

    assert exception_info.value.response["Error"]["Code"] == "NoSuchBucket"
```

## Callable Responses

For more advanced cases it is also possible to use any callable as the source for
generating the response. For example, if I want the response to be different based
on the arguments specified when making the call, I can create a function to return
a result that reflects the inputs.

```python
import typing

import boto3

import lobotomy


def _respond(*args, **kwargs) -> typing.Dict[str, typing.Any]:
    return {
        "Body": "{}.{}".format(kwargs["Bucket"], kwargs["Key"]).encode()
    }


@lobotomy.patch()
def test_callable_responses(lobotomized: "lobotomy.Lobotomy"):
    """Should return the expected body value from the callable response."""
    lobotomized.add_call("s3", "get_object", _respond)

    session = boto3.Session()
    client = session.client("s3")

    response = client.get_object(Bucket="foo", Key="bar")
    assert response["Body"].read() == b"foo.bar"
```

Any callable is supported as long as it accepts the `*args, **kwargs` appropriate to
the calling client service request.
