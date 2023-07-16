"""Validation module for service inputs."""

import json

import jsonschema
from topshelfsoftware_util.log import get_logger
# ----------------------------------------------------------------------------#
#                               --- Globals ---                               #
# ----------------------------------------------------------------------------#
from __init__ import MODULE_NAME
PAYLOAD_SCHEMA_FILE = "payload_schema.json"

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
    payload_schema = _load_schema(PAYLOAD_SCHEMA_FILE)
    try:
        jsonschema.validate(instance=payload, schema=payload_schema)
        logger.info("Payload structure is valid per JSON schema")
    except jsonschema.ValidationError as e:
        logger.error(e)
        raise e
    return


def _load_schema(file: str) -> dict:
    """Loads a JSON schema file into a dictionary."""
    try:
        logger.info(f"Reading schema file: {file}")
        with open(file) as f:
            schema = json.loads(f.read())
            logger.debug(f"schema: {json.dumps(schema)}")
    except Exception as e:
        raise Exception(f"Failed to read schema file: {file}. Reason: {e}")
    
    return schema
