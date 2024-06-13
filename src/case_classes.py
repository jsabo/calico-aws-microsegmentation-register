import json
from configparser import RawConfigParser


class RegistrationServiceParams:
    """
    Case class containing the parameters needed to execute the registration service
    """
    def __init__(self, service_config: RawConfigParser):
        self.cluster_name = service_config.get('k8_cluster_section', 'cluster.name')
        self.filter_tag_key = service_config.get('instance_parameters_section', 'tag.key', fallback=None)
        self.filter_tag_value = service_config.get('instance_parameters_section', 'tag.value', fallback=None)
        self.filter_tag = {'Key': self.filter_tag_key, 'Value': self.filter_tag_value} if self.filter_tag_key is not None else {}


class RegistrationResponse:
    """
    Case class used to construct responses to Calico Enterprise registration attempts
    """
    def __init__(self, instance_arn: str, success: str):
        self.instance_arn = instance_arn
        self.success = success


class EventResponse:
    """
    Case class used to construct lambda event responses
    """
    def __init__(self, status_code: str, body: str):
        self.status_code = status_code
        self.body = body

    def to_dict(self):
        return {'statusCode': self.status_code, 'body': json.dumps(self.body)}