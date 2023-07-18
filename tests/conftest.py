import json
import os

import pytest

from topshelfsoftware_util.log import get_logger

from __setup__ import TEST_EVENTS_PATH
# ----------------------------------------------------------------------------#
#                               --- Logging ---                               #
# ----------------------------------------------------------------------------#
logger = get_logger("conftest")


@pytest.fixture
def test_event_to_dict(event_file: str) -> dict:
    """Read a JSON-formatted file into a Python dictionary."""
    event_fp = os.path.join(TEST_EVENTS_PATH, event_file)
    logger.info(f"reading JSON file {event_file} into dict")
    with open(event_fp, "r") as fp:
        event = json.load(fp)
    yield event
