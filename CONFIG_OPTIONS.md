# Configuration options

This file  lists the configuration properties accepted in the `BuildConfiguration` file.

## Top-level properties
__name__

The name of the `BuildConfiguration`. This will be used in the name of the output directory. This does not have to be
the same as the name of the `BuildConfiguration` file.

__kerberos__

A boolean indicating whether the dockerised cluster should use Kerberos.

__components__

A yaml dictionary containing the configuration options of the components. The keys are the names of the components, the
values are the configuration.

## Properties in `components`
__release__ or __snapshot__

If `release` is specified, the corresponding value is a release version number - for `snapshot`, the value is a local
filesystem path to an already built distribution. Specifying both results in an error.

__services__

It is possible to specify configuration options for the services belonging to the components. These options overwrite
the default options if they exist. Adding new services, however, is not possible.

### Oozie-specific properties

__hbase-common-jar-version__

When using Kerberos, Oozie needs the hbase-common-{version}.jar to be present. This property specifies its version
number. If ommitted, a default value will be used.
