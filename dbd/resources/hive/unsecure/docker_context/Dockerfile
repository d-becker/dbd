# Base the Hive image on the Hadoop image in the same BuildConfiguration.
ARG HADOOP_IMAGE
FROM ${HADOOP_IMAGE}

# Set up configuration directories and environment variables.
ENV CONF_DIR /opt/hive/conf
ENV HADOOP_HOME /opt/hadoop

# Add the generated Hive archive to the image.
ARG GENERATED_DIR=generated
COPY ${GENERATED_DIR}/hive.tar.gz /opt

# Extract and set up Hive
WORKDIR /opt
RUN tar zxf hive.tar.gz && rm hive.tar.gz && mv apache-hive* hive
ENV PATH $PATH:/opt/hive/bin
ADD defaults/* defaults/
