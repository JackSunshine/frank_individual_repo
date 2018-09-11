

import logging
import sys
import signal
import threading
import time
from ovsdb import ovsdb_monitor
from common import constants
from openflow import ics_bridge
from rest.client import manager as r_client


LOG = logging.getLogger(__name__)


class OVSAgent(object):

    def __init__(self, ryu_app):
        super(OVSAgent, self).__init__()
        self.ryu_app = ryu_app
        self.bridges_mapping = {}
        self.ovsdb_client = None
        self.rest_client = None
        self._post_event = threading.Event()
        self.polling_interval = 1
        self.iter_num = 0
        self.center_ip = None
        self.username = None
        self.password = None

        self.run_daemon_loop = True

        self.catch_sigterm = False
        self.catch_sighup = False

    def _handle_sigterm(self, signum, frame):
        self.catch_sigterm = True

    def _handle_sighup(self, signum, frame):
        self.catch_sighup = True

    def _check_and_handle_signal(self):
        if self.catch_sigterm:
            LOG.info("Agent caught SIGTERM, quitting daemon loop.")
            self.run_daemon_loop = False
            self.catch_sigterm = False
        if self.catch_sighup:
            LOG.info("Agent caught SIGHUP, resetting.")
            self.catch_sighup = False
        return self.run_daemon_loop

    def loop_count_and_wait(self, start_time, port_stats):
        # sleep till end of polling interval
        elapsed = time.time() - start_time
        LOG.debug("Agent rpc_loop - iteration:%(iter_num)d "
                  "completed. Processed ports statistics: "
                  "%(port_stats)s. Elapsed:%(elapsed).3f",
                  {'iter_num': self.iter_num,
                   'port_stats': port_stats,
                   'elapsed': elapsed})
        if elapsed < self.polling_interval:
            time.sleep(self.polling_interval - elapsed)
        else:
            LOG.debug("Loop iteration exceeded interval "
                      "(%(polling_interval)s vs. %(elapsed)s)!",
                      {'polling_interval': self.polling_interval,
                       'elapsed': elapsed})
        self.iter_num = self.iter_num + 1

    def daemon_loop(self):
        # Start everything.
        LOG.info("Agent initialized successfully, now running... ")
        signal.signal(signal.SIGTERM, self._handle_sigterm)
        if hasattr(signal, 'SIGHUP'):
            signal.signal(signal.SIGHUP, self._handle_sighup)
        while self._check_and_handle_signal():
            start = time.time()
            LOG.debug("Agent rpc_loop - iteration:%d started",
                      self.iter_num)
            time.sleep(0.5)
            self.loop_count_and_wait(start, None)

    def start(self):
        self._post_event.clear()
        self.ovsdb_client = ovsdb_monitor.OvsdbClient.get_client(self, constants.OVSDB_CONNECTION)
        self._post_event.set()

        self.rest_client = r_client.RestClient.get_client(self.center_ip, self.username, self.password)

    def process_bridge_events(self, bridge_event, name):
        self._post_event.wait()

        if bridge_event == constants.BRIDGE_CREATE_EVENT:
            br = ics_bridge.IcsNormalBridge(name, self.ovsdb_client, ryu_app=self.ryu_app)
            self.bridges_mapping[name] = br
            if name.startswith('manage'):
                return
            # br.set_secure_mode()
            br.setup_controllers()
            br.setup_default_table()

    def process_port_events(self, port_event, name):

        if name.startswith("en"):
            return

        if port_event == constants.PORT_CREATE_EVENT:
            networks = self.rest_client.get_vm_network()
            for network in networks:
                ports = self.rest_client.get_vm_ports_by_network_id(network['id'])
                if name in [port['name'] for port in ports]:
                    if network.get('tpid'):
                        br = self.bridges_mapping[self.ovsdb_client.port_to_br(name).execute()]
                        if '-' not in network['customer_vlan']:
                            br.set_db_attribute('Port', name, 'cvlans', int(network['customer_vlan']))
                        else:
                            start = network['customer_vlan'].split('-')[0]
                            end = network['customer_vlan'].split('-')[1]
                            br.set_db_attribute('Port', name, 'cvlans', range(int(start), int(end) + 1))
                        br.set_db_attribute('Port', name, 'vlan_mode', 'dot1q-tunnel')

    def process_internal_events(self):
        pass


def main(ryu_app):

    try:
        agent = OVSAgent(ryu_app)
    except (RuntimeError, ValueError) as e:
        LOG.error("%s Agent terminated!", e)
        sys.exit(1)
    agent.start()
    agent.daemon_loop()
