# Developer guide

## Introduction
This document is intended as a manual for developers who want to modify, extend or just better understand the codebase.

## BuildConfiguration file format
The _BuildConfiguration_ file is the place where the user specifies which components they want to have in their
dockerised cluster, what versions they should be or, if the user wants to use a snapshot build of some of the
components, where these snapshot builds are located on the filesystem. The _BuildConfiguration_ file is a yaml file
containing two dictionary keys:

* name: Defines the name of the _BuildConfiguration_. This does not have to be the same as the name of the
  _BuildConfiguration_ file.
* components: A dictionary containing the configuration of the components. For more details, see below.

### The components dictionary
The keys of the `components` dictionary are the names of the components to include in the dockerised cluster. The values
are dictionaries themselves, which contain the configuration for the specific component.

During the build proces, these inner dictionaries are passed to the component image builders that build the docker
images of the components. Each component image builder implementation is allowed to take custom configuration keys, but
all should support at least `release` and `snapshot`, exactly one of which must be specified in the dictionary. The
meaning of these keys is as follows:

* `release`: The corresponding value is a release version number. The appropriate release distribution is obtained and
  used to build the docker image. The most common way of obtaining the release distribution is downloading it from the
  internet, but implementations are allowed to retrieve it by other means, such as from a designated repository or a
  local cache.
* `snapshot`: The corresponding value is a filesystem path to a built snapshot distribution of the component. Currently
  it has to be a directory, but later it may be changed to an archive. The image builder uses this directory and its
  contents to build the docker image. Note that this does not mean building the component from source - that has to be
  done manually by the user. Implementations are allowed to cache intermediate results and images.
* Specifying none or both of `release` and `snapshot` results in an error.

### Example
The following is an example _BuildConfiguration_ file:

```
name: oozie430hadoop265
components:
  hadoop:
    release: 2.6.5
  oozie:
    snapshot: ~/OOZIE/oozie/distro/target/oozie-4.3.0-distro/oozie-4.3.0
```

The name of the _BuildConfiguration_ is `oozie430hadoop265`. There will be two components in the dockerised cluster:
Hadoop and Oozie. The Hadoop image will use the release distribution with version number 2.6.5, while the Oozie image
will use the distribution that was built by the user and is found locally at
`~/OOZIE/oozie/distro/target/oozie-4.3.0-distro/oozie-4.3.0`.

Note that having two components does not mean the dockerised cluster will consist of two docker containers. Components
may require multiple services, each of which runs in a separate container. For example, for Hadoop, there will be two
types of containers: name node and data node. Furthermore, docker-compose makes it possible to replicate services and
run them in multiple containers, for example there may be multiple data node containers in the dockerised cluster.

## Adding a new component
To add a new component that this tool can build, essentially two things are needed:

* resource files in the appropriate location
* a component image builder object, which implements the `component_builder.ComponentImageBuilder` interface.

Depending on how the component image is to be built, it may be enough to provide the resource files and the tool will
use the default component image building mechanism, which is to use the
`default_component_image_builder.DefaultComponentImageBuilder` class, passing the data read from the resource files to
it along with default values for its subcomponents. For more information on how it works, see its class documentation.

