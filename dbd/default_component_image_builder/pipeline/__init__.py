#!/usr/bin/env python3

"""
This package contains classes that represent the pipeline and the stages of the component image building process. The
main purpose of organising the build process in a pipeline is to make it possible to cache intermediate results and to
make it easier to add new stages at any point in the pipeline.

The inner stages of the pipeline are essentially transformations on a file: they take the path to the input file, use it
to produce their output and write the output to the output path. The input and output paths are provided when the stage
is executed, not when it is created - the pipeline executor makes sure that the output path of a stage becomes the input
path of the next stage. The reason for this is explained below:

Consider a situation in which the pipeline building takes place incrementally - a general pipeline builder adds the
stages common to all (or most) pipelines, and later a more specific builder adds its own stages. If the input and output
paths were provided when the stages are created, when the more specific builder adds a new stage in between two existing
stages, it would have to modify those stages to update their input and output paths to accomodate the new stage. The
approach taken here makes this step much easier, as the more specific builder can simply insert its own stages anywhere
without any additional modifications.

On both ends of the pipeline, there are special stages. The first stage, which we call entry stage, does not take an
input when it is run. This is because its real input (which can be provided at creation time, if any) may come from
other sources than the filesystem - it may be a web resource, a programmatically generated resource or anything
else. The last stage, called final stage, is the opposite: it does not take an output path, as its output is not
necessarily a file - for example, it can be a docker image.

"""

from .pipeline import EntryStage, FinalStage, Pipeline, Stage
