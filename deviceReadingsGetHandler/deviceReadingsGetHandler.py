import os
import json
import greengrasssdk
import sqlite3
import requests

client = greengrasssdk.client('iot-data')
OUTPUT_TOPIC = 'device/readings/get'
DB_PATH = '/home/pi/edge.db'

def lambda_handler(event, context):
    if '/response' in context.client_context.custom['subject']: # when invoked by a iot topic
        # response came from a iot topic
        # request.put(application endpoint, the event received)
        client.publish(topic=os.path.join(OUTPUT_TOPIC, 'response'), payload=json.dumps({'status': 'success'}))
        return
    else: # when invoked by a API
        client.publish(topic=OUTPUT_TOPIC, payload=json.dumps(os.path.join(OUTPUT_TOPIC, 'response')))
        return {
            'statusCode': 200,
            'body': json.dumps({
                'event': event,
                'context_client_context_custom': context.client_context.custom,
                'context_invoked_function_arn': context.invoked_function_arn
            })
        }
