ARG HADOOP_IMAGE
FROM ${HADOOP_IMAGE}
ENV CONF_DIR /opt/hive/conf
ENV HADOOP_HOME /opt/hadoop

ARG GENERATED_DIR=generated
COPY ${GENERATED_DIR}/hive.tar.gz /opt
WORKDIR /opt
RUN tar zxf hive.tar.gz && rm hive.tar.gz && mv apache-hive* hive
ENV PATH $PATH:/opt/hive/bin
ADD defaults/* defaults/
