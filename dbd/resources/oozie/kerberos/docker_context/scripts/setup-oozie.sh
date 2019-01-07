#!/bin/bash

function log {
        local message=$1
        echo "$message" >> docker_oozie_logs.txt
}

function get_fqdn {
    local IP="$(dig +short $(hostname))"
    local HOST_NAME_TMP="$(dig +short -x "$IP")"

    # Delete the last '.' character that dig adds to the reverse DNS result.
    local HOST_NAME="${HOST_NAME_TMP%?}"

    log "Reverse DNS FQDN is $HOST_NAME."
    echo "$HOST_NAME"
}

function copy_hadoop_site_xmls {
    # Copy the *-site.xml files from the Hadoop folder, except for core-site.xml that will be handled separately.
    cp $(find /opt/hadoop/etc/hadoop -name "*-site.xml" | grep -v core-site.xml) /opt/oozie/conf/hadoop-conf/
}

function merge_hadoop_core_site_xml_with_oozie_core_site_xml {
    python3 scripts/xmlcombine.py /opt/oozie/conf/hadoop-conf/core-site.xml /opt/hadoop/etc/hadoop/core-site.xml > tmp.xml && \
    mv tmp.xml /opt/oozie/conf/hadoop-conf/core-site.xml && \
    \
    log "Successfully copied the contents of the Hadoop core-site.xml to the Oozie configuration."
}

function set_oozie_url {
    # TODO: This doesn't do much as the script only modifies its own env vars.
    local FQDN="$1"

    export OOZIE_URL="http://${FQDN}:11000/oozie"
}

function get_oozie_keytab {
    local KERBEROS_SERVER="${KERBEROS_SERVER:-krb5}"
    local ISSUER_SERVER="${ISSUER_SERVER:-$KERBEROS_SERVER:8081}"

    local HOST_NAME="$1"

    local OOZIE_KEYTAB="/opt/oozie/oozie.keytab"
    local OOZIE_HTTP_KEYTAB="/opt/oozie/http.keytab"
    local OOZIE_MERGED_KEYTAB="/opt/oozie/oozie-http.keytab"

    wget http://"$ISSUER_SERVER"/keytab/"$HOST_NAME"/oozie -O "$OOZIE_KEYTAB" && \
    log "Downloaded keytab $OOZIE_KEYTAB." && \
    
    wget http://"$ISSUER_SERVER"/keytab/"$HOST_NAME"/HTTP -O "$OOZIE_HTTP_KEYTAB" && \
    log "Downloaded keytab $OOZIE_HTTP_KEYTAB" && \
    
    printf "%b" "rkt /opt/oozie/oozie.keytab\nrkt /opt/oozie/http.keytab\nwkt $OOZIE_MERGED_KEYTAB" | ktutil && \
    log "Merged Oozie keytabs into $OOZIE_MERGED_KEYTAB."
}

function get_kerberos_tgt {
    local HOST_NAME="$1"

    get_oozie_keytab "$HOST_NAME" && \

    kinit -kt /opt/oozie/oozie-http.keytab oozie/"$HOST_NAME" && \
    log "Obtained Kerberos TGT."
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

function move_hbase_common_jar_to_lib {
    mv /opt/oozie/hbase-common-*.jar /opt/oozie/lib
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

function main {
    local HOST_NAME="$(get_fqdn)"

    copy_hadoop_site_xmls && \
    merge_hadoop_core_site_xml_with_oozie_core_site_xml && \
    set_oozie_url "$HOST_NAME" && \
    get_kerberos_tgt "$HOST_NAME" && \
    wait_for_hadoop && \
    set_up_hdfs_oozie_directory && \
    upload_sharelib && \
    move_hbase_common_jar_to_lib && \
    set_write_permissions_on_hdfs && \
    start_oozie
}

main
