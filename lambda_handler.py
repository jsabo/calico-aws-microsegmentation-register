import logging
import configparser
from botocore.exceptions import ClientError
from src.aggregated_kubernetes_client import register_host_endpoint
from src.case_classes import RegistrationServiceParams, RegistrationResponse, EventResponse
from src.utils.aws_utils import parse_instance_arn, is_registration_event
from src.utils.k8s_utils import get_k8s_api_client

logger = logging.getLogger()
logger.setLevel(logging.INFO)

CONFIG_FILE = 'config.ini'


def register_with_calico(instance_arn: str, service_params: RegistrationServiceParams) -> RegistrationResponse:
    """
    Subroutine that attempts to register an EC2 instance with Calico Enterprise™
    :param instance_arn the ARN of the instance to register. Includes account ID, instance ID and AWS region
    :param service_params parameters required for registering an endpoint
    :return: A dict with the ARN as the key and a boolean value indicating whether the operation was a success (True)
    or a failure (False)
    """
    logger.info('Registering instance {}'.format(instance_arn))
    try:
        region, account_id, instance_id = parse_instance_arn(instance_arn)
        v1 = get_k8s_api_client(region, service_params.cluster_name)
        register_host_endpoint(v1, instance_arn, service_params.filter_tag)
        return RegistrationResponse(instance_arn, True)
    except ClientError as ce:
        logger.error('ClientError with error code {} thrown while processing instance ARN {}'.format(ce.response['Error']['Code'], instance_arn))
        return RegistrationResponse(instance_arn, False)
    except Exception as e:
        logger.error('Unexpected error {} while processing instance ARN {}'.format(str(e), instance_arn))
        return RegistrationResponse(instance_arn, False)


def handle(event: dict) -> dict:
    """
    Handles ec2 events and triggers instance registration when relevant
    :param event: the event that the code is evaluating
    :return: an EventResponse object with 200 if an event triggered a successful registration or if a registration
    wasn't needed, or an EventResponse object with a 500 code if the registration was required but was for some
    reason unsuccessful
    """
    if is_registration_event(event):
        service_config = configparser.RawConfigParser()
        service_config.read(CONFIG_FILE)
        service_params = RegistrationServiceParams(service_config)
        logger.info('Starting registration using cluster {}'.format(service_params.cluster_name))
        if service_params.filter_tag_key:
            logger.info('Filtering by tag key: {}, value:{}'.format(service_params.filter_tag_key,
                                                                    service_params.filter_tag_value))
        else:
            logger.info('Not filtering by tag')
        resources = event.get('resources', [])
        if len(resources) > 0:
            results = [register_with_calico(r, service_params) for r in resources]
            succeeded = [result.instance_arn for result in results if result.success]
            failed = [result.instance_arn for result in results if result not in succeeded]
            if failed:
                return EventResponse(500, 'Registration failed for {}'.format(' ,'.join(failed))).to_dict()
            return EventResponse(200, 'Registration successful for {}'.format(' ,'.join(succeeded))).to_dict()
    return EventResponse(200, 'State change didn\'t prompt registration').to_dict()


def handler(event, context):
    return handle(event)