import boto3
import logging

REGION_INDEX = 3
ACCOUNT_ID_INDEX = 4
INSTANCE_ID_INDEX = 5

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def parse_instance_arn(instance_arn: str) -> [str, str, str]:
    """
    This method parses an instance ARN arn:aws:ec2:<aws_region>:<account_id>:instance/<instance_id> and returns a triple
     of account ID, AWS region and instance ID
    :param instance_arn: the ARN of the instance whose data we want
    :return: account_id, region, instance_id
    """
    arn_list = instance_arn.split(':')
    region = arn_list[REGION_INDEX]
    account_id = arn_list[ACCOUNT_ID_INDEX]
    instance_id = arn_list[INSTANCE_ID_INDEX].split('/')[1]
    return region, account_id, instance_id


def is_registration_event(event: dict) -> bool:
    """
    Checks if this is an event that should trigger a registration or not
    :param event: the event that was triggered
    :return: True if the event should trigger an instance registration and False otherwise
    """
    source = event.get("source", "")
    detail = event.get("detail", {})
    state = detail.get("state", "").lower()
    return source == "aws.ec2" and state == "running"


def get_instance_network_data(instance_arn: str) -> dict:
    """
    This method returns all the missing data we need to register an EC2 instance with Calico Enterprise™
    :param instance_arn the arn of the instance whose data we require
    :return: the instance's IP address
    """
    # todo multiaccount
    region, account_id, instance_id = parse_instance_arn(instance_arn)
    ec2_api = boto3.client('ec2', region_name=region)
    reservation = ec2_api.describe_instances(InstanceIds=[instance_id])['Reservations'][0]
    instance = reservation['Instances'][0]
    network_interfaces = instance['NetworkInterfaces']
    tags = instance['Tags']
    res_map = {'Tags': tags, 'network_values': {}}
    for network_interface in network_interfaces:
        id = network_interface['NetworkInterfaceId']
        private_ip_address = network_interface['PrivateIpAddress']
        res_map['network_values'][id] = private_ip_address
    return res_map