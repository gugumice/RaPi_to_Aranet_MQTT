#!/bin/bash
if [ ! -e /home/pi ]; then
    echo "Only run this on your pi."
    exit 1
fi
systemctl enable temperatures.service
systemctl disable firstboot.service
raspi-config --expand-rootfs > /dev/null
python3 /opt/temps/config_temps.py
echo "01 10 * * * sudo shutdown -r" >>  /var/spool/cron/crontabs/root
/sbin/shutdown -r now
