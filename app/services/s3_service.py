import boto3
from botocore.exceptions import ClientError
from botocore.config import Config
from app.core.config import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION, AWS_S3_BUCKET


def _get_client():
    return boto3.client(
        "s3",
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION,
        config=Config(signature_version="s3v4"),
    )


def upload_file_to_s3(file_obj, s3_key: str, content_type: str) -> str:
    """Upload a file-like object to S3 and return the S3 key."""
    client = _get_client()
    client.upload_fileobj(
        file_obj,
        AWS_S3_BUCKET,
        s3_key,
        ExtraArgs={"ContentType": content_type},
    )
    return s3_key


def generate_presigned_url(s3_key: str, expires_in: int = 3600) -> str:
    """Generate a presigned download URL for an S3 object."""
    client = _get_client()
    url = client.generate_presigned_url(
        "get_object",
        Params={"Bucket": AWS_S3_BUCKET, "Key": s3_key},
        ExpiresIn=expires_in,
    )
    return url


def delete_file_from_s3(s3_key: str) -> None:
    """Delete an object from S3."""
    client = _get_client()
    client.delete_object(Bucket=AWS_S3_BUCKET, Key=s3_key)


def read_file_from_s3(s3_key: str, max_bytes: int = 500_000) -> str:
    """Download a text file from S3 and return its contents as a string.

    Args:
        s3_key: The S3 object key.
        max_bytes: Maximum number of bytes to read (default 500 KB) to avoid
                   sending enormous documents to the LLM context.

    Returns:
        The decoded text content of the file.
    """
    client = _get_client()
    response = client.get_object(Bucket=AWS_S3_BUCKET, Key=s3_key)
    raw = response["Body"].read(max_bytes)
    return raw.decode("utf-8", errors="replace")


def list_files_in_s3(prefix: str = "") -> list[dict]:
    """List objects in the S3 bucket, optionally filtered by prefix."""
    client = _get_client()
    response = client.list_objects_v2(Bucket=AWS_S3_BUCKET, Prefix=prefix)
    objects = response.get("Contents", [])
    return [
        {
            "key": obj["Key"],
            "size": obj["Size"],
            "last_modified": obj["LastModified"].isoformat(),
        }
        for obj in objects
    ]
