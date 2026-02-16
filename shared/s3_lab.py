import sys
import os
from typing import Optional, List, Dict, Any

try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False
    # Define dummy exceptions for type safety when missing
    class ClientError(Exception): pass
    class NoCredentialsError(Exception): pass

try:
    from rich.console import Console
    from rich.table import Table
    HAS_RICH = True
except ImportError:
    HAS_RICH = False

class S3LabManager:
    """
    Manages interactions with S3-compatible object storage using boto3.
    """
    def __init__(self, endpoint_url: Optional[str] = None, profile_name: Optional[str] = None, region_name: Optional[str] = None):
        if not HAS_BOTO3:
            print("❌ Error: 'boto3' library not found. Please install it with 'pip install boto3'.", file=sys.stderr)
            sys.exit(1)

        self.session = boto3.Session(profile_name=profile_name, region_name=region_name)
        self.s3_client = self.session.client("s3", endpoint_url=endpoint_url)
        self.s3_resource = self.session.resource("s3", endpoint_url=endpoint_url)
        if HAS_RICH:
            self.console = Console()
        else:
            self.console = None

    def list_buckets(self):
        """Lists all S3 buckets."""
        try:
            response = self.s3_client.list_buckets()
            buckets = response.get("Buckets", [])

            if not buckets:
                print("No buckets found.")
                return

            if HAS_RICH:
                table = Table(title="S3 Buckets")
                table.add_column("Name", style="cyan")
                table.add_column("Creation Date", style="green")

                for bucket in buckets:
                    table.add_row(bucket["Name"], str(bucket["CreationDate"]))
                self.console.print(table)
            else:
                print(f"{'Name':<30} | {'Creation Date'}")
                print("-" * 50)
                for bucket in buckets:
                    print(f"{bucket['Name']:<30} | {bucket['CreationDate']}")

        except (ClientError, NoCredentialsError) as e:
            print(f"Error listing buckets: {e}", file=sys.stderr)

    def list_objects(self, bucket_name: str, prefix: str = ""):
        """Lists objects in a specific bucket."""
        try:
            paginator = self.s3_client.get_paginator("list_objects_v2")
            page_iterator = paginator.paginate(Bucket=bucket_name, Prefix=prefix)

            found_objects = False

            if HAS_RICH:
                table = Table(title=f"Objects in s3://{bucket_name}/{prefix}")
                table.add_column("Key", style="cyan")
                table.add_column("Size", style="green")
                table.add_column("Last Modified", style="blue")

            header_printed = False
            for page in page_iterator:
                if "Contents" in page:
                    found_objects = True
                    for obj in page["Contents"]:
                        if HAS_RICH:
                            table.add_row(obj["Key"], str(obj["Size"]), str(obj["LastModified"]))
                        else:
                            if not header_printed: # Print header once
                                print(f"{'Key':<50} | {'Size':<10} | {'Last Modified'}")
                                print("-" * 90)
                                header_printed = True
                            print(f"{obj['Key']:<50} | {obj['Size']:<10} | {obj['LastModified']}")

            if HAS_RICH and found_objects:
                self.console.print(table)
            elif not found_objects:
                print(f"No objects found in s3://{bucket_name}/{prefix}")

        except (ClientError, NoCredentialsError) as e:
            print(f"Error listing objects in {bucket_name}: {e}", file=sys.stderr)

    def create_bucket(self, bucket_name: str, region: Optional[str] = None):
        """Creates a new S3 bucket."""
        try:
            kwargs = {"Bucket": bucket_name}
            if region and region != "us-east-1":
                kwargs["CreateBucketConfiguration"] = {"LocationConstraint": region}

            self.s3_client.create_bucket(**kwargs)
            print(f"✅ Bucket '{bucket_name}' created successfully.")
        except (ClientError, NoCredentialsError) as e:
            print(f"❌ Error creating bucket '{bucket_name}': {e}", file=sys.stderr)

    def delete_bucket(self, bucket_name: str):
        """Deletes an S3 bucket."""
        try:
            self.s3_client.delete_bucket(Bucket=bucket_name)
            print(f"✅ Bucket '{bucket_name}' deleted successfully.")
        except (ClientError, NoCredentialsError) as e:
            print(f"❌ Error deleting bucket '{bucket_name}': {e}", file=sys.stderr)

    def upload_file(self, bucket_name: str, key: str, local_path: str):
        """Uploads a local file to S3."""
        if not os.path.exists(local_path):
             print(f"Error: Local file '{local_path}' not found.", file=sys.stderr)
             return

        try:
            print(f"Uploading {local_path} to s3://{bucket_name}/{key} ...")
            self.s3_client.upload_file(local_path, bucket_name, key)
            print("✅ Upload successful.")
        except (ClientError, NoCredentialsError) as e:
            print(f"❌ Error uploading file: {e}", file=sys.stderr)

    def download_file(self, bucket_name: str, key: str, local_path: str):
        """Downloads a file from S3."""
        try:
            print(f"Downloading s3://{bucket_name}/{key} to {local_path} ...")
            self.s3_client.download_file(bucket_name, key, local_path)
            print("✅ Download successful.")
        except (ClientError, NoCredentialsError) as e:
            print(f"❌ Error downloading file: {e}", file=sys.stderr)

    def delete_object(self, bucket_name: str, key: str):
        """Deletes an object from S3."""
        try:
            self.s3_client.delete_object(Bucket=bucket_name, Key=key)
            print(f"✅ Object s3://{bucket_name}/{key} deleted.")
        except (ClientError, NoCredentialsError) as e:
            print(f"❌ Error deleting object: {e}", file=sys.stderr)

    def presign_url(self, bucket_name: str, key: str, expiration: int = 3600):
        """Generates a presigned URL for an object."""
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': bucket_name, 'Key': key},
                ExpiresIn=expiration
            )
            print(f"✅ Presigned URL (valid for {expiration}s):")
            print(url)
        except (ClientError, NoCredentialsError) as e:
            print(f"❌ Error generating presigned URL: {e}", file=sys.stderr)

