#/usr/bin/env bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

KERBEROS_SERVER=${KERBEROS_SERVER:-krb5}
ISSUER_SERVER=${ISSUER_SERVER:-$KERBEROS_SERVER\:8081}

IP=$(dig +short `hostname`)
HOST_NAME_TMP=$(dig +short -x "$IP")

# Delete the last '.' character that dig adds to the reverse DNS result.
export HOST_NAME=${HOST_NAME_TMP%?}

for NAME in ${KERBEROS_KEYTABS}; do               
   echo "Download $NAME/$HOST_NAME@... keytab file"                             
   wget http://$ISSUER_SERVER/keytab/$HOST_NAME/$NAME -O $CONF_DIR/$NAME.keytab
   echo "Run wget http://$ISSUER_SERVER/keytab/$HOST_NAME/$NAME -O $CONF_DIR/$NAME.keytab" #########
   KERBEROS_ENABLED=true
done                                 
                                           
for NAME in ${KERBEROS_KEYSTORES}; do                                   
   echo "Download keystore files for $NAME"                             
   wget http://$ISSUER_SERVER/keystore/$NAME -O $CONF_DIR/$NAME.keystore
   KERBEROS_ENABLED=true   
   KEYSTORE_DOWNLOADED=true
done                                  
                                                                                 
if [ -n "$KEYSTORE_DOWNLOADED" ]; then                                           
  wget http://$ISSUER_SERVER/keystore/$HOST_NAME -O $CONF_DIR/$HOST_NAME.keystore
  wget http://$ISSUER_SERVER/truststore -O $CONF_DIR/truststore
fi                                 
                                                                                    
if [ -n "$KERBEROS_ENABLED" ]; then                                                 
   cat $DIR/krb5.conf |  sed "s/SERVER/$KERBEROS_SERVER/g" | sudo tee /etc/krb5.conf
fi                   
                     
call-next-plugin "$@"
