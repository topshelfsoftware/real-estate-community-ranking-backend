"""Validation module for service inputs."""

import os

import jsonschema

from topshelfsoftware_util.json import load_json_schema
from topshelfsoftware_util.log import get_logger
# ----------------------------------------------------------------------------#
#                               --- Globals ---                               #
# ----------------------------------------------------------------------------#
from .__init__ import MODULE_NAME, SRC_PATH
PAYLOAD_SCHEMA_FILE = os.path.join(SRC_PATH, "payload_schema.json")

# ----------------------------------------------------------------------------#
#                               --- Logging ---                               #
# ----------------------------------------------------------------------------#
logger = get_logger(f"{MODULE_NAME}.{__name__}")

# ----------------------------------------------------------------------------#
#                                 --- MAIN ---                                #
# ----------------------------------------------------------------------------#
def validate_payload(payload: dict):
    """Validates the payload data structure including data types and allowed
    values. Throws a ValidationError exception if invalid, otherwise returns.
    
    Parameters
    ----------
    payload: dict
        Payload for the service.
    """
    logger.info("Validating the payload data structure")
    payload_schema = load_json_schema(PAYLOAD_SCHEMA_FILE)
    try:
        jsonschema.validate(instance=payload, schema=payload_schema)
        logger.info("Payload structure is valid per JSON schema")
    except jsonschema.ValidationError as e:
        logger.error(e)
        raise e
    return
