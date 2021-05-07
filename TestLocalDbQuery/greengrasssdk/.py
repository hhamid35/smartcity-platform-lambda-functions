import greengrasssdk
import sqlite3
import paho.mqtt.client as mqtt

client = greengrasssdk.client('iot-data')
db_conn = sql_connection('/src/test.sqlite')

def sql_connection(db_file):
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Error as e:
        print(e)

def test_local_db_query_run():
    client.


test_local_db_query_run()

def function_handler(event, context):
    return
