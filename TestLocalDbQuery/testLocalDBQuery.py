import os
import sys
import json
import logging

import greengrasssdk

import sqlite3

client = greengrasssdk.client('iot-data')

OUTPUT_TOPIC = 'test/test/response'
DB_PATH = '/home/pi/edge.db'

def get_input_topic(context):
    try:
        topic = context.client_context.custom['subject']
    except Exception as e:
        logging.error('Topic could not be parsed. ' + repr(e))
    return topic

def get_input_message(event):
    try:
        message = event['message']
    except Exception as e:
        logging.error('Message could not be parsed. ' + repr(e))
    return message
    
def get_device_name(con):
    cur = con.cursor()
    cur.execute('SELECT deviceName FROM devices')
    device_name = cur.fetchall()[0][0]
    return device_name

def function_handler(event, context):
    try:
        input_topic = get_input_topic(context)
        
        con = sqlite3.connect(DB_PATH)
        device_name = get_device_name(con)
        
        response = 'Invoked on topic "%s" with device name "%s"' % (input_topic, device_name)
        logging.info(response)
    except Exception as e:
        logging.error(e)
    finally:
        con.close()

    client.publish(topic=OUTPUT_TOPIC, payload=response)

    return