If you need to customise the component building process, read the [component image builder
objects](#component-image-builder-objects) section. Even for custom build processes, the `DefaultComponentImageBuilder`
class can be of use.

### Resource files
The intended location of a component's resource files is in the `resources` directory, under a subdirectory that has the
component's name. For example, the resource files of Oozie are located under `<repository_root>/resources/oozie`. The
`ComponentImageBuilder` implementations, however, should not use these paths directly, but obtain the resource path from
the `built_config` parameter passed to the `build` method. This makes the dependencies of the class more explicit and
the code more flexible.

The files that the main application needs are the following:

* compose-config_part: Contains configuration that should be in configuration xml files such as `core-site.xml`,
  `hive-site.xml` etc. The format (and the implementation) are from the [flokkr project](https://github.com/flokkr),
  documented [here](https://github.com/flokkr/docker-baseimage#envtoconf-simple-configuration-loading). The
  configuration specified in this file should be specific to the component. The `compose-config_part` files of the
  components will be concatenated by the main application to form a general configuration file in the output directory.
* docker-compose_part.yaml: Contains the component-specific parts of the `docker-compose` file that will be
  generated. The `docker-compose_part.yaml` files of the components will be merged by the main application. To reference
  the docker image name of the component, use variables of the form `${<COMPONENT_NAME_CAPITALISED>_IMAGE}`, for example
  for the Oozie image, `${OOZIE_IMAGE}` is used.
* assembly.yaml: A yaml file that contains key-value pairs of component-specific information. 

	One of the keys is `dependencies`, and the corresponding value is a list of the names of the other components that
  this component depends on. If the key is missing, an empty list is assumed.
  
  The `DefaultComponentImageBuilder` class, which is the type of the image builders of all existing components, uses the
  following additional keys:
  * `url`: A url templated with the version number of the component, from which the release archive can be
        downloaded. In the string, \"{version}\" is the placholder for the version number.
  * `version_command`: The command that should be run inside the built docker container to retrieve the component's
        version number. The actual version number will be obtained by matching `version_regex` against the output of
        this command.
  * `version_regex`: The regex that will be matched against the output of `version_command` to retrieve the actual
        version number.
		
  Custom component image builders can require or accept different keys.

The value associated with the `dependencies` key is a list with the names of the other components that the component
depends on. This may for example mean that the docker image of the present component should be based on the image of
another component, or that the present component needs to be built against the specified version of the dependency.

* Note that while building the components from source is avoided where possible and considered to be the user's
  responsibility, sometimes it cannot be avoided. For example Oozie does not come with a built distribution and its
  component builder implementation must build it from source. Also, the Oozie docker image is based on the Hadoop image,
  therefore Oozie lists Hadoop as its dependency.
  
The main application builds a dependency graph from the dependencies of the components. If there is a cycle in the
dependency graph, the application exits with an error message. Otherwise, the images are built in the correct order,
meaning dependencies are alwalys built before the images that depend on them.
 
Although it is possible to implement a `ComponentImageBuilder` that works differently, the
`DefaultComponentImageBuilder` class makes use of the following convention, so any additinal `ComponentImageBuilder`
should also do so:

In the resources directory of each component, there should be a a directory with the name `docker_context`. It should
contain the Dockerfile and any files that need to be in the docker build directory when building the image, except for
the file(s) that will be generated by the build process. This directory is considered immutable and should not be used
directly as the docker build directory. Instead, its contents should be copied to a new (ideally temporary) directory
along with the generated files. For more information on how this is done by `DefaultComponentImageBuilder`, see its
class documentation.

### Component image builder objects
If the default build process is not enough for your case, you can use a custom component image builder. In this case,
you must provide a python module that has the same name as the component - exactly the same character string that is
specified as the component name in the _BuildConfiguration_ file - therefore, component names must be valid python
module names. These modules are found by their names and loaded dynamically by the main application, so they need to be
available on the python path. The easiest way of achieving this is putting the component module source files in the same
directory as the main application source. If no module is found for a component, the default component image building
mechanism will be used.

The component modules must contain a function with the following signature:
```
def get_image_builder(assembly: Dict[str, Any], cache_dir: Path) -> component_builder.ComponentImageBuilder:
	...
```

The `assembly` parameter contains the key-value pairs that were read from the `assembly.yaml` file.

The `cache_dir` parameter is a `pathlib.Path` object pointing to the root cache directory. The image builders are not
required to use caching, but if they do, this directory should be used for it.

To build the component images, the main application calls the `build` method of the `ComponentImageBuilder` objects. The
`ComponentImageBuilder` of a component has access to configuration and build information of its dependencies (and other
previously built components) through the `built_config` parameter. This includes attributes that may only be generated
at build time, such as docker image names in case of snapshot builds.
