#!/usr/bin/env python3
import paho.mqtt.client as mqtt
import logging
hostname = '10.100.107.199'
broker_port = 8883
topic = 'mqtt/rpi'

client = mqtt.Client()
client.on_Connect = on_connect
client.connect(hostname, broker_port, 60)

def on_connect():
    logging.info('Connected with result code {}'.format('rc'))