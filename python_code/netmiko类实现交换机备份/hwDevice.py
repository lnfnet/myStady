from __future__ import print_function
from __future__ import unicode_literals
import time
import re
from netmiko.cisco_base_connection import CiscoBaseConnection
from netmiko.ssh_exception import NetMikoAuthenticationException
from netmiko import log


class HuaweiBase(CiscoBaseConnection):
    def session_preparation(self):
        """Prepare the session after the connection has been established."""
        self._test_channel_read()
        self.set_base_prompt()
        self.disable_paging(command="screen-length 0 temporary")
        # Clear the read buffer
        time.sleep(0.3 * self.global_delay_factor)
        self.clear_buffer()

    def config_mode(self, config_command="system-view"):
        """Enter configuration mode."""
return super(HuaweiBase, self).config_mode(config_command=config_command)
