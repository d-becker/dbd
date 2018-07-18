#!/usr/bin/env python3

import os, sys, yaml

def parse_yaml(filename):
    with open(filename) as file:
        text = file.read()
        return yaml.load(text)

def get_hadoop_config(config):
    hadoop_dict = config["components"]["hadoop"]

    release = "release" in hadoop_dict
    snapshot = "snapshot" in hadoop_dict
    
    if release and snapshot:
        raise RuntimeError("Both release and snapshot mode specified.")

    if not release and not snapshot:
        raise RuntimeError("None of release and snapshot mode specified.")

    mode = ""
    if release:
       mode = "release"
    else:
        mode = "snapshot"

    argument = hadoop_dict[mode]
    return (mode, argument)
        

def build_hadoop_image(mode, argument):
    if mode == "release":
        os.system("hadoop/build.sh -v {}".format(argument))

def ensure_hadoop_image_exists(mode, argument):
    # Check if the image exists and if not, build it.
    pass
    
def main():
    filename = sys.argv[1]
    conf = parse_yaml(filename)

    (mode, argument) = get_hadoop_config(conf)
    build_hadoop_image(mode, argument)    

main()
        
