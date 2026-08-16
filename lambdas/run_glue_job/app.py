import os
import time

from common.dynamodb_service import DynamoDBService
from common.glue_service import GlueService
from common.utils import (
    decode_s3_key,
    get_file_extension,
    get_s3_records_from_sns_event,
)


SUPPORTED_FILE_TYPES = {
    "txt",
    "csv",
    "json",
}

MAX_DYNAMODB_READ_ATTEMPTS = 15
DYNAMODB_RETRY_DELAY_SECONDS = 2


def lambda_handler(event, context):

    table_name = os.environ["TABLE_NAME"]
    crawler_bucket = os.environ["CRAWLER_BUCKET"]

    enable_glue_execution = os.environ.get(
        "ENABLE_GLUE_EXECUTION",
        "true",
    ).lower() == "true"

    dynamodb_service = DynamoDBService(
        table_name
    )

    glue_service = GlueService()

    s3_records = get_s3_records_from_sns_event(
        event
    )

    if not s3_records:
        raise ValueError(
            "No S3 records found in the SNS event."
        )

    processed_files = []

    for record in s3_records:

        bucket_name = (
            record["s3"]["bucket"]["name"]
        )

        encoded_key = (
            record["s3"]["object"]["key"]
        )

        object_key = decode_s3_key(
            encoded_key
        )

        version_id = (
            record["s3"]["object"].get(
                "versionId"
            )
        )

        file_type = get_file_extension(
            object_key
        )

        if file_type not in SUPPORTED_FILE_TYPES:
            raise ValueError(
                f"Unsupported file type for "
                f"{object_key}: "
                f"{file_type or 'missing'}"
            )

        object_details = None

        for attempt in range(
            1,
            MAX_DYNAMODB_READ_ATTEMPTS + 1,
        ):

            object_details = (
                dynamodb_service
                .get_s3_object_configuration(
                    object_key,
                    version_id,
                )
            )
            print(
                f"DynamoDB lookup result: {object_details}"
            )

            if object_details:
                break

            print(
                f"S3 configuration not found for "
                f"{object_key}, "
                f"version={version_id}. "
                f"Attempt "
                f"{attempt}/"
                f"{MAX_DYNAMODB_READ_ATTEMPTS}."
            )

            if attempt < MAX_DYNAMODB_READ_ATTEMPTS:
                time.sleep(
                    DYNAMODB_RETRY_DELAY_SECONDS
                )

        if not object_details:
            raise RuntimeError(
                f"S3 configuration was not found "
                f"in DynamoDB for "
                f"{object_key}, "
                f"version={version_id} "
                f"after "
                f"{MAX_DYNAMODB_READ_ATTEMPTS} "
                f"attempts."
            )

        file_size = object_details[
            "file_size"
        ]

        job_name = select_glue_job(
            file_type,
            file_size,
        )

        if not enable_glue_execution:

            print(
                f"Dry run: selected Glue job "
                f"{job_name} for {object_key}. "
                f"Glue execution skipped."
            )

            processed_files.append({
                "object_key": object_key,
                "version_id": version_id,
                "file_type": file_type,
                "file_size": file_size,
                "selected_job": job_name,
                "glue_started": False,
            })

            continue

        job_run_id = (
            glue_service.start_glue_job(
                job_name,
                bucket_name,
                object_key,
                crawler_bucket,
                version_id,
            )
        )

        processed_files.append({
            "object_key": object_key,
            "version_id": version_id,
            "file_type": file_type,
            "file_size": file_size,
            "selected_job": job_name,
            "job_run_id": job_run_id,
            "glue_started": True,
        })

    return {
        "statusCode": 200,
        "message": (
            "Glue job selection completed."
        ),
        "processed_files": processed_files,
    }


def select_glue_job(
    file_type,
    file_size,
):

    if file_type == "txt":

        if file_size <= 5 * 1024:
            return "TextSmallGlueJob"

        if file_size <= 10 * 1024:
            return "TextMediumGlueJob"

        return "TextLargeGlueJob"

    if file_type == "csv":

        if file_size <= 5 * 1024:
            return "CSVSmallGlueJob"

        if file_size <= 10 * 1024:
            return "CSVMediumGlueJob"

        return "CSVLargeGlueJob"

    if file_type == "json":

        if file_size <= 5 * 1024:
            return "JSONSmallGlueJob"

        if file_size <= 10 * 1024:
            return "JSONMediumGlueJob"

        return "JSONLargeGlueJob"

    raise ValueError(
        f"Unsupported file type: {file_type}"
    )