#!/usr/bin/env bash

REGISTRY=dbd

function usage {
    echo "Usage: $0 MODE (VERSION | PATH) HADOOP_TAG HADOOP_VERSION"
    echo
    echo "MODE is exactly one of the following:"
    echo -e "  -v\tUse a release version. The second argument (VERSION) is a release version string."
    echo -e "  -p\tUse a snapshot version. The second argument (PATH) is a path to a built snapshot distribution on the filesystem."
    echo "  HADOOP_TAG is the tag of the Hadoop docker image to base the new Oozie image on."
    echo "  HADOOP_VERSION is the version of Hadoop (e.g. 2.6.0) against which the Oozie distribution will be built. Only used if building in -p mode."
}

function create_tmp {
    if [ ! -d "tmp" ]
    then
	mkdir tmp
    else
	rm -r tmp/*
    fi
}

function cleanup {
    rm -r tmp
}

function release {
    if [ $# -ne 3 ]
    then
	echo "Too many or few arguments in release mode."
	usage
	exit 1
    fi
	
    local oozie_version=$1
    local hadoop_image_tag=$2
    local hadoop_version=$3

    create_tmp
    local URL="https://www-eu.apache.org/dist/oozie/$oozie_version/oozie-$oozie_version.tar.gz"
    echo "Downloading Oozie release version $oozie_version."
    wget ${URL} -O tmp/oozie-src.tar.gz &&
    tar -xzf tmp/oozie-src.tar.gz -C tmp &&
    rm tmp/oozie-src.tar.gz &&
    mv tmp/oozie* tmp/oozie &&
    tmp/oozie/bin/mkdistro.sh -Puber -Phadoop.version=$hadoop_version -DskipTests &&
    mv tmp/oozie/distro/target/oozie-$oozie_version-distro.tar.gz tmp/oozie.tar.gz &&
    rm -r tmp/oozie || exit 1

    local tag=${oozie_version}_h$hadoop_version
    echo "Building docker image tagged $tag with Oozie release version $oozie_version based on Hadoop image with tag $hadoop_image_tag."
    echo docker build --build-arg HADOOP_TAG=$hadoop_image_tag -t ${REGISTRY}/oozie:${tag} .
    docker build --build-arg HADOOP_TAG=$hadoop_image_tag -t ${REGISTRY}/oozie:${tag} .
}

function snapshot {
    if [ $# -ne 2 ]
    then
	echo "Too many or few arguments in snapshot mode."
	usage
	exit 1
    fi

    local oozie_dist_path=$1
    local hadoop_image_tag=$2
    local tag=from_dist_at_$(date "+%s")

    echo "Preparing Oozie snapshot version from path $oozie_dist_path."
    create_tmp
    tar -czf tmp/oozie.tar.gz -C `dirname $oozie_dist_path` `basename $oozie_dist_path`

    echo "Building docker image tagged $tag with Oozie snapshot version based on Hadoop image with tag $hadoop_image_tag."
    docker build --build-arg HADOOP_TAG=$hadoop_image_tag -t ${REGISTRY}/oozie:${tag} .
}

function main {
    local mode=$1
    shift
    
    if [ "$mode" = "-v" ]
    then
	release "$@" || exit 1
    elif [ "$mode" = "-p" ]
    then
	snapshot "$@" || exit 1
    else
	usage
	exit 1
    fi

    cleanup
}


main "$@"
