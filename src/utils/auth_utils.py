import base64
import boto3
import logging
import re
from botocore.signers import RequestSigner

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class EKSAuth(object):
    METHOD = 'GET'
    EXPIRES = 60
    EKS_HEADER = 'x-k8s-aws-id'
    EKS_PREFIX = 'k8s-aws-v1.'
    STS_URL = 'sts.amazonaws.com'
    STS_ACTION = 'Action=GetCallerIdentity&Version=2011-06-15'

    def __init__(self, cluster_id, region='us-east-1'):
        self.cluster_id = cluster_id
        self.region = region

    def get_token(self):
        """
        Return bearer token
        """
        session = boto3.session.Session()
        # Get ServiceID required by class RequestSigner
        client = session.client("sts", region_name=self.region)
        service_id = client.meta.service_model.service_id

        signer = RequestSigner(
            service_id,
            session.region_name,
            'sts',
            'v4',
            session.get_credentials(),
            session.events
        )

        params = {
            'method': self.METHOD,
            'url': 'https://sts.{}.amazonaws.com/?Action=GetCallerIdentity&Version=2011-06-15'.format(self.region),
            'body': {},
            'headers': {
                self.EKS_HEADER: self.cluster_id
            },
            'context': {}
        }

        signed_url = signer.generate_presigned_url(
            params,
            region_name=session.region_name,
            expires_in=self.EXPIRES,
            operation_name=''
        )

        base64_url = base64.urlsafe_b64encode(signed_url.encode('utf-8')).decode('utf-8')
        return self.EKS_PREFIX + re.sub(r'=*', '', base64_url)


def get_eks_token(region: str, cluster_name: str) -> str:
    """
    Returns a base64 encoded pre-signed URL that can be used for authentication with the EKS cluster
    :param region: the region where the cluster is located
    :param cluster_name: the name of the EKS cluster
    :return:
    """
    logger.info('Getting eks authentication token')
    eks = EKSAuth(cluster_name, region=region)
    token = eks.get_token()
    return token