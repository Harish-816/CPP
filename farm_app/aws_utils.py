import json
import os
from functools import lru_cache
import boto3
from django.conf import settings

@lru_cache(maxsize=1)
def get_aws_config():
    """
    Load one JSON secret from AWS Secrets Manager.
    Example secret value (JSON):
    {
      "S3_BUCKET_NAME": "cpp-my-test-bucket",
      "SQS_QUEUE_URL": "https://sqs.eu-west-1.amazonaws.com/123456789012/smartfarm-queue",
      "SNS_TOPIC_ARN": "arn:aws:sns:eu-west-1:123456789012:smartfarm-topic",
      "DYNAMODB_TABLE": "SmartFarmAnalysis"
    }
    """
    region = settings.AWS_REGION_NAME
    secret_name = settings.AWS_SECRET_NAME

    client = boto3.client('secretsmanager', region_name=region)
    response = client.get_secret_value(SecretId=secret_name)

    if 'SecretString' in response:
        secret_str = response['SecretString']
    else:
        secret_str = response['SecretBinary'].decode('utf-8')

    return json.loads(secret_str)


def get_s3_client():
    region = settings.AWS_REGION_NAME
    return boto3.client('s3', region_name=region)


def get_sqs_client():
    region = settings.AWS_REGION_NAME
    return boto3.client('sqs', region_name=region)


def upload_file_to_s3(local_path: str, s3_key: str) -> str:
    """
    Upload local file to S3 and return public URL (assuming bucket is public or behind CloudFront).
    """
    conf = get_aws_config()
    bucket_name = conf['S3_BUCKET_NAME']
    s3 = get_s3_client()

    s3.upload_file(local_path, bucket_name, s3_key)

    url = f"https://{bucket_name}.s3.{settings.AWS_REGION_NAME}.amazonaws.com/{s3_key}"
    return url


def send_analysis_message_to_sqs(message_dict: dict):
    """
    Send JSON message to SQS. Lambda will be triggered by this queue.
    """
    conf = get_aws_config()
    queue_url = conf['SQS_QUEUE_URL']

    sqs = get_sqs_client()
    sqs.send_message(
        QueueUrl=queue_url,
        MessageBody=json.dumps(message_dict)
    )
