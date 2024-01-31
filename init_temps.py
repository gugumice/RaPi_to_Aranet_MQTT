#!/usr/bin/env python3

import logging
import os, socket
import argparse
import configparser
from time import sleep
from run_temps import get_w1sensors
logging.basicConfig(format = "%(levelname)s: %(asctime)s: %(message)s", level=logging.INFO)

def get_cpu_serial()->str:
    """
    Get CPU serial id to use it as MSQT device ID
    Returns: CPU ID
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

init_config = {
        'log_file': '',
        'root_name': 'Test',
        'send_interval': 5,
        'device_number': get_cpu_serial(),
        'watchdog': '/dev/watchdog',
        'id_significant_nums': 8,
        'broker_host': '10.100.107.199',
        'broker_port': 8883,
        'w1_dev_path' : '/sys/bus/w1/devices/??-*',
        'init_sensor_params' : {'name': 'Term #', 'group': 'Ledusskapis', 'groupId': 1, 'productNumber': 'DS18B20'}
        }

def make_actual_config(config)->dict:
    '''
    Make config for actual RaPi
    In: Initial configuration
    Out: Actual default configuration with IDs of connected 1W sensors
    '''

    w1_sensors =  get_w1sensors(config['w1_dev_path'])
    sl = {}
    for i,s in enumerate(w1_sensors):
        sensor = s[s.rfind('/')+1:]
        sl[sensor] = {'name': init_config['init_sensor_params']['name'].replace('#',str(i+1)),
                     'group': init_config['init_sensor_params']['group'],
                     'groupId': init_config['init_sensor_params']['groupId'],
                     'productNumber': init_config['init_sensor_params']['productNumber']}
    ac = {}
    # Delete init key
    del config['init_sensor_params']
    ac['MQTT'] = config
    ac['sensors'] = sl
    return(ac)

def main():
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
