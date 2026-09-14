"""
Copyright (c) 2021-2024 LAAS-CNRS

  This program is free software: you can redistribute it and/or modify
  it under the terms of the GNU Lesser General Public License as published by
  the Free Software Foundation, either version 2.1 of the License, or
  (at your option) any later version.

  This program is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU Lesser General Public License for more details.

  You should have received a copy of the GNU Lesser General Public License
  along with this program.  If not, see <https://www.gnu.org/licenses/>.

SPDX-License-Identifier: LGPL-2.1
"""

"""
@brief  This is a class for the factory test of Twitst 1.4.1

@author Luiz Villa <luiz.villa@laas.fr>
@author Guillaume Arthaud <guillaume.arthaud@laas.fr>
"""

from serial.tools import list_ports

def find_twist_device_ports(target_vid=0x2fe3, target_pid=0x0100, num_devices = 1):
    found_devices = []  # List to store the ports for the found devices

    # Get a list of all available ports
    ports = list_ports.comports()

    # Iterate through each port to find the target devices
    for port in ports:
        # Check if the port matches the target device based on VID and PID
        if port.vid == target_vid and port.pid == target_pid:
            found_devices.append(port.device)
            # If both devices are found, return their ports
            if len(found_devices) == num_devices:
                return found_devices

    # If the loop completes without finding both devices, return an empty list
    return []

target_vid = 0x2fe3
target_pid = 0x0100
num_devices = 1

target_ports = find_twist_device_ports(target_vid, target_pid, num_devices)

if len(target_ports) == num_devices:
    print("Ports for devices with target VID and PID:", target_ports)
else:
    print("Unable to find ports for both devices.")