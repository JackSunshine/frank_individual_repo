from rest.client.network_api import NetworkApi
from rest.client.port_api import PortApi


class RestClient(NetworkApi, PortApi):

    def __init__(self, center_ip, username, password):
        super(RestClient, self).__init__(center_ip, username, password)

    @classmethod
    def get_client(cls, center_ip, username='admin', password='admin@inspur'):
        return cls(center_ip, username, password)
