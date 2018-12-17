#!/bin/bash

OOZIE_HADOOP_FILES="/opt/oozie/conf/hadoop-config.xml \
                    /opt/oozie/conf/hadoop-conf/core-site.xml"

echo "$OOZIE_HADOOP_FILES" | xargs sed -ie "s|hdfs/_HOST|nn/_HOST|g" && \
echo "$OOZIE_HADOOP_FILES" | xargs sed -ie "s/LOCALREALM/EXAMPLE.COM/g" && \
/opt/hadoop/resolve_HOSTs.py --oozie
/opt/oozie/scripts/setup-oozie.sh
