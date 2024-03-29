#!/usr/bin/env python3
import argparse
import glob,os,sys
import logging
import configparser
import json
import threading
import paho.mqtt.client as mqtt
from datetime import datetime,timedelta
from time import sleep

cfg = configparser.ConfigParser()
#1W device path
w1_dev_path = '/sys/bus/w1/devices/??-*'
#Dict for DS1820 readings
temperature_measurements={}
lock=threading.Lock()

def get_w1sensors(path) -> list:
    '''
    Returns list of 1W sensors
    '''
    sensors = glob.glob(path)
    if len(sensors) == 0:
        logging.error('W1 devices not found')
        sys.exit(1)
    return(sensors)

def read_sensor(sensor_id) -> None:
    """
    Thread function to read DS 18b20 temperature sensor
    Write temperature reading to global temperature_measurements dict
    """
    global temperature_measurements
    id = sensor_id[sensor_id.rfind('/')+1:]
    try:
        with open('{}/w1_slave'.format(sensor_id),'r') as s:
            raw_lines = s.readlines()
    except Exception as e:
        logging.error(e)
        with lock:
            temperature_measurements[id]=None
        return()
    if raw_lines[0].strip()[-3:] == 'YES':
        temp_pos=raw_lines[1].find('t=')
        with lock:
            temperature_measurements[id] = round(float(raw_lines[1][temp_pos+2:])/1000,2)
    else:
        with lock:
            temperature_measurements[id]=None
        logging.error('{} CRC error'.format(sensor_id))

def take_temperatures(w1_sensors) -> None:
    '''
    Get readings from sensors.
    Each sensor is red by seperate thread
    '''
    threads = []
    for s in w1_sensors:
        
        t = threading.Thread(target=read_sensor, args=(s,))
        threads.append(t)
        t.start()
    for t in threads:
        t.join()

def make_retain_messages(w1_sensors) -> list:
    '''
    Make retainded MQTT messages for Aranet compatability
    from sensor data and config.ini device descriptors
    In: touple with full paths to 1w sensors
    Out: List of topic,payload tuples as MTQQ messages
    '''
    messages=[]
    sign_num=int(cfg['MQTT']['id_significant_nums'])
    for s in w1_sensors:
        sensor_id = s[s.rfind('/')+1:]
        #Name
        msg_topic = '{}/{}/sensors/{}/name/'.format(cfg['MQTT']['root_name'],cfg['MQTT']['device_number'][-sign_num:],sensor_id[-sign_num:])
        msg_payload = json.loads(cfg['sensors'][sensor_id].replace("'", '"'))['name']
        messages.append((msg_topic, msg_payload))
        #productNumber
        msg_topic = '{}/{}/sensors/{}/productNumber/'.format(cfg['MQTT']['root_name'],cfg['MQTT']['device_number'][-sign_num:],sensor_id[-sign_num:])
        msg_payload = json.loads(cfg['sensors'][sensor_id].replace("'", '"'))['productNumber']
        messages.append((msg_topic, msg_payload))
        #group
        msg_topic = '{}/{}/sensors/{}/group/'.format(cfg['MQTT']['root_name'],cfg['MQTT']['device_number'][-sign_num:],sensor_id[-sign_num:])
        msg_payload = json.loads(cfg['sensors'][sensor_id].replace("'", '"'))['group']
        messages.append((msg_topic, msg_payload))
        #groupid
        msg_topic = '{}/{}/sensors/{}/groupId/'.format(cfg['MQTT']['root_name'],cfg['MQTT']['device_number'][-sign_num:],sensor_id[-sign_num:])
        msg_payload = json.loads(cfg['sensors'][sensor_id].replace("'", '"'))['groupId']
        messages.append((msg_topic, msg_payload))
    return(messages)

