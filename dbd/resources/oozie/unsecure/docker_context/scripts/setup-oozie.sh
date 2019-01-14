#!/bin/bash

function log {
        local message=$1
        echo "$message" >> docker_oozie_logs.txt
}

function merge_hadoop_core_site_xml_with_oozie_core_site_xml {
    python3 scripts/xmlcombine.py /opt/oozie/conf/hadoop-conf/core-site.xml /opt/hadoop/etc/hadoop/core-site.xml > tmp.xml && \
    mv tmp.xml /opt/oozie/conf/hadoop-conf/core-site.xml && \
    \
    log "Successfully copied the contents of the Hadoop core-site.xml to the Oozie configuration."
}

function wait_for_hadoop {
    until hdfs dfsadmin -report;
    do
	log "HDFS is not ready." && \
	sleep 0.5;
    done

    log "Hdfs is up and running."
}

function set_up_hdfs_oozie_directory {
    sudo -u hadoop JAVA_HOME="$JAVA_HOME" hdfs dfs -mkdir /user && \
    sudo -u hadoop JAVA_HOME="$JAVA_HOME" hdfs dfs -mkdir /user/oozie && \
    sudo -u hadoop JAVA_HOME="$JAVA_HOME" hdfs dfs -chown -R oozie:oozie /user/oozie && \
    sudo -u hadoop JAVA_HOME="$JAVA_HOME" hdfs dfs -chmod -R a+w / && \
    \
    log "Successfully set up hdfs user directory."
}

function upload_sharelib {
    /opt/oozie/bin/oozie-setup.sh sharelib create -fs hdfs://namenode:9000 && \
    \
    log "Successfully uploaded the sharelib."
}

function set_write_permissions_on_hdfs {
    sudo -u hadoop JAVA_HOME="$JAVA_HOME" hdfs dfs -chmod -R a+rwx / && \
    \
    log "Write permissions on hdfs."
}

function start_oozie {
    log "Starting the Oozie server."

    /opt/oozie/bin/oozied.sh run
}

merge_hadoop_core_site_xml_with_oozie_core_site_xml && \
wait_for_hadoop && \
set_up_hdfs_oozie_directory && \
upload_sharelib && \
set_write_permissions_on_hdfs && \
start_oozie
