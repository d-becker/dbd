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

function get_kerberos_tgt {
    local IP="$(dig +short $(hostname))"
    local HOST_NAME_TMP="$(dig +short -x "$IP")"

    # Delete the last '.' character that dig adds to the reverse DNS result.
    local HOST_NAME="${HOST_NAME_TMP%?}"

    kinit -kt /opt/hadoop/etc/hadoop/oozie.keytab oozie/"$HOST_NAME"
}

function wait_for_hadoop {
    while [ "$(hdfs dfsadmin -report)" = "" ]
    do
        sleep 0.5
    done

    log "Hdfs is up and running."
}

function set_up_hdfs_oozie_directory {
    hdfs dfs -mkdir -p /user/oozie && \
    hdfs dfs -chown -R oozie:oozie /user/oozie && \
    hdfs dfs -chmod -R a+w / && \
    \
    log "Successfully set up hdfs user directory."
}

function upload_sharelib {
    /opt/oozie/bin/oozie-setup.sh sharelib create -fs hdfs://namenode:9000 && \
    \
    log "Successfully uploaded the sharelib."
}

function set_write_permissions_on_hdfs {
    hdfs dfs -chmod -R a+rwx / && \
    \
    log "Write permissions on hdfs."
}

function start_oozie {
    log "Starting the Oozie server."

    /opt/oozie/bin/oozied.sh run
}

merge_hadoop_core_site_xml_with_oozie_core_site_xml && \
get_kerberos_tgt && \
wait_for_hadoop && \
set_up_hdfs_oozie_directory && \
upload_sharelib && \
set_write_permissions_on_hdfs && \
start_oozie
