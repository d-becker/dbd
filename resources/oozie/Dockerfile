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
ENV OOZIE_URL http://localhost:11000/oozie
