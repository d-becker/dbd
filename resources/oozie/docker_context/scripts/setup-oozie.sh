python3 scripts/xmlcombine.py /opt/oozie/conf/hadoop-conf/core-site.xml /opt/hadoop/etc/hadoop/core-site.xml > tmp.xml
mv tmp.xml /opt/oozie/conf/hadoop-conf/core-site.xml

echo "Successfully copied the contents of the Hadoop core-site.xml to the Oozie configuration." > docker_oozie_logs.txt

while [ "$(hdfs dfsadmin -report)" = "" ]
do
    sleep 0.5
done

sudo -u hadoop JAVA_HOME=$JAVA_HOME hdfs dfs -mkdir /user
sudo -u hadoop JAVA_HOME=$JAVA_HOME hdfs dfs -mkdir /user/oozie
sudo -u hadoop JAVA_HOME=$JAVA_HOME hdfs dfs -chown -R oozie:oozie /user/oozie
sudo -u hadoop JAVA_HOME=$JAVA_HOME hdfs dfs -chmod -R a+w /

echo "Successfully set up hdfs user directory." >> docker_oozie_logs.txt

/opt/oozie/bin/oozie-setup.sh sharelib create -fs hdfs://namenode:9000

echo "Successfully uploaded the sharelib." >> docker_oozie_logs.txt

sudo -u hadoop JAVA_HOME=$JAVA_HOME hdfs dfs -chmod -R a+rwx /

echo "Write permissions on hdfs." >> docker_oozie_logs.txt

/opt/oozie/bin/oozied.sh start

if [ $? -eq 0 ]
then
    echo "Started the Oozie server." >> docker_oozie_logs.txt 
else
    echo "Could not start the Oozie server." >> docker_oozie_logs.txt
fi

/bin/bash
