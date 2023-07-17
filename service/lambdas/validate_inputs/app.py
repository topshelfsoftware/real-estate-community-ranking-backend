import json

from topshelfsoftware_util.common import fmt_json
from topshelfsoftware_util.log import get_logger

from validate import validate_payload
# ----------------------------------------------------------------------------#
#                               --- Globals ---                               #
# ----------------------------------------------------------------------------#
from __init__ import MODULE_NAME

# ----------------------------------------------------------------------------#
#                               --- Logging ---                               #
# ----------------------------------------------------------------------------#
logger = get_logger(f"{MODULE_NAME}.{__name__}")

# ----------------------------------------------------------------------------#
#                                 --- MAIN ---                                #
# ----------------------------------------------------------------------------#
def lambda_handler(event, context):
    logger.info(f"event: {fmt_json(event)}")

    if not isinstance(event, dict):
        logger.info("Converting event to dict")
        event = json.loads(event)
        logger.info(f"event: {fmt_json(event)}")
    payload = event
    
    validate_payload(payload)
    logger.info("Validation succeeded")

    return event


if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser()
    parser.add_argument("--event-file", dest="event_file", type=str, required=True,
                        help="JSON file containing the Lambda event object")
    args = parser.parse_args()

    with open(args.event_file, "r") as fp:
        event = json.load(fp)
    resp = lambda_handler(event, None)
    logger.info(f"resp: {resp}")