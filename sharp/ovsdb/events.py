

from ovsdbapp.backend.ovs_idl import event as row_event
from common.constants import PORT_CREATE_EVENT, PORT_UPDATE_EVENT, PORT_DELETE_EVENT,\
    BRIDGE_CREATE_EVENT, BRIDGE_UPDATE_EVENT, BRIDGE_DELETE_EVENT


class PortEvent(row_event.RowEvent):
    """Port create update delete event."""

    def __init__(self, driver):
        self.driver = driver
        table = 'Port'
        events = (self.ROW_CREATE, self.ROW_UPDATE, self.ROW_DELETE)
        super(PortEvent, self).__init__(events, table, None)
        self.event_name = 'PortEvent'

    def run(self, event, row, old):
        port_event = None
        if event == row_event.RowEvent.ROW_CREATE:
            port_event = PORT_CREATE_EVENT
        elif event == row_event.RowEvent.ROW_UPDATE:
            port_event = PORT_UPDATE_EVENT
        elif event == row_event.RowEvent.ROW_DELETE:
            port_event = PORT_DELETE_EVENT

        if self.driver:
            self.driver.process_port_events(port_event, row.name)


class BridgeEvent(row_event.RowEvent):
    """Bridge create update delete event."""

    def __init__(self, driver):
        self.driver = driver
        table = 'Bridge'
        events = (self.ROW_CREATE, self.ROW_UPDATE, self.ROW_DELETE)
        super(BridgeEvent, self).__init__(events, table, None)
        self.event_name = 'BridgeEvent'

    def run(self, event, row, old):
        bridge_event = None
        if event == row_event.RowEvent.ROW_CREATE:
            bridge_event = BRIDGE_CREATE_EVENT
        elif event == row_event.RowEvent.ROW_UPDATE:
            bridge_event = BRIDGE_UPDATE_EVENT
        elif event == row_event.RowEvent.ROW_DELETE:
            bridge_event = BRIDGE_DELETE_EVENT

        if self.driver:
            self.driver.process_bridge_events(bridge_event, row.name)
