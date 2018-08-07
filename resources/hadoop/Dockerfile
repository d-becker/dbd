ARG BASE=30
FROM flokkr/base:${BASE}
RUN apk add --update --no-cache libstdc++ findutils ncurses python && rm -rf /var/cache/apk/*
RUN adduser -h /opt/ -s /bin/bash -G flokkr -D hadoop && chown hadoop /opt
USER hadoop
VOLUME /data
RUN sudo chown hadoop /data
ADD 012_hdfsinit /opt/launcher/plugins/012_hdfsinit
RUN sudo chmod o+x /opt/launcher/plugins/012_hdfsinit/hdfsinit.sh
ENV CONF_DIR /opt/hadoop/etc/hadoop
ENV PATH $PATH:/opt/hadoop/bin
ENV JAVA_OPTS_VAR HADOOP_OPTS

COPY tmp/hadoop.tar.gz /opt
RUN tar zxf hadoop.tar.gz && rm hadoop.tar.gz && mv hadoop* hadoop && rm -rf /opt/hadoop/share/doc
RUN mv /opt/hadoop/etc/hadoop /opt/hadoop/etc/hadoop.orig && mkdir -p /opt/hadoop/etc/hadoop && chmod 775 /opt/hadoop/etc/hadoop
WORKDIR /opt/hadoop
ADD log4j.properties /opt/hadoop/etc/hadoop/log4j.properties
#We nedd logs directory writable from hadoop3
RUN mkdir /opt/hadoop/logs
RUN sudo chown -R hadoop /opt/hadoop/etc
RUN chmod g+rwx /opt/hadoop/logs