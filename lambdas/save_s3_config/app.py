import os

from common.dynamodb_service import DynamoDBService
from common.s3_service import S3Service
from common.utils import (
    decode_s3_key,
    get_s3_records_from_sns_event,
)


def lambda_handler(event, context):

    table_name = os.environ["TABLE_NAME"]

    dynamodb_service = DynamoDBService(
        table_name
    )

    s3_service = S3Service()

    s3_records = get_s3_records_from_sns_event(
        event
    )

    if not s3_records:
        raise ValueError(
            "No S3 records found in the SNS event."
        )

    saved_files = []

    for record in s3_records:

        bucket_name = (
            record["s3"]["bucket"]["name"]
        )

        encoded_object_key = (
            record["s3"]["object"]["key"]
        )

        object_key = decode_s3_key(
            encoded_object_key
        )

        version_id = (
            record["s3"]["object"].get(
                "versionId"
            )
        )

        object_details = (
            s3_service.get_object_details(
                bucket_name,
                object_key,
                version_id,
            )
        )

        dynamodb_service.save_s3_object_configuration(
            object_details
        )

        saved_files.append(
            object_details
        )

        print(
            f"Saved S3 configuration for "
            f"{object_key}, "
            f"version={object_details['version_id']}"
        )

    return {
        "statusCode": 200,
        "message": (
            "S3 object configurations "
            "saved successfully."
        ),
        "saved_files": saved_files,
    }