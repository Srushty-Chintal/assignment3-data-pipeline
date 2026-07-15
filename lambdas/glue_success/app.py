import os

from common.athena_service import AthenaService
from common.crawler_service import CrawlerService


def lambda_handler(event, context):

    job_name = event["detail"]["jobName"]

    database_name = os.environ["DATABASE_NAME"]
    athena_output = os.environ["ATHENA_OUTPUT_LOCATION"]

    crawler_service = CrawlerService()
    athena_service = AthenaService()

    if job_name.startswith("Text"):
        crawler_name = "TextFilesCrawler"
        table_name = "text_files"

    elif job_name.startswith("CSV"):
        crawler_name = "CSVFilesCrawler"
        table_name = "csv_files"

    elif job_name.startswith("JSON"):
        crawler_name = "JSONFilesCrawler"
        table_name = "json_files"

    else:
        raise Exception(
            f"Unknown Glue job: {job_name}"
        )

    crawler_service.start_crawler(
        crawler_name
    )

    crawler_service.wait_for_crawler(
        crawler_name
    )

    query = (
        f"CREATE OR REPLACE VIEW "
        f"{table_name}_view AS "
        f"SELECT * FROM {table_name}"
    )

    query_execution_id = (
        athena_service.start_query(
            query,
            database_name,
            athena_output
        )
    )

    athena_service.wait_for_query(
        query_execution_id
    )

    return {
        "statusCode": 200,
        "message": (
            "Crawler completed and Athena "
            "view created successfully."
        )
    }