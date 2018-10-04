#!/bin/bash

while [ "$(hdfs dfsadmin -report)" = "" ]
do
    sleep 0.5
done

hdfs dfs -mkdir /sparklog
hdfs dfs -chmod 777 /sparklog
hdfs dfs -chmod 777 /

SPARK_DIST_CLASSPATH=$(hadoop classpath)
export SPARK_DIST_CLASSPATH

bin/spark-class org.apache.spark.deploy.history.HistoryServer
