#!/usr/bin/env python3

import logging
import os, socket
import argparse
import configparser
from run_temps import get_w1sensors
logging.basicConfig(format = "%(levelname)s: %(asctime)s: %(message)s", level=logging.INFO)

def get_cpu_serial() -> str:
    """
    Get CPU serial id to use it as MSQT device ID
    """
    cpuserial = None
    try:
        with open('/proc/cpuinfo','r') as f:
            lines= f.readlines()
        for l in lines:
            if l.startswith('Serial'):
                cpuserial = l[10:26]
    except Exception as e:
        logging.error(e)
    return(cpuserial)

init_config: dict = {
        'log_file': '',
        'root_name': 'Test',
        'mqtt_send_interval_mins': 5,
        'device_number': get_cpu_serial(),
        'device_name': socket.gethostname(),
        'watchdog': '/dev/watchdog',
        'id_significant_nums': 6,
        'broker_host': '10.100.107.199',
        'broker_port': 8883,
        'w1_dev_path' : '/sys/bus/w1/devices/28-*',
        'sms_recipients' : '+37129111111,+3712922222',
        'http_call' : "http://cache.egl.local/csp/sarmite/sys.sms.cls?number={}&text={}",
        'init_sensor_params' : {'name': 'Term #', 'group': 'Ledusskapis', 'groupId': 1, 'productNumber': 'DS18B20', 'min_temp':2.0, 'max_temp':8.0, 'alarm_grace_min': 10}
        }

def make_actual_config(config: dict) -> dict:
    '''
    Make config for actual RaPi 

    '''
    w1_sensors =  get_w1sensors(config['w1_dev_path'])
    sl = {}
    for i,s in enumerate(w1_sensors):
        sensor = s[s.rfind('/')+1:]
        sl[sensor] = {'name': init_config['init_sensor_params']['name'].replace('#',str(i+1)),
                     'group': init_config['init_sensor_params']['group'],
                     'groupId': init_config['init_sensor_params']['groupId'],
                     'productNumber': init_config['init_sensor_params']['productNumber'],
                     'min_temp': init_config['init_sensor_params']['min_temp'],
                     'max_temp': init_config['init_sensor_params']['max_temp'],
                     'alarm_grace_min': init_config['init_sensor_params']['alarm_grace_min']
                     }
    ac = {}
    # Delete init key
    del config['init_sensor_params']
    ac['MQTT'] = config
    ac['sensors'] = sl
    return(ac)

def main() -> None:
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
    cfg = configparser.ConfigParser()
    # Write config to configparser object
    for k,v in make_actual_config(init_config).items():
        cfg[k] = v
    # Create ini file
    try:
        with open(args.config, 'w') as configfile:
            cfg.write(configfile)
        logging.info('File {} created\n'.format(configfile))
    except Exception as e:
        logging.error('{}:\t{}'.format(e))

if __name__ == '__main__':
    main()
