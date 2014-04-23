#!/usr/bin/env python
import dbus
import avahi
import threading
import log as logging


LOG = logging.getLogger(__name__)


class AvahiDiscoverError(Exception):
    pass

class AvahiServerThread(threading.Thread):
    def __init__(self, service_name, service_port, \
            service_type="_cloudlet._udp", text=""):
        # use UDP service type beacuse tcp does not type does not broadcast
        # message to multiple nic.
        self.service_name = service_name
        self.service_port = service_port
        self.service_type = service_type
        self.text = text
        self.server = None
        self.group = None
        self.stop = threading.Event()
        self.is_published = False
        threading.Thread.__init__(self, target=self.run)

    def run(self):
        # keep trying to publish Avahi discovery message
        self.is_published = False
        while (self.is_published == False):
            try:
                self.publish()
                LOG.info("[Avahi] Start Avahi Server")
                self.is_published = True
            except dbus.exceptions.DBusException as e:
                msg = "Cannot connect to avahi-daemon. Please start avahi-daemon"
                LOG.warning(msg)
            if self.stop.wait(1) == True:
                break

        # wait until terminate thread
        while True:
            if self.stop.wait(10):
                break
        
        if self.is_published and self.group is not None:
            try:
                self.group.Reset()
                self.group.Free()
            except dbus.exceptions.DBusException as e:
                pass

    def server_state_changed(self, state):
        if state == avahi.SERVER_COLLISION:
            LOG.warning("Server name collision")
            self.remove_service()
        elif state == avahi.SERVER_RUNNING:
            self.add_service()
        else:
            LOG.warning("unexpected server state")
            self.remove_service()

    def add_service(self):
        if self.group is None:
            self.group = dbus.Interface(
                    self.bus.get_object(
                        avahi.DBUS_NAME, self.server.EntryGroupNew()
                        ),
                    avahi.DBUS_INTERFACE_ENTRY_GROUP)
            #self.group.connect_to_signal('StateChanged', self.entry_group_state_changed)
        LOG.info("[Avahi] Adding service '%s' of type '%s' ..." % (self.service_name, self.service_type))

        domain = ""
        host = ""
        self.group.AddService(
                avahi.IF_UNSPEC,    #interface
                avahi.PROTO_UNSPEC, #protocol
                dbus.UInt32(0),                  #flags
                self.service_name, self.service_type,
                domain, host,
                dbus.UInt16(self.service_port),
                avahi.string_array_to_txt_array(self.text))
        self.group.Commit()

    def remove_service(self):
        if self.group is not None:
            self.group.Reset()

    def publish(self):
        self.bus = dbus.SystemBus()
        self.server = dbus.Interface(
                        self.bus.get_object(
                                avahi.DBUS_NAME,
                                avahi.DBUS_PATH_SERVER),
                        avahi.DBUS_INTERFACE_SERVER)
        #self.server.connect_to_signal("StateChanged", self.server_state_changed)
        #self.server_state_changed(self.server.GetState())
        self.add_service()
        self.is_published = True

    def terminate(self):
        self.stop.set()
        


def test():
    service = AvahiServerThread(service_name="cloudlet service", service_port=11111)
    service.start()
    while True:
        raw_input("Press any key to unpublish the service ")
        break
    service.terminate()


if __name__ == "__main__":
    test()


