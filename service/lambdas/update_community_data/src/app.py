import base64

from botocore.exceptions import ClientError as BotoClientError

from topshelfsoftware_util.aws import create_boto3_client
from topshelfsoftware_util.common import fmt_json
from topshelfsoftware_util.log import get_logger
# ----------------------------------------------------------------------------#
#                               --- Globals ---                               #
# ----------------------------------------------------------------------------#
from .__init__ import (
    MODULE_NAME, COMMUNITY_DATA_BUCKET_NAME, COMMUNITY_DATA_OBJECT_NAME
)
s3_client = create_boto3_client("s3")

# ----------------------------------------------------------------------------#
#                               --- Logging ---                               #
# ----------------------------------------------------------------------------#
logger = get_logger(f"{MODULE_NAME}.{__name__}")

# ----------------------------------------------------------------------------#
#                                 --- MAIN ---                                #
# ----------------------------------------------------------------------------#
def lambda_handler(event, context):
    logger.info(f"event: {fmt_json(event)}")
    
    xlsx_blob_encoded: str = event["xlsx_blob_encoded"]
    logger.info(f"encoded: {xlsx_blob_encoded}")
    
    # decode the base64 encoded blob and read into memory
    xlsx_blob = base64.b64decode(xlsx_blob_encoded)
    logger.info(f"decoded: {xlsx_blob}")

    try:
        logger.info(f"uploading xlsx bytes to s3 bucket {COMMUNITY_DATA_BUCKET_NAME}")
        resp = s3_client.put_object(Body=xlsx_blob,
                                    Bucket=COMMUNITY_DATA_BUCKET_NAME,
                                    Key=COMMUNITY_DATA_OBJECT_NAME)
        logger.info("successfully uploaded")
    except BotoClientError as e:
        logger.error(e)
        raise e
    version_id = resp["VersionId"]
    logger.info(f"s3 obj version id: {version_id}")
    
    return {
        "s3_bucket": COMMUNITY_DATA_BUCKET_NAME,
        "s3_object": COMMUNITY_DATA_OBJECT_NAME,
        "s3_version_id": version_id
    }
