#!/bin/bash

# This script can be used to set the OOZIE_URL environment variable.
# You need to source the script to take effect in the calling shell:
# source ./oozie_url.sh

function get_fqdn {
    local IP="$(dig +short $(hostname))"
    local HOST_NAME_TMP="$(dig +short -x "$IP")"

    # Delete the last '.' character that dig adds to the reverse DNS result.
    local HOST_NAME="${HOST_NAME_TMP%?}"

    echo "$HOST_NAME"
}

export OOZIE_URL=http://"$(get_fqdn)":11000/oozie
