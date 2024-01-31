#!/bin/bash
if [ ! -e /home/pi ]; then
    echo "Only run this on your pi."
    exit 1
fi
systemctl enable temperatures.service
systemctl disable firstboot.service
raspi-config --expand-rootfs > /dev/null
sleep 3
python3 /opt/temps/config_temps.py

newHostname=rapi-mqtt$(grep -E '^Serial' /proc/cpuinfo | tail -n 1 | cut -c 22-28)
hostnamectl set-hostname $newHostname --static

sleep 2
echo "01 10 * * * sudo shutdown -r" >>  /var/spool/cron/crontabs/root
/sbin/shutdown -r now
