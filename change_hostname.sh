#!/bin/bash
# /usr/sbin/change_hostname.sh - program to permanently change hostname.  
# $1 - new hostname prefix, should be a legal hostname
newHostname=${$1}$(grep -E '^Serial' /proc/cpuinfo | tail -n 1 | cut -c 22-28)
hostnamectl set-hostname $newHostname --static
