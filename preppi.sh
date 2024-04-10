#!/bin/bash

systemctl disable bluetooth.service
systemctl disable hciuart.service
apt-get update && apt-get -y upgrade

ln /opt/thermo/thermometers.service /lib/systemd/system/thermometers.service
ln /opt/thermo/firstboot.service /lib/systemd/system/firstboot.service
ln /opt/thermo/config.ini /home/pi/config.ini
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
chown -R pi:thermo /opt/thermo/
addgroup watchdog
usermod -a -G watchdog pi
apt-get --yes install python3-pip
sed -i '/^\[global\]$/a break-system-packages = true' /etc/pip.conf
pip install paho-mqtt

echo 'KERNEL=="watchdog", MODE="0660", GROUP="watchdog"' > /etc/udev/rules.d/60-watchdog.rules
#/usr/sbin/shutdown -r now
