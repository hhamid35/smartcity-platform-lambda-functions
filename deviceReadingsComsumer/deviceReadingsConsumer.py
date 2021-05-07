import os
import sys
import json
import logging
import requests
import greengrasssdk

import sqlite3

client = greengrasssdk.client('iot-data')

OUTPUT_TOPIC = 'device/readings/put/response'
DB_PATH = '/home/pi/edge.db'

def get_device_id(con, device_name):
    cur = con.cursor()
    cur.execute('SELECT deviceID FROM devices WHERE deviceName=?', (device_name,))
    device_id = cur.fetchall()[0][0]
    return device_id

def get_device_type(con, device_id):
    cur = con.cursor()
    cur.execute('SELECT deviceType FROM devices WHERE deviceID=?',(device_id,))
    device_type = cur.fetchall()[0][0]
    return device_type

def get_application_id(con, device_id):
    cur = con.cursor()
    cur.execute('SELECT applicationID FROM registrations WHERE deviceID=?', (device_id,))
    application_id = cur.fetchall()[0][0]
    return application_id

def get_application_endpoint(con, application_id):
    cur = con.cursor()
    cur.execute('SELECT applicationEndpoint FROM applications WHERE applicationID=?', (application_id,))
    application_endpoint = cur.fetchall()[0][0]
    return application_endpoint
    
def get_application_port(con, application_id):
    cur = con.cursor()
    cur.execute('SELECT applicationPort FROM applications WHERE applicationID=?', (application_id,))
    application_port = cur.fetchall()[0][0]
    return application_port

def get_application_name(con, application_id):
    cur = con.cursor()
    cur.execute('SELECT applicationName FROM applications WHERE applicationID=?', (application_id,))
    application_name = cur.fetchall()[0][0]
    return application_name   

def function_handler(event, context):
    response = {
        'status': 'unsuccessful'
    }
    try:        
        con = sqlite3.connect(DB_PATH)
        
        device_id = get_device_id(con, event['deviceName'])
        application_id = get_application_id(con, device_id)
        application_endpoint = get_application_endpoint(con, application_id)
        application_port = get_application_port(con, application_id)
        application_name = get_application_name(con, application_id)
        device_type = get_device_type(con, device_id)

        http_request = {
            'applicationName': application_name,
            'edgeName': 'Toronto-Region-1',
            'deviceName': event['deviceName'], 
            'deviceIP': event['deviceIP'],
            'deviceType': device_type,
            'capacity': event['capacity'],
            'longitude': event['longitude'],
            'latitude': event['latitude'],
            'timestamp': event['timestamp'],
        }
        
        
        
        client.publish(topic=OUTPUT_TOPIC, payload=json.dumps(http_request))
        
        application_url_prefix = 'http://' + application_endpoint + ':' + str(application_port)
        application_url  = application_url_prefix + '/devices'
        # r = requests.get(application_url, data = http_request)
        r = requests.get(application_url)
        
        if r.status_code != 200:
            response['status'] = 'error when sending readings to the application'
        else:
            response['status'] = 'successs'
            response['devices'] = r.json()
            
        logging.info(response)
    except Exception as e:
        logging.error(e)
        response['status'] = repr(e)
    finally:
        con.close()

    client.publish(topic=OUTPUT_TOPIC, payload=json.dumps(response))

    return