def make_temperature_messages(temperature_measurements) -> list:
    '''
    Make MQTT messages for Aranet compatability
    In: temperature measurements from sensors
    Out: List of topic,payload tuples as MTQQ messages
    '''
    sign_num=int(cfg['MQTT']['id_significant_nums'])
    messages=[]
    for k,v in temperature_measurements.items():
        topic='{}/{}/sensors/{}/measurements'.format(cfg['MQTT']['root_name'], cfg['MQTT']['device_number'][-sign_num:],k[-sign_num:])
        payload=json.dumps({'temperature': v, 'rssi': 0, 'time': int(datetime.now().timestamp()), "battery": "1.00"})
        messages.append((topic, payload))
    return(messages)

def send_mqtt_msg(messages,host='10.100.107.199', port=8883,qos=0, retain=False,client=None) -> bool:
    '''
    Send MQTT messages to broker
    Return True if sending succeded
    '''
    logging.debug('Sending host: {}, port: {}, qos: {} retain: {}'.format(host,port,qos,retain))
    client = mqtt.Client(client)
    try:
        client.connect(host, port)
    except Exception as e:
        logging.error(e)
        return(False)
    for i,m in enumerate(messages):
        logging.debug('Sending {}: topic: {}, payload: {}, retain: {}'.format(i, m[0],m[1],retain))
        s = client.publish(m[0],m[1],retain)
        logging.debug('Message status: {}'.format(s))
    client.disconnect()
    return(True)

def initialize_logging(cfg) -> None:
    '''
    Set up logging
    '''
    if len(cfg['MQTT']["log_file"]) > 0:
        try:
            logging.basicConfig(
                format="%(asctime)s - %(message)s",
                filename=cfg['MQTT']["log_file"],
                filemode="w",
                level=logging.INFO,
            )
            logging.info('Logging to {}.'.format(cfg['MQTT']["log_file"]))
        except:
            logging.error('Error opening {}. Logging to console'.format(cfg['MQTT']["log_file"]))
    else:
        logging.basicConfig(format = "%(levelname)s: %(asctime)s: %(message)s", level=logging.DEBUG)
        logging.info('Logging to console')
def initialize_watcdog(cfg) -> object:
    '''
    Set up watchdog
    '''
    if len(cfg['MQTT']["watchdog"].strip()) > 0:
        try:
            watchdog_obj = open(cfg['MQTT']["watchdog"], "w")
            logging.info("Watchdog enabled on {}".format(cfg['MQTT']["watchdog"]))
        except Exception as e:
            logging.error(e)
        return(watchdog_obj)
    return(None)

def main() -> None:
    watchdog_obj = None
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
    try:
        cfg.read(args.config)
    except Exception as e:
        logging.critical('{}\n{}'.format(args.config,e))
        sys.exit(1)

    initialize_logging(cfg)

    watchdog_obj = initialize_watcdog(cfg)

    w1_sensors=get_w1sensors(w1_dev_path)
    retained_messages = make_retain_messages(w1_sensors)
    send_mqtt_msg(retained_messages, host=cfg['MQTT']['broker_host'], port=int(cfg['MQTT']['broker_port']), retain=False, client=cfg['MQTT']['device_number'])
    #Set timer for sending interval (minutes)
    msg_sent_interval = timedelta(minutes=float(cfg['MQTT']['send_interval']))
    msg_sent_last = datetime.now() - msg_sent_interval
    while True:
        #Pat watchdog
        if watchdog_obj is not None:
            print("V", file=watchdog_obj, flush=True)
        take_temperatures(w1_sensors)
        temperature_messages = make_temperature_messages(temperature_measurements)
        if datetime.now() > msg_sent_last + msg_sent_interval:
            send_mqtt_msg(temperature_messages, host=cfg['MQTT']['broker_host'], port=int(cfg['MQTT']['broker_port']), retain=False, client=cfg['MQTT']['device_number'])
            msg_sent_last=datetime.now()
            logging.debug('Sending thermometer readings')
        sleep(10)

if __name__ == '__main__':
    main()
