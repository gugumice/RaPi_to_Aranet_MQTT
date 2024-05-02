#!/bin/bash
if [ ! -e /home/pi ]; then
    echo "Only run this on your pi."
    exit 1
fi
systemctl enable thermometers.service
systemctl disable firstboot.service
raspi-config --expand-rootfs > /dev/null
echo "01 10 * * * sudo shutdown -r" >>  /var/spool/cron/crontabs/root
sleep 1
newHostname=rapi-mqtt$(grep -E '^Serial' /proc/cpuinfo | tail -n 1 | cut -c 22-28)
hostnamectl set-hostname $newHostname --static
echo ${newHostname} > /etc/hostname
sed -i '/^127.0.0.1/s/.*/127.0.0.1\t'${newHostname}'/g' /etc/hosts
sed -i '/^#NTP=.*/a FallbackNTP=laiks.egl.local' /etc/systemd/timesyncd.conf
echo '10.100.20.104   laiks.egl.local' >> /etc/hosts
echo '10.100.50.102   cache.egl.local' >> /etc/hosts
chmod a+x /opt/thermo/*.py opt/thermo/*.sh
python3 /opt/thermo/init_temps.py
sleep 3
/sbin/shutdown -r now
