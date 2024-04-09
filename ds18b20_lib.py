#!/usr/bin/env python3
import logging
import time
import threading
import glob,sys

def get_w1sensors(path) -> list:
    '''
    Returns list of 1W sensors
    '''
    sensors = glob.glob(path)
    if len(sensors) == 0:
        logging.error('W1 devices not found')
        sys.exit(1)
    return(sensors)

class Ds18b20Sensor(threading.Thread):
    def __init__(self,path):
        super().__init__()
        self.path='{}/w1_slave'.format(path)
        #self.id = path[path.rfind('/')+1:]
        self.temp = None
        self.status = None
    def run(self):
        self.temp = None
        self.status = None
        try:
            with open(self.path,'r') as s:
                raw_lines = s.readlines()
        except Exception as e:
            self.status = e
            return
        if raw_lines[0][29:35] == 'crc=00':
            self.status = 'N/A'
            return 
        if (len(raw_lines) > 0) and (raw_lines[0].strip()[-3:] == 'YES'):
                temp_pos=raw_lines[1].find('t=')
                self.temp = round(float(raw_lines[1][temp_pos+2:])/1000,2)
                return
        self.status = 'CRC Error'

class TempSensor(Ds18b20Sensor):
    def __init__(self, path):
        super().__init__(path)
        self.id = path[path.rfind('/')+1:]
        self.name = None
        self.group = None
        self.groupId = None
        self.productNumber = 'DS18B20'
        self.deviceNumber = None
        self.max_temp = 8.00
        self.min_temp = 2.00
        self.alarm_grace_secs = 30
        self._alarm_detected_time = None
        self.alarm = False
    def read(self):
        self.run()
        if self.status is None:
            #Sensor OK, check if temps in range
            if self.temp < self.min_temp:
                self.status = 'Temp LOW'
            elif self.temp > self.max_temp:
                self.status = 'Temp HIGH'
        if self.status is not None:
            if self._alarm_detected_time is None:
                #Set alarm time
                self._alarm_detected_time = time.time()
            else:
                #If alarm grace period is over set alarm to true
                if time.time() > self._alarm_detected_time + self.alarm_grace_secs:
                    self.alarm = True
        else:
            #Everything Ok, disable alarms if any
            self.resetAlarm()
    def resetAlarm(self):
        self._alarm_detected_time = None
        self.status = None
        self.alarm = False

def main():
    path = '/sys/bus/w1/devices/28-*'
    w1_sensors = [TempSensor(s) for s in get_w1sensors(path)]
    logging.basicConfig(format = "%(levelname)s: %(asctime)s: %(message)s", level=logging.DEBUG)
    [s.start() for s in w1_sensors]
    for i in range(50):
        [s.read() for s in w1_sensors]
        [print('stat:{}, alarm:{}, id:{}, temp:{}'.format(t.status, t.alarm, t.id, t.temp)) for t in w1_sensors]
        time.sleep(1)

if __name__ == '__main__':
    main()