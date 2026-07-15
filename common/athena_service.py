import time
import boto3


class AthenaService:

    def __init__(self):
        self.athena_client = boto3.client("athena")

    def start_query(
        self,
        query,
        database_name,
        output_location
    ):

        response = self.athena_client.start_query_execution(
            QueryString=query,
            QueryExecutionContext={
                "Database": database_name
            },
            ResultConfiguration={
                "OutputLocation": output_location
            }
        )

        return response["QueryExecutionId"]

    def wait_for_query(self, query_execution_id):

        while True:

            response = self.athena_client.get_query_execution(
                QueryExecutionId=query_execution_id
            )

            status = response["QueryExecution"]["Status"]["State"]

            if status == "SUCCEEDED":
                return

            elif status == "FAILED":
                raise Exception("Athena query failed.")

            elif status == "CANCELLED":
                raise Exception("Athena query cancelled.")

            time.sleep(5)