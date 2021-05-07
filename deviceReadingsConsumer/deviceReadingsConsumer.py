import json
import logging
import platform
import sys
import time

import greengrasssdk

logger = logging.getLogger(__name__)
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

client = greengrasssdk.client("iot-data")

OUT_TOPIC = "device/readings/put/response"
def function_handler(event, context):
    try:
        client.publish(
            topic=OUT_TOPIC,
            payload=json.dumps(
                {"message": "Hello world! Sent from Greengrass Core"}
            ),
        )
    except Exception as e:
        client.publish(
            topic=OUT_TOPIC,
            payload=json.dumps(
                {"message": repr(e)}
            ),
        )
        logger.error("Failed to publish message: " + repr(e))
    return