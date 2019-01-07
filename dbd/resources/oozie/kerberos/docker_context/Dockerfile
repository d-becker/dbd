# Base the Oozie image on the Hadoop image in the same BuildConfiguration.
ARG HADOOP_IMAGE
FROM ${HADOOP_IMAGE}

# Install python3 needed for configuring Oozie.
USER root
RUN apk add --update --no-cache python3 zip

# Add the generated Oozie archive to the image.
ARG GENERATED_DIR=generated
WORKDIR /opt
COPY ${GENERATED_DIR}/oozie.tar.gz /opt

# Extract Oozie.
RUN tar zxf oozie.tar.gz && rm oozie.tar.gz && mv oozie* oozie

# Setup the oozie user and add it to its groups.
RUN adduser -h /opt/oozie -s /bin/bash -G flokkr -D oozie \
    && adduser oozie supergroup \
    && chown -R oozie /opt/oozie \
    && passwd -d oozie

# Copy the scripts and files needed to configure Oozie.
USER oozie
WORKDIR /opt/oozie
COPY scripts ./scripts
COPY oozie-site_additional.xml .

# Download the hbase-common.jar file.
ARG HBASE_COMMON_JAR_VERSION
RUN wget http://central.maven.org/maven2/org/apache/hbase/hbase-common/${HBASE_COMMON_JAR_VERSION}/hbase-common-${HBASE_COMMON_JAR_VERSION}.jar

# Add the contents of the oozie-site_additional.xml file to oozie-site.xml.
RUN python3 scripts/xmlcombine.py /opt/oozie/conf/oozie-site.xml ./oozie-site_additional.xml > tmp.xml \
    && mv tmp.xml /opt/oozie/conf/oozie-site.xml
