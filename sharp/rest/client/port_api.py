

import logging
import requests as rq

from requests.packages.urllib3.exceptions import InsecureRequestWarning
rq.packages.urllib3.disable_warnings(InsecureRequestWarning)

from rest.client.rest_client_base import RestClientBase

log = logging.getLogger(__name__)


class PortApi(RestClientBase):

    def _make_vm_port(self, port):

        res = {'name': port['deviceName'],
               'network_name': port['networkName'],
               'vlan': port['networkVlan']}

        return res

    def _make_vm_ports(self, ports):
        return [self._make_vm_port(port) for port in ports]

    def get_vm_ports_by_network_id(self, network_id):
        headers = self._customize_header()
        if headers:
            r = rq.get("https://{center_ip}/networks/{networkId}/vnics".
                       format(center_ip=self.center_ip, networkId=network_id),
                       headers=headers, verify=False)
            if r.status_code == rq.codes.ok:
                return self._make_vm_ports(r.json().get('items'))
            else:
                log.error("Some errors occurred while querying vm's ports, the error messages is %s" % r.text)
                return None
        else:
            return None
