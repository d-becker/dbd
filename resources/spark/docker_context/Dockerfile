# Base Spark image on the Hadoop image in the same BuildConfiguration.
ARG HADOOP_IMAGE
FROM ${HADOOP_IMAGE}

# Add the generated Spark archive to the image.
ARG GENERATED_DIR=generated
WORKDIR /opt
COPY ${GENERATED_DIR}/spark.tar.gz /opt

# Extract and Spark.
RUN tar zxf spark.tar.gz && rm spark.tar.gz && mv spark* spark

# Set environment variables.
ENV CONF_DIR /opt/spark/conf
ENV HADOOP_CONF_DIR=/opt/spark/conf
ENV PATH $PATH:/opt/spark/bin

# Copy the initialisation script to the image. It will run at startup.
WORKDIR /opt/spark
COPY init.sh /opt/spark/init.sh

