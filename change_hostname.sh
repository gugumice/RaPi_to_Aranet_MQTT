#!/bin/bash
# /usr/sbin/change_hostname.sh - program to permanently change hostname.  Permissions
# are set so that www-user can `sudo` this specific program.

# args:
# $1 - new hostname, should be a legal hostname
hostnamectl set-hostname ${$1} --static
#sed -i "s/$HOSTNAME/$1/g" /etc/hosts
#echo $1 > /etc/hostname
#/etc/init.d/hostname.sh
#subprocess.run(['sudo', '/usr/sbin/change_hostname.sh', newhostname])