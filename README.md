This script enables Raspberry Pi with DS18b20 sensor(s) to emulate Aranet Pro base station sending data to MQTT broker in places where wireless Aranet sensors do not work.
1. Install latest Raspberry PI OS Lite, enable 1-wire interface and update system.
2. Attach DS18b20 sensors to Raspberry Pi and check if they work: cat /sys/devices/w1_busmaster1/28-*/temperatures
3. Create /opt/thermo directory, download files and execute preppi.sh as root
4. Edit config.ini as needed. Sensor group names and group IDs should match corresponding setting.
Script also sends sms messages to phones in list but this feature should be adapted to particular site.
