import base64
from http import HTTPStatus
import json

from botocore.exceptions import ClientError as BotoClientError

from topshelfsoftware_aws_util.sfn import (
    SfnStatus, get_exec_hist, launch_sfn, poll_sfn
)
from topshelfsoftware_util.json import fmt_json
from topshelfsoftware_util.log import get_logger
# ----------------------------------------------------------------------------#
#                               --- Globals ---                               #
# ----------------------------------------------------------------------------#
from .__init__ import MODULE_NAME, STATE_MACHINE_ARN
KNOWN_ERRORS = {
    "AssertionError": HTTPStatus.BAD_REQUEST,
    "WorksheetNotFoundError": HTTPStatus.BAD_REQUEST
}

# ----------------------------------------------------------------------------#
#                               --- Logging ---                               #
# ----------------------------------------------------------------------------#
logger = get_logger(f"{MODULE_NAME}.{__name__}")

# ----------------------------------------------------------------------------#
#                                 --- MAIN ---                                #
# ----------------------------------------------------------------------------#
def lambda_handler(event, context):
    logger.info(f"event: {fmt_json(event)}")
    payload_base64_encoded = event["body"]
    payload_decoded = base64.b64decode(payload_base64_encoded)
    logger.info(f"payload decoded: {payload_decoded}")

    try:
        # check if binary data was sent as a 'Buffer'
        buffer = json.loads(payload_decoded.decode())
        payload_type = buffer['type']
        bin_data = bytes(buffer["data"])  
    except UnicodeDecodeError:
        # data was delivered as decoded string
        payload_type = "decoded string"
        bin_data = payload_decoded
    finally:
        logger.info(f"payload type: {payload_type}")
        logger.info(f"payload binary data: {bin_data}")
    bin_data_base64_bytes = base64.b64encode(bin_data)
    bin_data_base64_str = bin_data_base64_bytes.decode("utf-8")
    logger.info(f"binary data base64 encoded string: {bin_data_base64_str}")
    payload = {"xlsx_base64_encoded": bin_data_base64_str}

    status = HTTPStatus.OK
    resp_body = {
        "metadata": {
            "stateMachineArn": STATE_MACHINE_ARN
        }
    }

    # launch the stepfunction
    try:
        execution_arn = launch_sfn(STATE_MACHINE_ARN, payload=payload)
        resp_body["metadata"]["executionArn"] = execution_arn
    except BotoClientError as e:
        status = HTTPStatus.BAD_GATEWAY
        err_msg = f"Boto3 Client Exception: {e}"
        err_type = "botocore.exceptions.ClientError"
    except Exception as e:
        status = HTTPStatus.INTERNAL_SERVER_ERROR
        err_msg = f"Unexpected Exception: {e}"
        err_type = status.phrase
    finally:
        if status in [HTTPStatus.INTERNAL_SERVER_ERROR, HTTPStatus.BAD_GATEWAY]:
            logger.error(err_msg)
            return fmt_lambda_resp(status, resp_body, err_msg, err_type)
    
    # poll the stepfunction
    try:
        sfn_resp = poll_sfn(execution_arn, step=0.5)
        resp_status = sfn_resp["status"]
        resp_body["status"] = resp_status
        
        start_date = sfn_resp.get("startDate", "")
        if start_date:
            resp_body["startDate"] = str(start_date)
            logger.info(f"start date: {start_date}")

        stop_date = sfn_resp.get("stopDate", "")
        if stop_date:
            resp_body["stopDate"] = str(stop_date)
            logger.info(f"stop date: {stop_date}")
        
        output = sfn_resp.get("output", {})
        if output:
            resp_body["output"] = json.loads(str(output))
            logger.info(f"output: {output}")
        
        if resp_status == SfnStatus.FAILED.value:
            exec_history = get_exec_hist(execution_arn)
            
            fail_param = "executionFailedEventDetails"
            for exec in exec_history["events"]:
                if fail_param in exec:
                    error = exec[fail_param]["error"]
                    logger.error(f"failure cause: {error}")
                    if error in KNOWN_ERRORS.keys():
                        status = KNOWN_ERRORS[error]
                    else:
                        status = HTTPStatus.INTERNAL_SERVER_ERROR
                    try:
                        resp_body["error"] = json.loads(exec[fail_param]["cause"])
                    except:
                        resp_body["error"] = exec[fail_param]["cause"]
                    break
            
            if resp_body.get("error") is None:
                status = HTTPStatus.INTERNAL_SERVER_ERROR
                resp_body["error"] = "failed to find stepfunction failure details"
    except BotoClientError as e:
        status = HTTPStatus.BAD_GATEWAY
        err_msg = f"Boto3 Client Exception: {e}"
        err_type = "botocore.exceptions.ClientError"
    except Exception as e:
        status = HTTPStatus.INTERNAL_SERVER_ERROR
        err_msg = f"Unexpected Exception: {e}"
        err_type = status.phrase
    finally:
        if status in [HTTPStatus.INTERNAL_SERVER_ERROR, HTTPStatus.BAD_GATEWAY]:
            logger.error(err_msg)
            return fmt_lambda_resp(status, resp_body, err_msg, err_type)

    return fmt_lambda_resp(status, resp_body)


def fmt_lambda_resp(status: HTTPStatus, body: dict,
                    err_msg: str = None, err_type: str = None) -> dict:
    """Format the Lambda response."""
    if err_msg is not None and err_type is not None:
        body["error"] = {
            "errorMessage": err_msg,
            "errorType": err_type
        }
    resp = {
        "statusCode": status.value,
        "body": json.dumps(body)
    }
    logger.info(f"status code: {status.value}")
    logger.info(f"response body: {fmt_json(body)}")
    return resp
