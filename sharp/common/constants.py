






# known port
DHCP_CLIENT_PORT = 68
DHCP_SERVER_PORT = 67


OF_CONNECT_TIMEOUT = 30
OF_REQUEST_TIMEOUT = 10
DEFAULT_OVSDB_TIMEOUT = 10
BRIDGE_MAC_TABLE_SIZE = 50000



BRIDGE_CREATE_EVENT = "create"
BRIDGE_UPDATE_EVENT = "update"
BRIDGE_DELETE_EVENT = "delete"

PORT_CREATE_EVENT = "create"
PORT_UPDATE_EVENT = "update"
PORT_DELETE_EVENT = "delete"


OPENFLOW_CONTROLLER = "tcp:127.0.0.1:6653"
OVSDB_CONNECTION = "tcp:127.0.0.1:6640"

# ovs datapath types
OVS_DATAPATH_SYSTEM = 'system'
OVS_DATAPATH_NETDEV = 'netdev'
OVS_DPDK_VHOST_USER = 'dpdkvhostuser'
OVS_DPDK_VHOST_USER_CLIENT = 'dpdkvhostuserclient'

OVS_DPDK_PORT_TYPES = [OVS_DPDK_VHOST_USER, OVS_DPDK_VHOST_USER_CLIENT]

# default ovs vhost-user socket location
VHOST_USER_SOCKET_DIR = '/var/run/openvswitch'

MAX_DEVICE_RETRIES = 5

# OpenFlow version constants
OPENFLOW10 = "OpenFlow10"
OPENFLOW11 = "OpenFlow11"
OPENFLOW12 = "OpenFlow12"
OPENFLOW13 = "OpenFlow13"
OPENFLOW14 = "OpenFlow14"
OPENFLOW15 = "OpenFlow15"



# Represent ovs status
OVS_RESTARTED = 0
OVS_NORMAL = 1
OVS_DEAD = 2

# --- Bridge pipeline ----

LOCAL_SWITCHING = 0

CANARY_TABLE = 23

# Table for ARP poison/spoofing prevention rules
ARP_SPOOF_TABLE = 24

# Table for MAC spoof filtering
MAC_SPOOF_TABLE = 25

# Table to decide whether further filtering is needed
TRANSIENT_TABLE = 60