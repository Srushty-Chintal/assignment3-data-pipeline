# File types supported by the assignment
FILE_TYPE_TEXT = "txt"
FILE_TYPE_CSV = "csv"
FILE_TYPE_JSON = "json"

# File-size limits in bytes
FIVE_KB = 5 * 1024
TEN_KB = 10 * 1024

# Processing statuses stored in DynamoDB
STATUS_RECEIVED = "RECEIVED"
STATUS_GLUE_STARTED = "GLUE_JOB_STARTED"
STATUS_GLUE_SUCCEEDED = "GLUE_JOB_SUCCEEDED"
STATUS_GLUE_FAILED = "GLUE_JOB_FAILED"

# Crawler waiting configuration
CRAWLER_WAIT_SECONDS = 10
CRAWLER_MAX_ATTEMPTS = 30