import boto3
import json

s3 = boto3.client('s3')

def lambda_handler(event, context):
#"sagemaker-us-east-2-583938224360"
#"smartcity-waste-management-garbage-level-training-data/output/garbage-bin-level-forecaster-2021-02-16-16-57-57-804/output/sample-text-file.txt"
    bucket = "sagemaker-us-east-2-583938224360"
    key = "smartcity-waste-management-garbage-level-training-data/output/garbage-bin-level-forecaster-2021-02-16-16-57-57-804/output/sample-text-file.txt"
    s3_file = 'model.tar.gz'
    
    try:
        data = s3.get_object(Bucket=bucket,Key=key)
        json_data = data["Body"].read()
        
        return{
            "response_code" : 200,
            "data" : str(json_data)
        }
    except Exception as e:
        print(e)
        raise e