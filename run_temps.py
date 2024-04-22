#!/usr/bin/env python3
#https://github.com/eclipse/paho.mqtt.python
import os,sys
import argparse
import logging
import configparser
import time
import json
import requests
import paho.mqtt.publish as publish
from ds18b20_lib import TempSensor,get_w1sensors

running = True
cfg = None
wdObj = None

#Interval in secs to send retained messages
mqtt_send_retained_interval = 3600

def init_logging(cfg) -> None:
    '''
    Set up logging
    '''
    if len(cfg['MQTT']["log_file"]) > 0:
        try:
            logging.basicConfig(
                format="%(asctime)s - %(message)s",
                filename=cfg['MQTT']["log_file"],
                filemode="w",
                level=logging.ERROR,
            )
            logging.info('Logging to {}.'.format(cfg['MQTT']["log_file"]))
        except:
            logging.error('Error opening {}. Logging to console'.format(cfg['MQTT']["log_file"]))
    else:
        logging.basicConfig(format = "%(levelname)s: %(asctime)s: %(message)s", level=logging.INFO)
        logging.info('Logging to console')
def init_watchdog():
    global wdObj
    if cfg['watchdog'] is not None:
        try:
            wdObj = open(cfg['watchdog'], "w")
            logging.info("Watchdog enabled on {}".format(cfg['watchdog']))
        except Exception as e:
            logging.error(e)
    else:
        logging.info("Watchdog disabled")

def send_sms(call, phones, messages):
    '''
    Send sms
    '''
    for phone in phones:
        for message in messages:
            r=requests.get(call.format(phone,message))
            logging.info(call.format(phone,message))
            logging.info('Response: {}'.format(r))

def make_retain_mqtt_messages(w1_sensors) -> list:
    '''
    Make retainded MQTT messages for Aranet compatability
    from sensor data and config.ini device descriptors
    In: array of w1 sensors
    Out: List of topic,payload tuples as MTQQ messages
    '''
    global cfg
    sign_num=int(cfg['MQTT']['id_significant_nums'])
    messages = []
    for s in w1_sensors:
        id = s.id[-sign_num:]
        deviceNumber = s.deviceNumber[-12:]
        msg_topic = '{}/{}/sensors/{}/name/'.format(cfg['MQTT']['root_name'],deviceNumber,id)
        msg_payload = s.name
        messages.append((msg_topic, msg_payload,0,1))
        #productNumber
        msg_topic = '{}/{}/sensors/{}/productNumber/'.format(cfg['MQTT']['root_name'],deviceNumber,id)
        msg_payload = s.productNumber
        messages.append((msg_topic, msg_payload,0,1))
        #group
        msg_topic = '{}/{}/sensors/{}/group/'.format(cfg['MQTT']['root_name'],deviceNumber,id)
        msg_payload = s.group
        messages.append((msg_topic, msg_payload,0,1))
        #groupid
        msg_topic = '{}/{}/sensors/{}/groupId/'.format(cfg['MQTT']['root_name'],deviceNumber,id)
        msg_payload = s.groupId
        messages.append((msg_topic, msg_payload,0,1))
    return(messages)

def make_temp_mqtt_message(objSensor) -> list:
    '''
    Make MQTT messages for Aranet compatability
    In: DS18b20 class object
    Out: List of topic,payload tuples as MTQQ messages
    '''
    global cfg
    sign_num = int(cfg['MQTT']['id_significant_nums'])
    id = objSensor.id[-sign_num:]
    topic='{}/{}/sensors/{}/json/measurements'.format(cfg['MQTT']['root_name'], objSensor.deviceNumber, id)
    payload=json.dumps({'temperature': str(objSensor.temp), 'rssi': '0', 'time': int(time.time()), 'battery': "1"})
    return((topic, payload,0,0))

def send_mqtt_msg(messages,hostname='10.100.107.199', port=8883, client_id=None) -> bool:
    '''
    Make MQTT messages to broker
    In: list of MTQQ messages
    Out: bool
    '''
    if client_id is None:
        client_id=cfg['MQTT']['device_number'][-8:]
    client_id=cfg['MQTT']['device_number'][-8:]
    try:
        publish.multiple(messages, hostname=hostname, port=port, client_id=client_id)
    except Exception as e:
        logging.error("Error sending message: {}".format(e))
        return(False)
    for m in messages:
        logging.info("Sent:".format(m))
    return(True)

