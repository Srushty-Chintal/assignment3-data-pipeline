import os
import time

from common.constants import STATUS_GLUE_STARTED
from common.dynamodb_service import DynamoDBService
from common.glue_service import GlueService
from common.utils import (
    decode_s3_key,
    get_file_extension,
    get_s3_records_from_sns_event
)


def lambda_handler(event, context):

    table_name = os.environ["TABLE_NAME"]
    crawler_bucket = os.environ["CRAWLER_BUCKET"]

    enable_glue_execution = os.environ.get(
        "ENABLE_GLUE_EXECUTION",
        "false"
    ).lower() == "true"

    dynamodb_service = DynamoDBService(table_name)
    glue_service = GlueService()

    s3_records = get_s3_records_from_sns_event(event)

    processed_files = []

    for record in s3_records:

        bucket_name = record["s3"]["bucket"]["name"]

        encoded_key = record["s3"]["object"]["key"]

        object_key = decode_s3_key(encoded_key)

        version_id = record["s3"]["object"].get(
            "versionId"
        )

        file_config = None

        for attempt in range(5):

            file_config = dynamodb_service.get_file_config(
                object_key,
                version_id
            )

            if file_config:
                break

            time.sleep(2)

        if not file_config:
            raise Exception(
                f"Configuration not found in DynamoDB for "
                f"{object_key}, version {version_id}"
            )

        file_type = get_file_extension(object_key)

        file_size = file_config["file_size"]

        job_name = glue_service.get_glue_job_name(
            file_type,
            file_size
        )

        if not enable_glue_execution:

            print(
                f"Dry run: selected Glue job {job_name} "
                f"for {object_key}. Glue execution skipped."
            )

            processed_files.append({
                "object_key": object_key,
                "selected_job": job_name,
                "glue_started": False
            })

            continue

        job_run_id = glue_service.start_glue_job(
            job_name,
            bucket_name,
            object_key,
            crawler_bucket,
            version_id
        )

        dynamodb_service.update_status(
            object_key,
            version_id,
            STATUS_GLUE_STARTED
        )

        dynamodb_service.update_glue_job_details(
            object_key,
            version_id,
            job_name,
            job_run_id
        )

        processed_files.append({
            "object_key": object_key,
            "selected_job": job_name,
            "job_run_id": job_run_id,
            "glue_started": True
        })

    return {
        "statusCode": 200,
        "message": "Glue job selection completed.",
        "processed_files": processed_files
    }