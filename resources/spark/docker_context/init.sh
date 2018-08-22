while [ "$(hdfs dfsadmin -report)" = "" ]
do
    sleep 0.5
done

hdfs dfs -mkdir /sparklog
hdfs dfs -chmod 777 /sparklog
hdfs dfs -chmod 777 /

export SPARK_DIST_CLASSPATH=$(hadoop classpath)

bin/spark-class org.apache.spark.deploy.history.HistoryServer
