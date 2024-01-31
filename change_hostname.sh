#!/bin/bash
# /usr/sbin/change_hostname.sh - program to permanently change hostname.  


newHostname=grep -E '^Serial' /proc/cpuinfo | tail -n 1 | cut -c-16
# $1 - new hostname, should be a legal hostname
hostnamectl set-hostname ${$1} --static
