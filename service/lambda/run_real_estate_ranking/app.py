from http import HTTPStatus
import json

from botocore.exceptions import ClientError as BotoClientError

from topshelfsoftware_util.common import fmt_json
from topshelfsoftware_util.log import get_logger

from sfn import SfnStatus, get_exec_hist, launch_sfn, poll_sfn
# ----------------------------------------------------------------------------#
#                               --- Globals ---                               #
# ----------------------------------------------------------------------------#
from __init__ import MODULE_NAME, STATE_MACHINE_ARN
KNOWN_ERRORS = {
    "ValidationError": HTTPStatus.BAD_REQUEST,
    "UnprocessableContentError": HTTPStatus.UNPROCESSABLE_ENTITY
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

    body = event["body"]
    # convert body from string to dict if req'd
    if isinstance(body, str):
        body = json.loads(body)
        logger.info(f"Converted event['body'] to type: {type(body)}")
    logger.info(f"event body: {fmt_json(body)}")

    status = HTTPStatus.OK
    resp_body = {
        "metadata": {
            "stateMachineArn": STATE_MACHINE_ARN
        }
    }

    # launch the stepfunction
    try:
        execution_arn = launch_sfn(payload=body)
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
        sfn_resp = poll_sfn(execution_arn, step=2)
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


if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser()
    parser.add_argument("--event-file", dest="event_file", type=str, required=True,
                        help="JSON file containing the Lambda event object")
    parser.add_argument("--out-file", dest="out_file", type=str, required=True,
                        help="JSON file to write the Lambda response body")
    args = parser.parse_args()

    with open(args.event_file, "r") as fp:
        event = json.load(fp)
    resp = lambda_handler(event, None)
    with open(args.out_file, "w") as fp:
        json.dump(resp["body"], fp, indent=4)