def main() -> None:
    global cfg
    global wdObj
    cfg = configparser.ConfigParser()
    app_path=os.path.dirname(os.path.realpath(__file__))
    parser = argparse.ArgumentParser(description="Rapi as Aranet MQTT base")
    parser.add_argument(
        "-c",
        "--config",
        type=str,
        metavar="file",
        help="Name of config file. Default: config.ini",
        default="{}/config.ini".format(app_path),
    )
    args = parser.parse_args()
    #Read config file
    try:
        cfg.read(args.config)
    except Exception as e:
        logging.critical('{}\n{}'.format(args.config,e))
        sys.exit(1)
    init_logging(cfg)
    mqtt_send_interval = 60 * float(cfg['MQTT']['mqtt_send_interval_mins'])
    mqtt_send_retained_time = time.time()
    #Initialize w1 sensor ojects
    w1_sensors = get_w1sensors(cfg['MQTT']['w1_dev_path']) 
    w1_sensor_array=[]
    for t in w1_sensors:
        o=TempSensor(t)
        try:
            sd = json.loads(cfg['sensors'][o.id].replace("'", '"'))
        except KeyError as e:
            m = 'Sensor {} not found in w1_devices'.format(e)
            send_sms(call = cfg['MQTT']['http_call'], phones = [cfg['MQTT']['sms_recipients'].split(',')[0]], messages = [m])
            time.sleep(2)
            sys.exit(1)
        o.name = sd['name']
        o.group = sd['group']
        o.groupId = sd['groupId']
        o.productNumber = sd['productNumber']
        o.deviceNumber = cfg['MQTT']['device_number'][-12:]
        o.min_temp = float(sd['min_temp'])
        o.max_temp = float(sd['max_temp'])
        o.alarm_grace_secs = sd['alarm_grace_min']*60
        w1_sensor_array.append(o)
    [s.start() for s in w1_sensor_array]
    #Send Start SMS message to first phone num in list
    m = 'RPI {} On'.format(cfg['MQTT']['device_number'][-int(cfg['MQTT']['id_significant_nums']):])
    send_sms(call = cfg['MQTT']['http_call'], phones = [cfg['MQTT']['sms_recipients'].split(',')[0]], messages = [m])
    del m
    mqtt_send_time = time.time() - mqtt_send_interval - 3
    mqtt_send_retained_time = time.time() - mqtt_send_retained_interval - 3
    sms_messages = []
    mqtt_mesages = []
    while running:
        #Pat watchdog
        if wdObj is not None:
            print('1',file = wdObj, flush = True)
        for o in w1_sensor_array:
            o.read()
            if time.time() > mqtt_send_retained_time + mqtt_send_retained_interval:
            #Send retained MQTT messages (sensor names,groups,etc)
                mqtt_mesages = make_retain_mqtt_messages(w1_sensor_array)
                mqtt_send_retained_time = time.time()
            if o.status in ('CRC Error','N/A'):
                #Send sms if error reading sensor
                sms_messages.append('{}:{} {}'.format(o.id, o.name, o.status))
            if time.time() > mqtt_send_time + mqtt_send_interval:
                mqtt_mesages.append(make_temp_mqtt_message(o))
            if o.alarm:
                msg = "{}, Group: {} min: {} max: {} curr: {}".format(o.name, o.group, o.min_temp, o.max_temp, o.temp)
                logging.info(msg)
                sms_messages.append(msg)
                o.resetAlarm()
        if len(sms_messages) > 0:
            send_sms(call = cfg['MQTT']['http_call'], phones = cfg['MQTT']['sms_recipients'].split(','), messages = sms_messages)
            sms_messages = []
        if len(mqtt_mesages) > 0:
            send_mqtt_msg(mqtt_mesages, hostname=cfg['MQTT']['broker_host'], port=int(cfg['MQTT']['broker_port']))
            mqtt_mesages =[]
            mqtt_send_time = time.time()
        time.sleep(5)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        running = False
        if wdObj is not None:
            print('V', file=wdObj, flush=True)
            print('Watchdog disabled')
        print('\nExiting...')
        sys.exit(0)
