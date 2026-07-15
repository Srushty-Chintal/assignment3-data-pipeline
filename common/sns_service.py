import boto3


class SNSService:

    def __init__(self):
        self.sns_client = boto3.client("sns")

    def send_notification(
        self,
        topic_arn,
        subject,
        message
    ):

        response = self.sns_client.publish(
            TopicArn=topic_arn,
            Subject=subject,
            Message=message
        )

        return response["MessageId"]