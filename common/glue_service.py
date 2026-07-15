import boto3

from common.constants import (
    FILE_TYPE_TEXT,
    FILE_TYPE_CSV,
    FILE_TYPE_JSON,
    FIVE_KB,
    TEN_KB
)


class GlueService:

    def __init__(self):
        self.glue_client = boto3.client("glue")

    def get_size_category(self, file_size):

        if file_size <= FIVE_KB:
            return "small"

        elif file_size <= TEN_KB:
            return "medium"

        else:
            return "large"

    def get_glue_job_name(
        self,
        file_type,
        file_size
    ):

        size = self.get_size_category(file_size)

        if file_type == FILE_TYPE_TEXT:
            return f"Text{size.capitalize()}GlueJob"

        elif file_type == FILE_TYPE_CSV:
            return f"CSV{size.capitalize()}GlueJob"

        elif file_type == FILE_TYPE_JSON:
            return f"JSON{size.capitalize()}GlueJob"

        else:
            raise Exception(
                "Unsupported file type."
            )

    def start_glue_job(
        self,
        job_name,
        source_bucket,
        object_key,
        output_bucket,
        version_id
    ):

        response = self.glue_client.start_job_run(
            JobName=job_name,
            Arguments={
                "--SOURCE_BUCKET": source_bucket,
                "--OBJECT_KEY": object_key,
                "--OUTPUT_BUCKET": output_bucket,
                "--VERSION_ID": version_id
            }
        )

        return response["JobRunId"]