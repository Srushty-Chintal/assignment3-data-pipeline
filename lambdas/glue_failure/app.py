import os

from common.sns_service import SNSService


def lambda_handler(event, context):

    sns_service = SNSService()

    topic_arn = os.environ["OUTPUT_TOPIC_ARN"]

    job_name = event["detail"]["jobName"]

    job_run_id = event["detail"]["jobRunId"]

    job_state = event["detail"]["state"]

    error_message = event["detail"].get(
        "message",
        "No error message."
    )

    message = f"""
Glue Job Failed

Job Name : {job_name}

Job Run ID : {job_run_id}

Status : {job_state}

Reason : {error_message}
"""

    sns_service.send_notification(
        topic_arn,
        "Glue Job Failure",
        message
    )

    return {
        "statusCode": 200,
        "message": "Failure notification sent."
    }