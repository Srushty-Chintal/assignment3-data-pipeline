import os

from common.utils import (
    decode_s3_key,
    get_s3_records_from_sns_event
)

from common.s3_service import S3Service
from common.dynamodb_service import DynamoDBService


def lambda_handler(event, context):

    table_name = os.environ["TABLE_NAME"]

    s3_service = S3Service()

    dynamodb_service = DynamoDBService(table_name)

    s3_records = get_s3_records_from_sns_event(event)

    for record in s3_records:

        bucket_name = record["s3"]["bucket"]["name"]

        encoded_object_key = record["s3"]["object"]["key"]

        object_key = decode_s3_key(
            encoded_object_key
        )

        version_id = record["s3"]["object"].get(
            "versionId"
        )

        file_details = s3_service.get_object_details(
            bucket_name,
            object_key,
            version_id
        )

        dynamodb_service.save_file_config(
            file_details
        )

    return {
        "statusCode": 200,
        "message": "File configuration saved successfully."
    }