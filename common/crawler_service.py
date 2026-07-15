import time
import boto3

from common.constants import (
    CRAWLER_WAIT_SECONDS,
    CRAWLER_MAX_ATTEMPTS
)


class CrawlerService:

    def __init__(self):
        self.glue_client = boto3.client("glue")

    def start_crawler(self, crawler_name):

        self.glue_client.start_crawler(
            Name=crawler_name
        )

    def wait_for_crawler(self, crawler_name):

        attempts = 0

        while attempts < CRAWLER_MAX_ATTEMPTS:

            response = self.glue_client.get_crawler(
                Name=crawler_name
            )

            crawler_state = response["Crawler"]["State"]

            if crawler_state == "READY":
                return

            time.sleep(CRAWLER_WAIT_SECONDS)

            attempts += 1

        raise Exception("Crawler timeout.")