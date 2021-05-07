import boto3
import json
import os
import base64

s3 = boto3.client('s3')

def lambda_handler(event, context):
    s3_bucket = 'sagemaker-us-east-2-583938224360'
    s3_prefix = 'smartcity-waste-management-garbage-level-training-data/output/garbage-bin-level-forecaster-2021-02-16-16-57-57-804/output'
    s3_file = 'model.tar.gz'
    
    s3_path_key = os.path.join(s3_prefix, s3_file)
    
    
    try:
        response = s3.get_object(Bucket=s3_bucket, Key=s3_path_key)
        payload = response['Body'].read()
        
        return {
            'response_code' : 200,
            'message': 'success',
            'file_name': 'model.tar.gz',
            'Content-Length': response['ContentLength'],
            'Content-Type': response['ContentType'],
            'payload' : payload.hex(),
        }
    except Exception as e:
        return {
            'response_code': 404,
            'message': repr(e),
        }