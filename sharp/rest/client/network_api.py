
import logging
import requests as rq

from requests.packages.urllib3.exceptions import InsecureRequestWarning
rq.packages.urllib3.disable_warnings(InsecureRequestWarning)

from rest.client.rest_client_base import RestClientBase

log = logging.getLogger(__name__)


class NetworkApi(RestClientBase):

    def _make_vm_network(self, network):

        res = {'id'  : network['id'],
               'name': network['name'],
               'vlan': network['vlan'],
               'connect_mode': network['connectMode'],
               'vlan_flag': network['vlanFlag'],
               'mtu': network['mtu']}

        res['customer_vlan'] = network['userVlan']
        res['tpid'] = network['tpidType']

        return res

    def _make_vm_networks(self, networks):
        return [self._make_vm_network(network) for network in networks]

    def get_vm_networks(self):
        headers = self._customize_header()
        if headers:
            r = rq.get("https://{center_ip}/hosts/{hostId}/networks?type=vmnetwork".
                       format(center_ip=self.center_ip, hostId=self._convert_node_ip_to_id()),
                       headers=headers, verify=False)
            if r.status_code == rq.codes.ok:
                return self._make_vm_networks(r.json())
            else:
                log.error("Some errors occurred while querying vm network, the error messages is %s" % r.text)
                return None
        else:
            return None
