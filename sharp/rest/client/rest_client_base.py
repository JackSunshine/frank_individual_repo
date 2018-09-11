#encoding=utf-8
import requests as rq
import json
import logging
import abc
import six

from requests.packages.urllib3.exceptions import InsecureRequestWarning
rq.packages.urllib3.disable_warnings(InsecureRequestWarning)

CONFIG_FILE = '/etc/ics/ics-net/manageIP.conf'

log = logging.getLogger(__name__)


@six.add_metaclass(abc.ABCMeta)
class RestClientBase(object):

    def __init__(self, center_ip, username, password):
        self.center_ip = center_ip
        self.username = username
        self.password = password

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

    @staticmethod
    def get_local_node_address():
        with open(CONFIG_FILE, 'r') as f:
            for line in f.readlines():
                if line.startswith('IP='):
                    return line.split('=')[1]
        return None

    def _convert_node_ip_to_id(self):
        headers = self._customize_header()
        node_id = None
        if headers:
            r = rq.get('https://%s/hosts' % self.center_ip, headers=headers, verify=False)
            if r.status_code == rq.codes.ok:
                for node in r.json().get('items'):
                    if node.get('name') == self.get_local_node_address():
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
            log.error("Authentication failure.")
            return None

