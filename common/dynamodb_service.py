import boto3

from common.constants import STATUS_RECEIVED


class DynamoDBService:
    """
    Contains DynamoDB operations for file configuration.
    """

    def __init__(self, table_name):
        dynamodb = boto3.resource("dynamodb")
        self.table = dynamodb.Table(table_name)

    def save_file_config(self, file_config):
        """
        Saves an S3 object's configuration to DynamoDB.
        """

        item = file_config.copy()

        item["processing_status"] = STATUS_RECEIVED

        self.table.put_item(
            Item=item
        )

        return item
    def get_file_config(self, object_key, version_id):
        """
        Reads one file configuration using the DynamoDB keys.
        """

        response = self.table.get_item(
            Key={
                "object_key": object_key,
                "version_id": version_id
            }
        )

        return response.get("Item")

    def update_status(
        self,
        object_key,
        version_id,
        new_status
    ):
        """
        Updates the file-processing status.
        """

        self.table.update_item(
            Key={
                "object_key": object_key,
                "version_id": version_id
            },
            UpdateExpression=(
                "SET processing_status = :status"
            ),
            ExpressionAttributeValues={
                ":status": new_status
            }
        )

    def update_glue_job_details(
        self,
        object_key,
        version_id,
        job_name,
        job_run_id
    ):
        """
        Saves the selected Glue job name and run ID.
        """

        self.table.update_item(
            Key={
                "object_key": object_key,
                "version_id": version_id
            },
            UpdateExpression=(
                "SET glue_job_name = :job_name, "
                "glue_job_run_id = :job_run_id"
            ),
            ExpressionAttributeValues={
                ":job_name": job_name,
                ":job_run_id": job_run_id
            }
        )