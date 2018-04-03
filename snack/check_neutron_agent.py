import pycurl
import cStringIO
import os
import json
import subprocess
import time
import commands
import sys
import signal


class MonitorAgent(object):

    agent_name = {'Open vSwitch agent': 'neutron-openvswitch-agent',
                  'DHCP agent': 'neutron-dhcp-agent'}

    log_file = "/var/log/ics/icsnet/check_neutron_agent.log"

    def __init__(self):
        self.check_if_has_instance()
        self.db_conn = None
        self.buf = cStringIO.StringIO()
        self.curl = pycurl.Curl()
        self.host = self.get_hostname()
        self.address = self.get_server_address()
        self.curl.setopt(self.curl.URL, "http://%s:9696/v2.0/agents?host=%s" % (self.address, self.host))
        self.curl.setopt(self.curl.WRITEFUNCTION, self.buf.write)
        self.count = 0
        directory = os.path.dirname(self.log_file)
        if not os.path.exists(directory):
            os.makedirs(directory)
        self.write_messages_to_logfile("Started neutron agent monitor, %s, %s, pid is %s." % (
            self.host, self.address, os.getpid()))

    def check_if_has_instance(self):
        script_name = os.path.basename(__file__)
        errcode, output = commands.getstatusoutput("ps -aux | grep -e %s | grep -v grep | awk '{print $2}'" % (
            script_name))
        if output.replace(str(os.getpid()), ''):
            self.write_messages_to_logfile("The system already has a process running %s" % (
                output.replace(str(os.getpid()), '').rstrip('\n')))
            sys.exit(0)

    def check_if_agent_running(self, agent):
        errcode, output = commands.getstatusoutput("ps -aux | grep -e %s | grep -v grep | awk '{print $2}'" % (
            self.agent_name.get(agent)))
        if output:
            return True
        else:
            self.write_messages_to_logfile("We shouldn't restart neutron agent if agent is not running!")
            return False

    def get_server_address(self):
        with open('/etc/neutron/neutron.conf') as f:
            for line in f.readlines():
                if line.startswith('transport_url'):
                    return line[line.rfind("@") + 1:line.rfind(":")]

    def get_hostname(self):
        with open('/etc/hostname') as f:
            return f.readline().rstrip('\n')

    def write_messages_to_logfile(self, messages):
        with open(self.log_file, 'a+') as log:
            date = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            log.write("%s:" % (date) + messages + '\n')

    def check_host_and_address(self):
        if not self.host or not self.address:
            self.host = self.get_hostname()
            self.address = self.get_server_address()
            self.curl.setopt(self.curl.URL, "http://%s:9696/v2.0/agents?host=%s" % (self.address, self.host))
            self.write_messages_to_logfile("Checking hostname = %s and server address = %s!" % (
                                           self.host, self.address))

    def get_agent_status(self):
        self.check_host_and_address()
        try:
            self.curl.perform()
        except:
            self.write_messages_to_logfile("Error occurred while invoke Rest API!")
            return []
        if self.curl.getinfo(self.curl.HTTP_CODE) is not 200:
            self.write_messages_to_logfile("Get agent status failed(%d) through Rest API!" %
                                           self.curl.getinfo(self.curl.HTTP_CODE))
            return []

        try:
            agents_info = json.loads(self.buf.getvalue())
        except:
            self.write_messages_to_logfile("The message obtained is wrong %s" % (self.buf.getvalue()))
            return []

        self.buf.truncate(0)
        self.buf.seek(0)
        restart_agents = []
        for agent in agents_info['agents']:
            if not agent['alive']:
                restart_agents.append(agent['agent_type'])
        return restart_agents

    def restart_agent(self, agent='neutron-openvswitch-agent'):
        self.count = self.count + 1
        self.write_messages_to_logfile("Restarting %s, %d times to restart!" % (agent, self.count))
        subprocess.call('systemctl restart %s' % agent, shell=True)
        self.write_messages_to_logfile("Restarted %s, %d times to restart!" % (agent, self.count))

    def handle_sigterm(self, signum, frame):
        self.write_messages_to_logfile("Received SIGTERM signal, exited normally, signum is %s." % (signum))
        sys.exit(0)

    def loop(self):
        signal.signal(signal.SIGTERM, self.handle_sigterm)
        while True:
            agent_types = self.get_agent_status()
            for agent_type in agent_types:
                if self.check_if_agent_running(agent_type):
                    self.restart_agent(self.agent_name.get(agent_type))
            time.sleep(90)

if __name__ == '__main__':
    monitor = MonitorAgent()
    monitor.loop()
