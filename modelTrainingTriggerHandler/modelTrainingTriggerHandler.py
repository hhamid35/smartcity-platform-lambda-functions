import os
import json
import boto3

CONTAINERS = {
    'us-west-1': '632365934929.dkr.ecr.us-west-1.amazonaws.com/forecasting-deepar:latest',
    'us-west-2': '433757028032.dkr.ecr.us-west-2.amazonaws.com/forecasting-deepar:latest',
    'us-east-1': '811284229777.dkr.ecr.us-east-1.amazonaws.com/forecasting-deepar:latest',
    'us-east-2': '825641698319.dkr.ecr.us-east-2.amazonaws.com/forecasting-deepar:latest',
}

REGION = boto3.session.Session().region_name

# Role to pass to SageMaker training job that has access to training data in S3, etc
SAGEMAKER_ROLE = os.environ['SAGEMAKER_ROLE']

sagemaker = boto3.client('sagemaker')

def ensure_session(session=None):
    """If session is None, create a default session and return it. Otherwise return the session passed in"""
    if session is None:
        session = boto3.session.Session()
    return session


def lambda_handler(event, context):
    try:
        response = sagemaker.create_training_job(
            TrainingJobName=event['training_job_name'],
            HyperParameters={
                "time_freq": event['freq'],
                "context_length": str(event['context_length']),
                "prediction_length": str(event['prediction_length']),
                "epochs": "400",
                "learning_rate": "5E-4",
                "mini_batch_size": "64",
                "early_stopping_patience": "40",
                "num_dynamic_feat": "auto",
            },
            AlgorithmSpecification={
                'TrainingImage': CONTAINERS[REGION],
                'TrainingInputMode': 'File'
            },
            RoleArn=SAGEMAKER_ROLE,
            InputDataConfig=[
                {
                    'ChannelName': 'train',
                    'DataSource': {
                        'S3DataSource': {
                            'S3DataType': 'ManifestFile',
                            'S3Uri': f's3://{}-training-data/data'.format(event['s3_bucket_base_uri']),
                            'S3DataDistributionType': 'FullyReplicated'
                        }
                    },
                    'ContentType': 'application/json',
                    'CompressionType': 'None'
                }
            ],
            OutputDataConfig={
                'S3OutputPath': f's3://{}-training-data/output'.format(event['s3_bucket_base_uri'])
            },
            ResourceConfig={
                'InstanceType': 'ml.c4.2xlarge',
                'InstanceCount': 1,
                'VolumeSizeInGB': 50
            },
            StoppingCondition={
                'MaxRuntimeInSeconds': 86400
            }
        )
        
    except Exception as e:
        return {
            'statusCode': 500,
            'body': repr(e),
        }
    else:
        return {
            'statusCode': 200,
            'body': repr(response),
        }
