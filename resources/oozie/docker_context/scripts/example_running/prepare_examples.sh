# This script will be thrown away.

tar -xzf oozie-examples.tar.gz
hdfs dfs -put examples examples

echo "Examples uploaded to hdfs."

sudo apk add --update --no-cache openrc openssh
ssh-keygen -f ~/.ssh/id_rsa -P ""
cat ~/.ssh/id_rsa.pub > ~/.ssh/authorized_keys

sudo rc-status
sudo touch /run/openrc/softlevel
sudo /etc/init.d/sshd start

echo "SSH server running on localhost."
