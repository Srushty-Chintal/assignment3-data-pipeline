import json
from urllib.parse import unquote_plus


def decode_s3_key(encoded_key):
    """
    S3 event notifications encode object keys.

    Example:
    input%2Fstudent+data.csv

    Output:
    input/student data.csv
    """

    return unquote_plus(encoded_key)


def get_s3_records_from_sns_event(event):
    """
    SNS receives the original S3 event as a JSON string.

    This function:
    1. Reads the SNS records.
    2. Extracts the SNS message.
    3. Converts the message from JSON string to dictionary.
    4. Returns the original S3 records.
    """

    s3_records = []

    for sns_record in event.get("Records", []):
        sns_message = sns_record["Sns"]["Message"]

        s3_event = json.loads(sns_message)

        for s3_record in s3_event.get("Records", []):
            s3_records.append(s3_record)

    return s3_records


def get_file_extension(object_key):
    """
    Returns the file extension from an S3 object key.

    Example:
    input/student.csv -> csv
    """

    if "." not in object_key:
        return ""

    return object_key.rsplit(".", 1)[1].lower()