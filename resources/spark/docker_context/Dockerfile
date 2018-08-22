ARG HADOOP_IMAGE
FROM ${HADOOP_IMAGE}

ARG GENERATED_DIR=generated
WORKDIR /opt
COPY ${GENERATED_DIR}/spark.tar.gz /opt
RUN tar zxf spark.tar.gz && rm spark.tar.gz && mv spark* spark

ENV CONF_DIR /opt/spark/conf
WORKDIR /opt/spark
COPY init.sh /opt/spark/init.sh
ENV HADOOP_CONF_DIR=/opt/spark/conf
ENV PATH $PATH:/opt/spark/bin
