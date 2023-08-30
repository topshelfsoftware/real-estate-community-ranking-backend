from enum import Enum
import json
import time
import uuid

from topshelfsoftware_util.aws import create_boto3_client
from topshelfsoftware_util.common import fmt_json
from topshelfsoftware_util.log import get_logger
# ----------------------------------------------------------------------------#
#                               --- Globals ---                               #
# ----------------------------------------------------------------------------#
from .__init__ import MODULE_NAME, STATE_MACHINE_ARN
sfn_client = create_boto3_client("stepfunctions")

# ----------------------------------------------------------------------------#
#                               --- Logging ---                               #
# ----------------------------------------------------------------------------#
logger = get_logger(f"{MODULE_NAME}.{__name__}")

# ----------------------------------------------------------------------------#
#                                 --- MAIN ---                                #
# ----------------------------------------------------------------------------#
class SfnStatus(str, Enum):
    """Enumeration for step function status."""
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    TIMED_OUT = "TIMED_OUT"
    ABORTED = "ABORTED"


def launch_sfn(payload: dict) -> str:
    """Launch the step function with the specified payload.
    Return the execution ARN."""
    uid = str(uuid.uuid4())
    logger.info(f"Execution name: {uid}")

    # run step function
    logger.info(f"Launching step function: {STATE_MACHINE_ARN}")
    res = sfn_client.start_execution(
        stateMachineArn=STATE_MACHINE_ARN,
        name=uid,
        input=json.dumps(payload),
    )

    # retrieve the execution arn for the step function
    execution_arn = res["executionArn"]
    logger.info(f"execution arn: {execution_arn}")
    return execution_arn


def poll_sfn(execution_arn: str, step: float = 1) -> dict:
    """Poll the step function for status.
    Return the execution response once the status is no longer `RUNNING`."""
    sfn_status = SfnStatus.RUNNING.value
    n = 0
    while sfn_status == SfnStatus.RUNNING.value:
        time.sleep(step)
        n += 1
        
        logger.debug(f"polling execution arn: {execution_arn}")
        res = sfn_client.describe_execution(executionArn=execution_arn)
        logger.info(f"poll #{n:02d} response: {fmt_json(res)}")

        sfn_status = res["status"]
    logger.info(f"sfn status: {sfn_status}")
    return res


def get_exec_hist(execution_arn: str, max_results: int = 5) -> dict:
    """Retrieve the step function execution history."""
    exec_history = sfn_client.get_execution_history(
        executionArn=execution_arn,
        maxResults=max_results,
        reverseOrder=True
    )
    logger.info(f"execution history: {fmt_json(exec_history)}")
    return exec_history
