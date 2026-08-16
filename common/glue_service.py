import boto3


class GlueService:

    def __init__(self):
        self.glue_client = boto3.client("glue")

    def start_glue_job(
        self,
        job_name,
        source_bucket,
        object_key,
        output_bucket,
        version_id,
    ):

        arguments = {
            "--SOURCE_BUCKET": source_bucket,
            "--OBJECT_KEY": object_key,
            "--OUTPUT_BUCKET": output_bucket,
        }

        if version_id:
            arguments["--VERSION_ID"] = version_id

        response = self.glue_client.start_job_run(
            JobName=job_name,
            Arguments=arguments,
        )

        return response["JobRunId"]