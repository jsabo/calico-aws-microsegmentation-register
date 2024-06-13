import os.path
import yaml
import boto3
import logging
from src.utils.auth_utils import get_eks_token
from kubernetes import client, config
from kubernetes.client import CoreV1Api

KUBE_FILEPATH = '/tmp/kubeconfig'

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def set_up_kubeconfig_file(region: str, cluster_name: str):
    """
    Writes a local file with the config values required for running the kubernetes client
    :param region:
    :param cluster_name:
    :return:
    """
    logger.info("Setting up kube config")
    if not os.path.exists(KUBE_FILEPATH):
        eks_api = boto3.client('eks', region_name=region)
        cluster_info = eks_api.describe_cluster(name=cluster_name)
        cert = cluster_info['cluster']['certificateAuthority']['data']
        endpoint = cluster_info['cluster']['endpoint']
        kube_content = dict()
        kube_content['apiVersion'] = 'v1'
        kube_content['clusters'] = [{'cluster': {'server': endpoint, 'certificate-authority-data': cert},
                                     'name': 'kubernetes'}]
        kube_content['contexts'] = [{'context': {'cluster': 'kubernetes', 'user': 'aws'},
                                     'name': 'aws'}]
        kube_content['current-context'] = 'aws'
        kube_content['Kind'] = 'config'
        kube_content['users'] = [{'name': 'aws', 'user': 'lambda'}]
        logger.debug("Writing kubeconfig file")
        with open(KUBE_FILEPATH, 'w') as outfile:
            yaml.dump(kube_content, outfile, default_flow_style=False)


def get_k8s_api_client(region: str, cluster_name: str) -> CoreV1Api:
    logger.info('Configuring kubernetes api client')
    set_up_kubeconfig_file(region, cluster_name)
    token = get_eks_token(region, cluster_name)
    config.load_kube_config(KUBE_FILEPATH)
    configuration = client.Configuration()
    configuration.api_key['authorization'] = token
    configuration.api_key_prefix['authorization'] = 'Bearer'
    api = client.ApiClient(configuration)
    v1 = client.CoreV1Api(api)
    return v1