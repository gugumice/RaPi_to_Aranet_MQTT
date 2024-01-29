#!/bin/bash
if [ ! -e /home/pi ]; then
    echo "Only run this on your pi."
    exit 1
fi
systemctl enable kiosk.service
systemctl disable firstboot.service
raspi-config --expand-rootfs > /dev/null
CURRENT_HOSTNAME=$(cat /proc/sys/kernel/hostname)
IPO=$(ip -o -4 addr list eth0 | awk '{print $4}' | cut -d/ -f1 |  cut -d. -f2);
NEW_HOSTNAME="rpi-kio4-"$IPO
echo $CURRENT_HOSTNAME
echo $NEW_HOSTNAME
sleep 1
hostnamectl set-hostname ${NEW_HOSTNAME} --static
echo "01 10 * * * sudo shutdown -r" >>  /var/spool/cron/crontabs/root
/sbin/shutdown -r now