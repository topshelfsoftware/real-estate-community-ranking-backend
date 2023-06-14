import boto3
from botocore.exceptions import ClientError as BotoClientError
import pandas as pd

from topshelfsoftware_util.common import fmt_json
from topshelfsoftware_util.io import cdtmp
from topshelfsoftware_util.log import add_console_handler, get_logger

from communities import (
    compile_top_communities, filter_communities, rank_communities,
    read_excel_sheet, score_communities
)
# ----------------------------------------------------------------------------#
#                               --- Globals ---                               #
# ----------------------------------------------------------------------------#
from __init__ import MODULE_NAME
s3_client = boto3.client("s3")

# ----------------------------------------------------------------------------#
#                               --- Logging ---                               #
# ----------------------------------------------------------------------------#
logger = get_logger(f"{MODULE_NAME}.{__name__}")
add_console_handler(logger)

# ----------------------------------------------------------------------------#
#                                 --- MAIN ---                                #
# ----------------------------------------------------------------------------#
def lambda_handler(event, context):
    logger.info(f"event: {fmt_json(event)}")
    hb_needs: dict = event["needs"]
    hb_wants: dict = event["wants"]

    with cdtmp():
        # TODO: download .xlsx file from s3
        xlsx_fn = ""

        # read excel sheets into memory
        df_needs = read_excel_sheet(xlsx_fn, sheet_num=0)
        df_wants = read_excel_sheet(xlsx_fn, sheet_num=1)

    status_code = 200
    body = {}

    # filter communties by needs
    df_needs = filter_communities(df_needs, hb_needs)
    if len(df_needs.index) == 0:
        # payload has filtered out all communities so
        # the client (CPU) should modify the request
        status_code = 422
        body["error"] = "Unprocessable Content"
        body["error_msg"] = "All communities have been filtered out leaving none to rank. " \
                            "Modify request payload."
        return {
            "statusCode": status_code,
            "body": body
        }

    # score communities by wants
    df_wants = score_communities(df_wants, hb_wants)

    # apply filter and sort scores to rank
    df = pd.merge(df_needs, df_wants, left_index=True, right_index=True)
    df = rank_communities(df)

    # get the top 3 communities (at most)
    body["top_communities"] = compile_top_communities(df, n=3)
    logger.info(fmt_json(body))

    return {
        "statusCode": status_code,
        "body": body
    }


if __name__ == "__main__":
    event = {
        "needs": {
            "price_range_lower": "400k",
            "price_range_upper": "MAX",
            "age_of_home": "Does not Matter",
            "location": ["West Valley", "Isolated from City"],
            "size_of_community": ["Small", "Medium"]
        },
        "wants": {
            "gated": 4,
            "quality_golf_courses": 5,
            "mult_golf_courses": 4,
            "mountain_views": 4,
            "many_social_clubs": 2,
            "softball_field": 1,
            "fishing": 1,
            "woodwork_shop": 1,
            "competitive_pickleball": 3,
            "indoor_pool": 1,
            "quality_trails": 2,
            "dog_park": 1
        },
        "email_address": "hi@example.com"
    }
    resp = lambda_handler(event, None)