def run_s3_lab_logic(args):
    """
    CLI Entry point for S3 Lab.
    """
    manager = S3LabManager(
        endpoint_url=args.endpoint_url,
        profile_name=args.profile,
        region_name=args.region
    )

    if args.action == "ls":
        if args.bucket:
            manager.list_objects(args.bucket, args.prefix or "")
        else:
            manager.list_buckets()

    elif args.action == "mb":
        if not args.bucket:
            print("Error: --bucket required for make bucket.", file=sys.stderr)
            sys.exit(1)
        manager.create_bucket(args.bucket, args.region)

    elif args.action == "rb":
        if not args.bucket:
            print("Error: --bucket required for remove bucket.", file=sys.stderr)
            sys.exit(1)
        manager.delete_bucket(args.bucket)

    elif args.action == "cp":
        if not args.src or not args.dest:
            print("Error: --src and --dest required for copy.", file=sys.stderr)
            sys.exit(1)

        # Determine direction based on s3:// prefix
        is_src_s3 = args.src.startswith("s3://")
        is_dest_s3 = args.dest.startswith("s3://")

        if is_src_s3 and not is_dest_s3:
            # Download
            bucket, key = args.src[5:].split("/", 1)
            manager.download_file(bucket, key, args.dest)
        elif not is_src_s3 and is_dest_s3:
            # Upload
            bucket, key = args.dest[5:].split("/", 1)
            manager.upload_file(bucket, key, args.src)
        else:
            print("Error: Currently only supports local->s3 or s3->local copy.", file=sys.stderr)
            sys.exit(1)

    elif args.action == "rm":
        if not args.bucket or not args.key:
            print("Error: --bucket and --key required for remove object.", file=sys.stderr)
            sys.exit(1)
        manager.delete_object(args.bucket, args.key)

    elif args.action == "presign":
        if not args.bucket or not args.key:
             print("Error: --bucket and --key required for presign.", file=sys.stderr)
             sys.exit(1)
        manager.presign_url(args.bucket, args.key, args.expires_in)

    else:
        print(f"Unknown action: {args.action}", file=sys.stderr)
        sys.exit(1)
