bin/oozie job -config examples/apps/java-main/job.properties -run -DnameNode=hdfs://namenode:9000 -DjobTracker=resourcemanager:8032
