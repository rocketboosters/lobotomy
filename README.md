# Lobotomy

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

## Basic Usage

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
