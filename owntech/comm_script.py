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

SPDX-License-Identifier: LGLPV2.1
"""

"""
@brief  This is a communcication script that deploys a PV emulator with
        hardware-in-the-loop with a Twitst 1.4.1

@author Luiz Villa <luiz.villa@laas.fr>
@author Thomas Walter <thomas.walter@laas.fr>
@author Guillaume Arthaud <guillaume.arthaud@laas.fr>
@author Amalie Alchami <amalie.alchami@utc.fr>
"""

import serial
import sys
sys.path.append('./owntech/lib/USB/comm_protocol/src/')

from owntech.lib.USB.comm_protocol.src import find_devices
from  owntech.lib.USB.comm_protocol.src.Shield_Class import Shield_Device

import matplotlib.pyplot as plt
import matplotlib.animation as animation

import xmlrpc.client as xml
import time
import matplotlib.pyplot as plt
import numpy as np

leg_to_test = "LEG1"                               #leg to be tested in this script
reference_names = ["V1","V2","VH","I1","I2","IH"]  #names of the sensors of the board

shield_vid = 0x2fe3
shield_pid = 0x0101

Shield_ports = find_devices.find_shield_device_ports(shield_vid, shield_pid)
print(Shield_ports)

Shield = Shield_Device(shield_port= Shield_ports[0])


# ---------------HARDWARE IN THE LOOP PV EMULATOR CODE ------------------------------------
message1 = Shield.sendCommand("IDLE")
print(message1)

message = Shield.sendCommand("POWER_ON")
print(message)

message = Shield.sendCommand("POWER_OFF")
print(message)

message = Shield.sendCommand("DUTY", "LEG1", 0.1)
print(message)

message = Shield.sendCommand("DUTY", "LEG2", 0.1)
print(message)

message = Shield.sendCommand("FREQUENCY", 30000)
print(message)

message = Shield.sendCommand("DEAD_TIME_RISING", "LEG2", 10)
print(message)

message = Shield.sendCommand("DEAD_TIME_FALLING", "LEG2", 10)
print(message)

message = Shield.sendCommand("DUTY", "LEG2", 0.1)
print(message)

message = Shield.sendCommand("PHASE_SHIFT", "LEG2", 50)
print(message)

