# Copyright (C) 2015 VA Linux Systems Japan K.K.
# Copyright (C) 2015 YAMAMOTO Takashi <yamamoto at valinux co jp>
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

from oslo_log import log as logging
from oslo_utils import excutils
import ryu.app.ofctl.api # noqa, do not remove this.
from ryu.base import app_manager
from ryu.lib import hub
from ryu.ofproto import ofproto_v1_3
from apps.main import ovs_agent

LOG = logging.getLogger(__name__)


def agent_main_wrapper(ryu_app):
    try:
        ovs_agent.main(ryu_app)
    except Exception:
        with excutils.save_and_reraise_exception():
            LOG.exception("Agent main thread died of an exception")
    finally:
        # The following call terminates Ryu's AppManager.run_apps(),
        # which is needed for clean shutdown of an agent process.
        # The close() call must be called in another thread, otherwise
        # it suicides and ends prematurely.
        hub.spawn(app_manager.AppManager.get_instance().close)


class OVSAgentRyuApp(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def start(self):
        # Start Ryu event loop thread
        super(OVSAgentRyuApp, self).start()
        return hub.spawn(agent_main_wrapper, ryu_app=self, raise_error=True)
