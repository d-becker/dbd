# This script will be thrown away.
# It is used to upload the Oozie examples to hdfs and install 
# and start the ssh server that is needed by the ssh example.

function upload_examples {
    tar -xzf oozie-examples.tar.gz
    hdfs dfs -put examples examples

    echo "Examples uploaded to hdfs."
}


function setup_and_start_ssh_server {
    sudo apk add --update --no-cache openrc openssh
    ssh-keygen -f ~/.ssh/id_rsa -P ""
    cat ~/.ssh/id_rsa.pub > ~/.ssh/authorized_keys

    sudo rc-status
    sudo touch /run/openrc/softlevel
    sudo /etc/init.d/sshd start

    echo "SSH server running on localhost."
}

upload_examples
setup_and_start_ssh_server

