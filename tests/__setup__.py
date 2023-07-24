import glob
import os
import sys

# add service and lambdas dir to system path, otherwise cannot import modules
PROJ_ROOT_PATH = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), os.pardir
)
SERVICE_PATH = os.path.join(PROJ_ROOT_PATH, "service")
LAMBDAS_PATH = os.path.join(SERVICE_PATH, "lambdas")
sys.path.append(PROJ_ROOT_PATH)
sys.path.append(SERVICE_PATH)
sys.path.append(LAMBDAS_PATH)

# test file paths
TEST_DATA_PATH = os.path.join(PROJ_ROOT_PATH, "tests", "data")
TEST_EVENTS_PATH = os.path.join(PROJ_ROOT_PATH, "tests", "events")
ALL_EVENT_FILES = [os.path.basename(x) for x in sorted(
    glob.glob(os.path.join(TEST_EVENTS_PATH, "*.json"))
)]
ALL_EXCEL_FILES = [os.path.basename(x) for x in sorted(
    glob.glob(os.path.join(TEST_DATA_PATH, "*.xlsx"))
)]