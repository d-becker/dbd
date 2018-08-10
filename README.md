# Dockerised Big Data (dbd)

## Introduction
This tool’s aim is to make it easy to set up a working dockerized big data infrastructure where the versions of the
components (Hadoop, Hive, Oozie etc.) can be set individually, and even unreleased snapshot builds can be used. This
makes integration testing a lot less cumbersome.

The docker images built by dbd and many of the scripts building them are based on the [flokkr
project](https://github.com/flokkr).

## Usage
First you need to specify which components you would like to use and what version or local snapshot build they should
be. You do it in a _BuildConfiguration_, which is a simple yaml file. It should contain a _name_ attribute and a
dictionary called _components_. The following is a simple example:

```
name: oozie500hadoop265
components:
  hadoop:
    release: 2.6.5
  oozie:
    release: 5.0.0
```

Each component takes a dictionary of configuration options. The set of recognised options may be different for each
component, but all of them recognise `release` and `snapshot`. If `release` is specified, the corresponding value is a
release version number - for `snapshot`, the value is a local filesystem path to an already built
distribution. Specifying both results in an error.

When you have created the _BuildConfiguration_ file, run the following in a terminal from the root of this repository:

```
dbd/dbd.py <build_configuration_file> <output_directory>
```

Replace `<build_configuration_file>` with your _BuildConfiguration_ file and `<output_directory>` with the directory
where you want to generate the output. The output directory must already exist. For the complete set of options, run
`dbd/dbd.py --help`.

Dbd will build the docker images needed by your _BuildConfiguration_. The release distributions will be downloaded from
the internet, while the snapshot versions are read from the local filesystem path provided in the _BuildConfiguration_
file. The tool may reuse existing images or otherwise use caching to speed up the build process.

The output of the build is a directory whose name is composed of the _BuildConfiguration_ name and a timestamp. For the
example above, the directory name would be something like `oozie500hadoop265_1533642997`. It is located within the
output directory that was specified on the command line. The directory contains - along with various other files - a
`docker-compose.yaml` file. You can use [docker-compose](https://docs.docker.com/compose/) to run your dockerised
cluster.

## Running mypy, pylint and tests
To run mypy, execute the following from the repository root:

```
mypy -p dbd
```

To run pylint, execute the following from the repository root:
```
pylint dbd
```

To run the tests, execute the following from the repository root:
```
python3 -m unittest discover -v -t dbd -s test
```
