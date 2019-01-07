# Dockerised Big Data (dbd)

## Introduction
This tool’s aim is to make it easy to set up a working dockerized big data infrastructure where the versions of the
components (Hadoop, Hive, Oozie etc.) can be set individually, and even unreleased snapshot builds can be used. This
makes integration testing a lot less cumbersome.

The tool takes a configuration file called the _BuildConfiguration_ as input, builds the required docker images and
produces a directory with a docker-compose file that can be used to start up the dockerised cluster.

The docker images built by dbd and many of the scripts building them are based on the [flokkr
project](https://github.com/flokkr).

## Prerequisites
* Docker
  
  Dbd uses docker to simulate computer clusters. This means that you need to have docker installed and the docker
  daemon running while using dbd.

* Python3
  
  To use dbd, you need at least python 3.6. If you would like to build a python wheel of dbd (recommended), you
  also need the setuptools python package.

* Maven
  
  To use release versions of the Oozie component, you also need maven as it is necessary to build Oozie.

Dbd also has a number of python packages it depends on, therefore it is recommended to install it from a (locally built)
python wheel, as in this case the dependencies are installed together with it. See instruction below on how to to this.

## Installation
After cloning the repository, you can run dbd directly from the source using the `run_dbd.py` file, but the recommended
way is to make a python wheel and install it using `pip`. This ensures that the python dependencies of the project also
get installed along with dbd.

To create a wheel, run the following command:

```
python3 setup.py bdist_wheel
```

To install dbd from the wheel, run the following command (you may have to to adjust version numbers):

```
pip3 install dist/dbd-0.1-py3-none-any.whl
```

Now you can use dbd as follows:

```
dbd --help
```

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

It is also possible to specify configuration options for the services belonging to the components. These options
overwrite the default options if they exist. Adding new services, however, is not possible. The following example
illustrates this:

```
name: oozie500hadoop265
components:
  hadoop:
    release: 2.6.5
  oozie:
    release: 5.0.0
    services:
      oozieserver: # One of the services belonging to the Oozie component
	    ports:
		  - 11000:11000
		  - 11002:11002
```

This will map ports 11000 and 11002 in the container to the same ports on the host machine. To find out what services
each component uses and what the default configuration is, consult the components' resource files - you can find more
information about them in the DEVELOPER_GUIDE.md file in this repository.

When you have created the _BuildConfiguration_ file, run the following in a terminal from the root of this repository:

```
python3 run_dbd.py <build_configuration_file> <output_directory>
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
python3 -m unittest discover -v -t . -s dbd/test
```
