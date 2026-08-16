import boto3


class S3Service:
    """
    Contains S3-related operations.
    """

    def __init__(self):
        self.s3_client = boto3.client("s3")

    def get_object_processing_details(
        self,
        bucket_name,
        object_key,
        version_id=None,
    ):
        """
        Returns only the object details required
        for selecting a Glue job.
        """

        parameters = {
            "Bucket": bucket_name,
            "Key": object_key,
        }

        if version_id:
            parameters["VersionId"] = version_id

        response = self.s3_client.head_object(
            **parameters
        )

        return {
            "bucket_name": bucket_name,
            "object_key": object_key,
            "version_id": (
                response.get("VersionId")
                or version_id
                or "null"
            ),
            "content_type": response.get(
                "ContentType",
                "unknown",
            ),
            "file_size": response.get(
                "ContentLength",
                0,
            ),
        }

    def get_object_details(
        self,
        bucket_name,
        object_key,
        version_id=None,
    ):
        """
        Gets the full details of one S3 object,
        including metadata and tags.
        """

        head_parameters = {
            "Bucket": bucket_name,
            "Key": object_key,
        }

        tag_parameters = {
            "Bucket": bucket_name,
            "Key": object_key,
        }

        if version_id:
            head_parameters["VersionId"] = version_id
            tag_parameters["VersionId"] = version_id

        head_response = self.s3_client.head_object(
            **head_parameters
        )

        tag_response = self.s3_client.get_object_tagging(
            **tag_parameters
        )

        tags = {}

        for tag in tag_response.get("TagSet", []):
            tags[tag["Key"]] = tag["Value"]

        actual_version_id = (
            head_response.get("VersionId")
            or version_id
            or "null"
        )

        return {
            "bucket_name": bucket_name,
            "object_key": object_key,
            "version_id": actual_version_id,
            "content_type": head_response.get(
                "ContentType",
                "unknown",
            ),
            "file_size": head_response.get(
                "ContentLength",
                0,
            ),
            "last_modified_date": head_response[
                "LastModified"
            ].isoformat(),
            "metadata": head_response.get(
                "Metadata",
                {},
            ),
            "tags": tags,
        }