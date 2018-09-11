
import tenacity
import logging
from ovsdbapp.backend.ovs_idl import idlutils
from ovsdbapp.backend.ovs_idl import connection as idl_connection
from ovsdbapp.schema.open_vswitch import impl_idl as idl_ovs
from ovsdbapp import event
from ovsdb.events import PortEvent, BridgeEvent


log = logging.getLogger('ovsdb')


class OvsDbNotifyHandler(event.RowEventHandler):
    def __init__(self, driver):
        super(OvsDbNotifyHandler, self).__init__()
        self.driver = driver


class BaseOvsIdl(idl_connection.OvsdbIdl):

    def __init__(self, driver, remote, schema):
        super(BaseOvsIdl, self).__init__(remote, schema)
        self.driver = driver
        self.notify_handler = OvsDbNotifyHandler(driver)
        self.event_lock_name = "ovs_event_lock"

    def notify(self, event, row, updates=None):
        # Do not handle the notification if the event lock is requested,
        # but not granted by the ovsdb-server.
        if self.is_lock_contended:
            return
        self.notify_handler.notify(event, row, updates)

    def post_connect(self):
        """When the ovs idl client connects to the ovsdb-server, it gets
        a dump of all events. We don't need to process them
        because there will be sync up at startup. After that, we will watch
        the events to make notify work."""
        pass


class OvsNotificationIdl(BaseOvsIdl):

    def __init__(self, driver, remote, schema='Open_vSwitch'):
        helper = idlutils.get_schema_helper(remote, schema_name=schema)
        helper.register_all()
        super(OvsNotificationIdl, self).__init__(driver, remote, helper)

        # it gets a dump of all events when connected to ovsdb-server,
        # if you watch events here.
        self._port_event = PortEvent(self.driver)
        self._bridge_event = BridgeEvent(self.driver)
        self.notify_handler.watch_events([self._port_event,
                                          self._bridge_event])


class OvsdbExtendedIdl(idl_ovs.OvsdbIdl):

    def __init__(self, connection):
        super(OvsdbExtendedIdl, self).__init__(connection)


class OvsdbClient(object):

    ovsdb_client = None

    def __init__(self, driver, connection):
        self.driver = driver
        self.connection = connection

    # Retry forever to get the OVS IDLs. Wait 2^x * 1 seconds between
    # each retry, up to 180 seconds, then 180 seconds afterwards.
    # The ovsdbapp will try to reconnect to ovsdb-server with 3 times
    # at 30 second intervals(timeout) if the connection was interrupted
    # during running.
    @classmethod
    def get_client(cls, driver, connection):
        if not cls.ovsdb_client:
            ovs_idl = OvsNotificationIdl(driver, connection)

            @tenacity.retry(
                wait=tenacity.wait_exponential(max=180),
                reraise=True)
            def get_connection(cls):
                log.info('Getting OVSDB IDL with retry')
                return cls(connection.Connection(ovs_idl, timeout=30))

            cls.ovsdb_client = get_connection(OvsdbExtendedIdl)

        return cls.ovsdb_client
