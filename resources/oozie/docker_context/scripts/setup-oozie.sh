#!/bin/bash

python3 scripts/xmlcombine.py /opt/oozie/conf/hadoop-conf/core-site.xml /opt/hadoop/etc/hadoop/core-site.xml > tmp.xml
mv tmp.xml /opt/oozie/conf/hadoop-conf/core-site.xml

function log {
        local message=$1
        echo "$message" >> docker_oozie_logs.txt
}

log "Successfully copied the contents of the Hadoop core-site.xml to the Oozie configuration."

while [ "$(hdfs dfsadmin -report)" = "" ]
do
    sleep 0.5
done

sudo -u hadoop JAVA_HOME="$JAVA_HOME" hdfs dfs -mkdir /user
sudo -u hadoop JAVA_HOME="$JAVA_HOME" hdfs dfs -mkdir /user/oozie
sudo -u hadoop JAVA_HOME="$JAVA_HOME" hdfs dfs -chown -R oozie:oozie /user/oozie
sudo -u hadoop JAVA_HOME="$JAVA_HOME" hdfs dfs -chmod -R a+w /

log "Successfully set up hdfs user directory."

/opt/oozie/bin/oozie-setup.sh sharelib create -fs hdfs://namenode:9000

log "Successfully uploaded the sharelib."

sudo -u hadoop JAVA_HOME="$JAVA_HOME" hdfs dfs -chmod -R a+rwx /

log "Write permissions on hdfs."

/opt/oozie/bin/oozied.sh run
