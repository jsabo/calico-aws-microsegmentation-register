import logging
from kubernetes.client import CoreV1Api
from src.utils.aws_utils import parse_instance_arn, get_instance_network_data

logger = logging.getLogger()
logger.setLevel(logging.INFO)

RESPONSE_ACCEPT_TYPES = ['application/json', 'application/yaml', 'application/vnd.kubernetes.protobuf',
                         'application/json;stream=watch', 'application/vnd.kubernetes.protobuf;stream=watch']


def list_namespaced_pod(v1: CoreV1Api, namespace: str):
    """
    Lists all the pods given a namespace
    :param v1:
    :param namespace:
    :return:
    """
    logger.info('Printing pods for namespace {}'.format(namespace))
    try:
        ret = v1.list_namespaced_pod(namespace)
        for i in ret.items:
            logger.info("%s\t%s\t%s" % (i.status.pod_ip, i.metadata.namespace, i.metadata.name))
    except Exception as e:
        logger.error('Error while trying to print pods from namespace {}'.format(namespace))


def list_host_endpoints(v1: CoreV1Api) -> str:
    logger.debug('Listing host endpoints')
    path_params = {}
    query_params = {"limit": 500}
    auth_settings = ['BearerToken']
    header_params = {'Accept': v1.api_client.select_header_accept(RESPONSE_ACCEPT_TYPES),
                     'Content-Type': v1.api_client.select_header_content_type(['*/*'])}
    # Get all the host endpoints
    try:
        logger.info('Getting host endpoints with response type str')
        host_endpoints = v1.api_client.call_api('/apis/projectcalico.org/v3/hostendpoints',
                                                'GET',
                                                path_params=path_params,
                                                query_params=query_params,
                                                header_params=header_params,
                                                auth_settings=auth_settings,
                                                response_type='str')
        logger.info(host_endpoints)
    except Exception as e:
        logger.error(e)


def register_host_endpoint(v1: CoreV1Api, instance_arn: str, filter_tag: dict):
    logger.info('Registering host endpoint')
    path_params = {}
    auth_settings = ['BearerToken']
    header_params = {'Accept': v1.api_client.select_header_accept(RESPONSE_ACCEPT_TYPES),
                     'Content-Type': v1.api_client.select_header_content_type(['*/*'])}
    # Get all the host endpoints
    try:
        region, account_id, instance_id = parse_instance_arn(instance_arn)
        n_id_to_ip_map = get_instance_network_data(instance_arn)
        logger.info('instance data is {}'.format(n_id_to_ip_map))
        tags = n_id_to_ip_map.get('Tags', [])
        filter_exists = bool(filter_tag)
        instance_filtered = True if filter_exists else False  # if no filter exists, we register everything
        if filter_tag:
            for tag in tags:
                if filter_tag['Key'] == tag['Key'] and filter_tag['Value'] == tag['Value']:
                    instance_filtered = False
        if instance_filtered:
            logger.info('Instance was filtered for not having tag with key {} and value {}'.format(filter_tag['Key'],
                                                                                                   filter_tag['Value']))
        else:
            for network_id in n_id_to_ip_map['network_values'].keys():
                private_ip = n_id_to_ip_map['network_values'][network_id]
                body_params = {'apiVersion': 'projectcalico.org/v3',
                               'kind': 'HostEndpoint',
                               'metadata': {
                                   'name': instance_id,
                                   'labels': {
                                       'account_id': account_id,
                                       'region': region,
                                       'k8s-app': 'calico-hep'
                                   }
                               },
                               'spec': {
                                   'interfaceName': 'ens5',
                                   'node': instance_id,
                                   'expectedIPs': [private_ip]
                               }
                               }
                for tag in tags:
                    body_params['metadata']['labels'].update({tag['Key'].lower(): tag['Value'].lower()})
                logger.info('Registering host endpoints with response type str and body params {}'.format(body_params))
                registration_response = v1.api_client.call_api('/apis/projectcalico.org/v3/hostendpoints',
                                                               'POST',
                                                               path_params=path_params,
                                                               header_params=header_params,
                                                               auth_settings=auth_settings,
                                                               body=body_params,
                                                               response_type='str')
                logger.info(registration_response)
    except Exception as e:
        logger.error(e)
