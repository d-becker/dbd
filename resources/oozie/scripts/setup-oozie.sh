touch docker_oozie_logs.txt

python scripts/xmlcombine.py /opt/oozie/conf/hadoop-conf/core-site.xml /opt/hadoop/etc/hadoop/core-site.xml > tmp.xml
mv tmp.xml /opt/oozie/conf/hadoop-conf/core-site.xml

echo "Successfully copied the contents of the Hadoop core-site.xml to the Oozie configuration." > docker_oozie_logs.txt

while [ "$(hdfs dfsadmin -report)" = "" ]
do
    sleep 0.5
done

sudo -u hadoop JAVA_HOME=$JAVA_HOME hdfs dfs -mkdir /user
sudo -u hadoop JAVA_HOME=$JAVA_HOME hdfs dfs -mkdir /user/oozie
sudo -u hadoop JAVA_HOME=$JAVA_HOME hdfs dfs -chown -R oozie:oozie /user/oozie
sudo -u hadoop JAVA_HOME=$JAVA_HOME hdfs dfs -chmod -R g+w /

echo "Successfully set up hdfs user directory." >> docker_oozie_logs.txt

/opt/oozie/bin/oozie-setup.sh sharelib create -fs hdfs://namenode:9000

echo "Successfully uploaded the sharelib." >> docker_oozie_logs.txt

echo "Write permissions on hdfs." >> docker_oozie_logs.txt

tar -xzf oozie-examples.tar.gz
hdfs dfs -put examples examples

echo "Examples uploaded to hdfs." >> docker_oozie_logs.txt

/opt/oozie/bin/oozied.sh start

echo "Started the Oozie server." >> docker_oozie_logs.txt 

/bin/bash