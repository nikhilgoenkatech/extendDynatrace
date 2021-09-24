from ruxit.api.base_plugin import RemoteBasePlugin
from ruxit.api.data import PluginProperty
import math
import logging
from enum import Enum

logger = logging.getLogger(__name__)

class RemoteExamplePlugin(RemoteBasePlugin):

    class State(Enum):
        DOWNTIME = 0
        MAINTENANCE = 1
        WORKING = 2

    def initialize(self, **kwargs):
        self.url = self.config.get("url", "http://127.0.0.1:8976")
        self.user = self.config.get("auth_user", "admin")
        self.password = self.config.get("auth_password", "admin")
        self.alert_interval = self.config.get("alert_interval", 10)
        self.event_interval = self.config.get("event_interval", 3)
        self.relative_interval = self.config.get("relative_interval", 60)
        self.state_interval = self.config.get("state_interval", 60)

        self.alert_iterations = 0
        self.event_iterations = 0
        self.relative_iterations = 0
        self.absolute_iterations = 0
        self.state_iterations = 0

        self.current_entries = 1
        self.archived_entries = 0

    def query(self, **kwargs):
        group_name = self.get_group_name()
        topology_group = self.topology_builder.create_group(group_name, group_name)
        topology_group.per_second("service.querries_per_second", self.get_num_querries())
        topology_group.report_property(key="group_property", value="group_property_value")
        devices = self.get_device_names()
        port = 80
        for device_name in devices:
            topology_device = topology_group.create_device(device_name, device_name)
            topology_device.state_metric("service.state_5", self.get_state_metric())
            topology_device.absolute("databases.total_num_entities", self.get_device_entries())
            table_size = 100
            topology_device.relative("databases.replicated_entries", self.get_archived_entries())
            for table in self.get_tables_for_device(device_name):
                topology_device.absolute("databases.table_size", table_size, {"table_name": table})
                table_size = table_size + 100
            if self.should_create_event():
                topology_device.report_custom_info_event("Custom event!")
                topology_device.report_performance_event("Performance problem description", "Performance problem", {})
            topology_device.report_property(key="device_property", value="device_property_value")
            topology_device.add_endpoint("127.0.0.1", port)
            port += 1


    def get_group_name(self):
        return "ExampleGroup"

    def get_state_metric(self):
        if self.state_iterations >= self.state_interval * 3:
            self.state_iterations = 0
        state = RemoteExamplePlugin.State(int(self.state_iterations / self.state_interval))
        self.state_iterations = self.state_iterations + 1
        return state.name

    def get_num_querries(self):
        self.alert_iterations = self.alert_iterations + 1
        if self.alert_iterations > self.alert_interval:
            if self.alert_iterations > self.alert_interval + 3:
                self.alert_iterations = 0
            return 1
        return 7

    def get_device_names(self):
        return ["DeviceOne", "DeviceTwo"]

    def get_tables_for_device(self, device):
        if device == "DeviceOne":
            return ["d1_t1", "d1_t2", "d1_t3", "d2_t4"]
        return ["d2_t1", "d2_t2", "d2_t3", "d2_t4", "d2_t5", "d2_t6"]

    def get_device_entries(self):
        if self.absolute_iterations == 360:
            self.absolute_iterations = 0
        self.absolute_iterations = self.absolute_iterations + 1
        return self.current_entries + math.sin(math.radians(self.absolute_iterations))

    def get_archived_entries(self):
        self.relative_iterations = self.relative_iterations + 1
        if self.relative_iterations > self.relative_interval:
            self.relative_iterations = 0
            self.archived_entries = self.archived_entries + 1
        return self.archived_entries

    def should_create_event(self):
        self.event_iterations = self.event_iterations + 1
        if self.event_iterations > self.event_interval:
            self.event_iterations = 0
            return True
        return False

