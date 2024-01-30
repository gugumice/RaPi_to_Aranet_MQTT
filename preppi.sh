#!/bin/bash

systemctl disable bluetooth.service
systemctl disable hciuart.service
apt-get update && apt-get -y upgrade

ln /opt/therm/thermometers.service /lib/systemd/system/thermometers.service
ln /opt/therm/firstboot.service /lib/systemd/system/firstboot.service
ln /opt/therm/config.ini /home/pi/config.ini
systemctl enable firstboot.service

timedatectl set-timezone Europe/Riga
sed -i '/^# Additional overlays.*/a dtoverlay=pi3-disable-wifi\ndtoverlay=pi3-disable-bt' /boot/config.txt
sed -i '/^\[all\].*/a gpu_mem=16' /boot/config.txt

sleep 3
addgroup thermo
usermod -a -G thermo pi
mkdir /var/log/thermo
touch /var/log/thermo/thermo.log
ln -s /var/log/thermo/thermo.log /home/pi/thermo.log
chown -R pi:thermo /var/log/thermo
addgroup watchdog
usermod -a -G watchdog pi
apt-get --yes install python3-pip
sed -i '/^\[global\]$/a break-system-packages = true' /etc/pip.conf

echo 'KERNEL=="watchdog", MODE="0660", GROUP="watchdog"' > /etc/udev/rules.d/60-watchdog.rules
sed -i '/^#NTP=.*/a FallbackNTP=laiks.egl.local' /etc/systemd/timesyncd.conf
chattr -i /etc/hosts
echo '10.100.20.104   laiks.egl.local' >> /etc/hosts
chattr +i /etc/hosts
pip3 --no-input install configparser
pip3 --no-input install paho-mqtt
#/usr/sbin/shutdown -r now