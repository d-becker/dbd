#!/usr/bin/env bash

REGISTRY=dbd

function usage {
    echo "Usage: $0 MODE VERSION | PATH"
    echo
    echo "MODE is exactly one of the following:"
    echo -e "  -v\tUse a release version. The second argument (VERSION) is a release version string."
    echo -e "  -p\tUse a snapshot version. The second argument (PATH) is a path to a built snapshot distribution on the filesystem."
}

function create_tmp {
    if [ ! -d "tmp" ]
    then
	mkdir tmp
    else
	rm -r tmp/*
    fi
}

function get_tar_released_version {
    HADOOP_VERSION=$1
    TAG=$HADOOP_VERSION
    
    echo "Downloading Hadoop release version $HADOOP_VERSION."

    local URL=https://www-eu.apache.org/dist/hadoop/common/hadoop-$HADOOP_VERSION/hadoop-$HADOOP_VERSION.tar.gz
    create_tmp
    wget ${URL} -O tmp/hadoop.tar.gz
}

function get_tar_dist_path {
    local hadoop_dist_path=$1
    TAG=from_dist_at_$(date "+%s")
    HADOOP_VERSION="SNAPSHOT"

    echo "Preparing Hadoop snapshot version from path $hadoop_dist_path."
    create_tmp
    tar -czf tmp/hadoop.tar.gz -C `dirname $hadoop_dist_path` `basename $hadoop_dist_path`
}

function build {
    echo "Building docker image with Hadoop version $HADOOP_VERSION and tag $TAG."
    docker build --label io.github.flokkr.hadoop.version=$HADOOP_VERSION -t ${REGISTRY}/hadoop:${TAG} .
}

function cleanup {
    rm -r tmp
}

function main {
    if [ $# -ne 2 ]
    then
	usage
	exit 1
    fi
    
    local mode=$1

    if [ "$mode" = "-v" ]
    then
	local hadoop_version=$2
	get_tar_released_version $hadoop_version || exit 1
    elif [ "$mode" = "-p" ]
    then
	local hadoop_dist_path=$2
	get_tar_dist_path $hadoop_dist_path || exit 1
    else
	usage
	exit 1
    fi

    build || exit 1
    cleanup
}

main "$@"
