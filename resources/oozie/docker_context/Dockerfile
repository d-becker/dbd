ARG HADOOP_IMAGE
FROM ${HADOOP_IMAGE}
USER root
RUN apk add --update --no-cache python3 zip

ARG GENERATED_DIR=generated
WORKDIR /opt
COPY ${GENERATED_DIR}/oozie.tar.gz /opt
RUN tar zxf oozie.tar.gz && rm oozie.tar.gz && mv oozie* oozie
RUN adduser -h /opt/oozie -s /bin/bash -G flokkr -D oozie \
    && adduser oozie supergroup \
    && chown -R oozie /opt/oozie \
    && passwd -d oozie
USER oozie
WORKDIR /opt/oozie
COPY scripts ./scripts
COPY oozie-site_additional.xml .
RUN python3 scripts/xmlcombine.py /opt/oozie/conf/oozie-site.xml ./oozie-site_additional.xml > tmp.xml \
    && mv tmp.xml /opt/oozie/conf/oozie-site.xml
ENV OOZIE_URL http://oozieserver:11000/oozie
