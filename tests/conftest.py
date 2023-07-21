import json
import os

import pytest

from topshelfsoftware_util.log import get_logger
# ----------------------------------------------------------------------------#
#                               --- Globals ---                               #
# ----------------------------------------------------------------------------#
from __setup__ import ALL_EVENT_FILES, TEST_EVENTS_PATH
FILE_DELIMITER = "_"

# ----------------------------------------------------------------------------#
#                               --- Logging ---                               #
# ----------------------------------------------------------------------------#
logger = get_logger("conftest")

# ----------------------------------------------------------------------------#
#                                 --- MAIN ---                                #
# ----------------------------------------------------------------------------#
@pytest.fixture
def get_event_as_dict(event_file: str) -> dict:
    """Read a JSON-formatted file into a Python dictionary."""
    event_fp = os.path.join(TEST_EVENTS_PATH, event_file)
    logger.info(f"reading JSON file {event_file} into dict")
    with open(event_fp, "r") as fp:
        event = json.load(fp)
    yield event


@pytest.fixture
def get_event_as_str(event_file: str) -> str:
    """Read a JSON-formatted file into a Python string."""
    event_fp = os.path.join(TEST_EVENTS_PATH, event_file)
    logger.info(f"reading JSON file {event_file} into dict")
    with open(event_fp, "r") as fp:
        event = fp.read()
    yield event


def get_test_event_files(matching: str = None) -> list[str]:
    """Obtain all test event files or a subset of the files
    matching the provided string."""
    subset = []
    for file_name in ALL_EVENT_FILES:
        file_no_ext, _ = os.path.splitext(file_name)
        file_kw = file_no_ext.split(FILE_DELIMITER)
        if matching is None or matching in file_kw:
            subset.append(file_name)
    return subset
