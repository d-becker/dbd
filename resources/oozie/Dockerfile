ARG HADOOP_IMAGE
FROM ${HADOOP_IMAGE}
USER root
RUN apk add --update --no-cache python zip
WORKDIR /opt
COPY tmp/oozie.tar.gz /opt
RUN tar zxf oozie.tar.gz && rm oozie.tar.gz && mv oozie* oozie
RUN adduser -h /opt/oozie -s /bin/bash -G flokkr -D oozie \
    && addgroup supergroup \
    && adduser oozie supergroup \
    && chown -R oozie /opt/oozie
USER oozie
WORKDIR /opt/oozie
COPY scripts ./scripts
COPY oozie-site_additional.xml .
RUN python scripts/xmlcombine.py /opt/oozie/conf/oozie-site.xml ./oozie-site_additional.xml > tmp.xml \
    && mv tmp.xml /opt/oozie/conf/oozie-site.xml
ENV OOZIE_URL http://oozieserver:11000/oozie
