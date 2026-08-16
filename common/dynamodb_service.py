import boto3
from boto3.dynamodb.conditions import Key


class DynamoDBService:

    def __init__(self, table_name):
        dynamodb = boto3.resource("dynamodb")
        self.table = dynamodb.Table(table_name)

    def save_job_configuration(
        self,
        file_type,
        min_size,
        max_size,
        glue_job,
    ):
        self.table.put_item(
            Item={
                "file_type": file_type,
                "min_size": min_size,
                "max_size": max_size,
                "glue_job": glue_job,
            }
        )

        
    def save_s3_object_configuration(
    self,
    object_details,
    ):
        self.table.put_item(
            Item={
                "object_key": object_details["object_key"],
                "version_id": object_details["version_id"],
                "content_type": object_details["content_type"],
                "file_size": object_details["file_size"],
                "last_modified_date": object_details[
                    "last_modified_date"
                ],
                "metadata": object_details["metadata"],
                "tags": object_details["tags"],
            }
        )

    def get_s3_object_configuration(
    self,
    object_key,
    version_id,
    ):
        response = self.table.get_item(
            Key={
                "object_key": object_key,
                "version_id": version_id,
            },
            ConsistentRead=True,
        )

        return response.get("Item")