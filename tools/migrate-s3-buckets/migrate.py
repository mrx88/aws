#!/usr/bin/env python
import boto3
from botocore.exceptions import ClientError
import psycopg2
import logging
import click
import sys


def get_legacy_images(dbconn):
    """Function to get the legacy images from the database.
    We assume database is source of truth and get images that
    contain legacy /image/* path.

    Args:
        dbconn (string): Postgres Database Connection String

    Returns:
        list: Returns a list of legacy images from PostgresDB
    """
    try:
        conn = psycopg2.connect(dbconn)
        cur = conn.cursor()
        cur.execute("SELECT path FROM avatars WHERE path LIKE '%image/%'")
        rows = cur.fetchall()
        legacy_image_paths = []
        for row in rows:
            # print(row[0])
            legacy_image_paths.append(row[0])

        if legacy_image_paths:
            logging.info(f"Legacy images found in DB: {legacy_image_paths}")
        else:
            logging.info("No rows with legacy image/ path found in database")
            sys.exit(0)
        return legacy_image_paths

    except Exception as e:
        logging.error(e)
    return conn


def upload_file_s3(old_file, old_bucket, modern_bucket):
    """Function to modify the image file path prefix
    and upload the file to the new bucket.

    Args:
        old_file (string): Legacy image file path
        old_bucket (string): Legacy S3 bucket name
        modern_bucket (string): New S3 bucket name
    """
    try:
        s3_resource = boto3.resource("s3")
        copy_source = {
            "Bucket": old_bucket,
            "Key": old_file
        }
        # Before uploading the file we need to rename it to "modern" format
        # We do this by replacing the "image/" prefix from the file name
        modern_file = old_file.replace("image/", "avatar/")
        s3_resource.meta.client.copy(copy_source, modern_bucket, modern_file)
    except ClientError as e:
        logging.error(e)
    return s3_resource


def update_db_path(dbconn, old_file):
    """Updates the legacy path in the database to the modern path
    for specific row.

    Args:
        dbconn (string): Database connection string
        old_file (string): Old file name with legacy path

    """
    try:
        conn = psycopg2.connect(dbconn)
        cur = conn.cursor()
        modern_file = old_file.replace("image/", "avatar/")
        cur.execute(f"UPDATE avatars SET path = REPLACE(path, '{old_file}', '{modern_file}')")
        conn.commit()
    except Exception as e:
        logging.error(e)
    return conn


def migrate_images_to_modern(dbconn, old_bucket, modern_bucket,
                             delete_old_images):
    """Migrates the leacy image S3 objects to the new S3 bucket
    and updates the database to reflect the new path.

    Args:
        dbconn (string): Database connection string

    Returns:
        _type_: _description_
    """
    try:
        s3_resource = boto3.resource("s3")
        legacy_bucket = s3_resource.Bucket(old_bucket)
        legacy_images_db = get_legacy_images(dbconn)

        # Iterate over the legacy images and upload them to the modern bucket
        legacy_s3_image_path = []
        for obj in legacy_bucket.objects.all():
            legacy_s3_image_path.append(obj.key)
        for image in legacy_images_db:
            if image in legacy_s3_image_path:
                logging.info(
                    f"Image {image} found in legacy bucket {old_bucket}")
                logging.info(f"Migrating {image} to {modern_bucket}")
                upload_file_s3(image, old_bucket, modern_bucket)

                logging.info(f"Updating path for {image} in database")
                update_db_path(dbconn, image)

                if delete_old_images:
                    logging.info(f"Deleting {image} from {old_bucket}")
                    s3_resource.Object(old_bucket, image).delete()
                else:
                    logging.info(f"Not deleting {image} from {old_bucket}")
            else:
                logging.warning(
                    f"Image {image} not found in legacy bucket {old_bucket}")
                # NOTE: Consider adding additional check here
                # I.e if old image path is present in DB but not in S3
    except ClientError as e:
        logging.error(e)
    return s3_resource


@click.command()
@click.option('--dbconn', help='Database connection string', required=True)
@click.option('--old_bucket', default="legacy-s3",
              help='Old S3 bucket name')
@click.option('--modern_bucket', default="production-s3",
              help='New S3 bucket name')
@click.option('--delete_old_images', default=False,
              help='If True delete files from old S3 bucket')
def main(dbconn, old_bucket, modern_bucket, delete_old_images):
    """Tool to migrate legacy image objects from old S3 bucket
     to new S3 bucket.

    Args:
        dbconn (string): Database connection string
    """
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s')

    try:
        # Get list of legacy images from the database
        get_legacy_images(dbconn)

        # Compare DB and S3 legacy images and migrate avatars to new bucket
        migrate_images_to_modern(
            dbconn, old_bucket, modern_bucket, delete_old_images)

    except Exception as e:
        logging.error(e)


if __name__ == '__main__':
    main()
