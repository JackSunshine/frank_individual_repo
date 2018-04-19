#encoding=utf-8
import requests as rq
import json
import time
import os
import sys
from requests.packages.urllib3.exceptions import InsecureRequestWarning
rq.packages.urllib3.disable_warnings(InsecureRequestWarning)

NODE_IP = 'node_ip'
SWITCH_NAME = 'switch_name'
DATA_NETWORK_NAME = 'data_network_name'
IP = 'ip'
NETMASK = 'netmask'
GATEWAY = 'gateway'
VLANTAG = 'vlan_tag'

NODE_IP_INDEX = 0
SWITCH_NAME_INDEX = 1
DATA_NETWORK_NAME_INDEX = 2
IP_INDEX = 3
NETMASK_INDEX = 4
GATEWAY_INDEX = 5
VLANTAG_INDEX = 6

FILE_NAME = 'data_networks.txt'


class DataNetwork(object):

    def __init__(self, ip_address):
        self.center_ip = ip_address
        self.counter = 0
        self.failure = 0

    def _write_message_to_logfile(self, messages):
        with open('data_networks.log', 'a+') as log:
            date = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            log.write("%s:" % (date + ' ' + messages + '\n'))

    def _customize_header(self):
        token = self._authentication()
        if token:
            headers = {
                'Accept': 'application/json;charset=utf-8',
                'version': '5.0',
                'Content-Type': 'application/json',
                'Authorization': token
            }
        else:
            return None
        return headers

    def _convert_node_ip_to_id(self, ip_address):
        headers = self._customize_header()
        node_id = None
        if headers:
            r = rq.get('https://%s/hosts' % self.center_ip, headers=headers, verify=False)
            if r.status_code == rq.codes.ok:
                for node in r.json().get('items'):
                    if node.get('name') == ip_address:
                        node_id = node.get('id')

        return node_id

    def _convert_switch_name_to_id(self, name):
        headers = self._customize_header()
        switch_id = None
        if headers:
            r = rq.get('https://%s/vswitchs' % self.center_ip, headers=headers, verify=False)
            if r.status_code == rq.codes.ok:
                for node in r.json().get('items'):
                    if node.get('name') == name:
                        switch_id = node.get('id')
        return switch_id

    def _authentication(self, username='admin', password='admin@inspur'):
        body_data = {
            'username': username,
            'password': password,
            'locale': 'cn',
            'domain': 'internal',
            'captcha': ''
        }

        headers = {
            'Accept': 'application/json;charset=utf-8',
            'version': '5.0',
            'Content-Type': 'application/json'
        }

        r = rq.post('https://%s/authentication' % self.center_ip, data=json.dumps(body_data),
                    headers=headers, verify=False)
        if r.status_code == rq.codes.ok:
            return r.json().get('sessonId')
        else:
            self._write_message_to_logfile("Authentication failure.")
            return None

    def _create_data_network(self, data_network_name, vlan_tag, switch_id, ip,
                             netmask, gateway, node_id):
        body_data = {
            'name': data_network_name,
            'vlan': vlan_tag,
            'type': 'DATANETWORK',
            'vswitchDto': {
                'id': switch_id
            },
            'portDtos': [{
                'ip': ip,
                'netmask': netmask,
                'gateway': gateway,
                'hostDto': {
                    'id': node_id,
                }
            }
            ]
        }

        headers = self._customize_header()
        if headers:
            r = rq.post('https://%s/networks?type=datanetwork' % self.center_ip, data=json.dumps(body_data),
                        headers=headers, verify=False)
            if r.status_code == rq.codes.ok:
                result = rq.get('https://%s/tasks/?processId=%s' % (self.center_ip, r.json().get('taskId')),
                                headers=headers, verify=False)
                if result.json().get('error') is None:
                    return True
                else:
                    self._write_message_to_logfile("Post data network failure, the error is" +
                                                   result.json().get('error'))
                    return False
            else:
                self._write_message_to_logfile("Post data network failure, the error messages is %s" % r.text)
                return False
        else:
            return False

    def check_before_start(self):
        if not os.path.exists(FILE_NAME):
            print("The configuration document %s is not exist in current directory, please prepare it." % FILE_NAME)
            print("The document format should be as following: \n"
                  "%-15s %-12s %-20s %-15s %-15s %-15s %-5s" % (NODE_IP, SWITCH_NAME, DATA_NETWORK_NAME,
                                                                IP, NETMASK, GATEWAY, VLANTAG))
            print("%-15s %-12s %-20s %-15s %-15s %-15s %-5s" % ("100.5.4.100", "vswitch", "data_network",
                                                                "100.2.3.100", "255.255.255.0", "100.2.3.254", "0"))
            return False
        return True

    def batch_create_data_networks(self):
        if self.check_before_start():

            with open(FILE_NAME, 'r') as f:
                for line in f.readlines():
                    values = line.split()
                    if NODE_IP not in line and values:
                        switch_id = self._convert_switch_name_to_id(values[SWITCH_NAME_INDEX])
                        node_id = self._convert_node_ip_to_id(values[NODE_IP_INDEX])
                        result = None
                        if switch_id and node_id:
                            result = self._create_data_network(values[DATA_NETWORK_NAME_INDEX],
                                                               values[VLANTAG_INDEX], switch_id,
                                                               values[IP_INDEX], values[NETMASK_INDEX],
                                                               values[GATEWAY_INDEX], node_id)
                        if not result:
                            self._write_message_to_logfile("Fail to create data_network=%s on "
                                                           "the %s:%s of node:%s:%s, "
                                                           "please check it later." % (values[DATA_NETWORK_NAME_INDEX],
                                                                                       values[SWITCH_NAME_INDEX],
                                                                                       switch_id,
                                                                                       values[NODE_IP_INDEX], node_id))
                            self.failure = self.failure + 1
                        else:
                            self._write_message_to_logfile("Create data_network=%s on "
                                                           "the %s:%s of node:%s:%s successfully." %
                                                           (values[DATA_NETWORK_NAME_INDEX],
                                                            values[SWITCH_NAME_INDEX],
                                                            switch_id,
                                                            values[NODE_IP_INDEX], node_id))
                            self.counter = self.counter + 1

            """The statistics might be inaccuracy since create data network is asynchronous operation."""
            self._write_message_to_logfile("Has been created %d data networks, success=%d, fail=%d." %
                                           (self.counter + self.failure, self.counter, self.failure))


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Please specify the icenter address, like: batch.py 100.7.33.100")
        sys.exit(0)
    data_network = DataNetwork(sys.argv[1])
    data_network.batch_create_data_networks()
