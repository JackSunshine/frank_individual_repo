# Copyright (C) 2014,2015 VA Linux Systems Japan K.K.
# Copyright (C) 2014,2015 YAMAMOTO Takashi <yamamoto at valinux co jp>
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""
* references
** OVS agent https://wiki.openstack.org/wiki/Ovs-flow-logic
"""

import netaddr

import logging
from ryu.lib.packet import in_proto
from ryu.lib.packet import ether_types

from common import constants

from openflow import ovs_bridge


LOG = logging.getLogger(__name__)


class IcsNormalBridge(ovs_bridge.OVSAgentBridge):
    """ics normal bridge specific logic."""

    def setup_default_table(self):
        self.install_dhcp_flow()
        self.install_normal(table_id=constants.TRANSIENT_TABLE, priority=0)
        self.setup_canary_table()

    def setup_canary_table(self):
        self.install_drop(constants.CANARY_TABLE)

    def check_canary_table(self):
        try:
            flows = self.dump_flows(constants.CANARY_TABLE)
        except RuntimeError:
            LOG.exception("Failed to communicate with the switch")
            return constants.OVS_DEAD
        return constants.OVS_NORMAL if flows else constants.OVS_RESTARTED

    def install_dhcp_flow(self):
        (_dp, ofp, ofpp) = self._get_dp()
        match = ofpp.OFPMatch(eth_type=ether_types.ETH_TYPE_IP,
                              ip_proto=in_proto.IPPROTO_UDP,
                              udp_src=constants.DHCP_CLIENT_PORT,
                              udp_dst=constants.DHCP_SERVER_PORT)
        self.install_packet_to_controller(table_id=0,
                                          priority=100,
                                          match=match)

