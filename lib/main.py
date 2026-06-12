#  Copyright (C) 2023  Author1, Author2, Author3, Author4, Author5
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
#  Main script for the 1st LAAS-LAPLACE Hackathon
#
#  Author1:
#  Author2:
#  Author3:
#  Author4:
#  Author5:

import pyvisa
import threading
from queue import Queue
import time

import pandas as pd

from lib.scope_class import Oscilloscope
from lib.KEYTHLEY2000 import KEYTHLEY2000
from lib.NGL202 import NGL202

from owntech.Twist_Class import Twist_Device
from owntech import find_devices
import matplotlib.pyplot as plt

def main_app():
    """
    Main function to control and monitor the DUT.

    :param shared_data: Queue to share data between threads
    """
    # ------------ PyVISA setup --------------------
    rm = pyvisa.ResourceManager('@py')
    print(rm.list_resources())
    # ------------ Temperature DMM setup --------------------
    digit_voltage, digit_current, digit_temp1, digit_temp2 = measure_devices_init(rm)

    # ------------ Power Supply setup --------------------
    supply = supply_init(rm)

    # ------------ Oscilloscope setup --------------------
    scope_address = 'USB0::0x0699::0x0522::C062816::INSTR'
    osc = Oscilloscope(scope_address)
    print('Scope ID: {}\n'.format(osc.send_query('*IDN?')))

    # -------------- DUT setup ------------------

    DUT_vid = 0x2fe3
    DUT_pid = 0x0100

    DUT_ports = find_devices.find_twist_device_ports(DUT_vid, DUT_pid)
    print(DUT_ports)

    DUT = Twist_Device(twist_port=DUT_ports[0])

    # Dictionnary to store results
    res = {'Voltage':[], 'Current':[], 'Temp1':[], 'Temp2':[]}

    # Config supply ramp
    step_volt = 1 #in v
    start_volt = 0
    stop_volt = 4

    for x in range(start_volt, stop_volt + step_volt, step_volt):
        supply.set_channel(1)
        supply.set_voltage(x/2)
        supply.set_channel(2)
        supply.set_voltage(x/2)
        res['Voltage'].append(digit_voltage.measureVoltage())
        res['Current'].append(digit_current.measureCurrent())
        res['Temp1'].append(digit_temp1.getTemp())
        res['Temp2'].append(digit_temp2.getTemp())
        time.sleep(1)

    df = pd.DataFrame(res)
    df.to_csv('res_2024.csv', index=False)

    rm.close()

def measure_devices_init(rm):
    """
    Initialized the measurement devices of the test bench.

    :param rm: list of available devices in pyvisa
    """

    # Get measurement devices
    digit_voltage = KEYTHLEY2000(rm, 'GPIB0::3::INSTR')
    digit_current = KEYTHLEY2000(rm, 'GPIB0::1::INSTR')
    digit_temp1 = KEYTHLEY2000(rm, 'GPIB0::2::INSTR')
    digit_temp2 = KEYTHLEY2000(rm, 'GPIB0::4::INSTR')
    # Check
    digit_voltage.check(role="voltage_high", name='KEITHLEY INSTRUMENTS INC.,MODEL 2000,1053308,A19  /A02', port="A")
    digit_current.check(role="current_high", name='KEITHLEY INSTRUMENTS INC.,MODEL 2000,0972521,A17  /A02', port="A")
    digit_temp1.check(role="temp1", name='KEITHLEY INSTRUMENTS INC.,MODEL 2000,1102655,A19  /A02', port="A")
    digit_temp2.check(role="temp2", name='KEITHLEY INSTRUMENTS INC.,MODEL 2000,1308393,A20  /A02', port="A")
    digit_temp1.configTemp(rjunc=26)
    digit_temp2.configTemp(rjunc=26)
    print("init measurement devices OK")
    return digit_voltage, digit_current, digit_temp1, digit_temp2


def supply_init(rm):
    """
    Initializes the power supply

    :param rm: List of devices in pyvisa
    """

    rm = pyvisa.ResourceManager()
    print(rm.list_resources())
    supply = NGL202(rm, 'ASRL8::INSTR')
    supply.check(role="PSU", name="Rohde&Schwarz,NGL202,3638.3376k03/105048,04.000 002CBB20D8F", port="1")

    # Config DC supply
    supply.set_channel(1) #select the channel 1 to do the setup on this specific channel
    supply.enable_channel() #enable the channel (turn the green light for the channel)
    supply.set_min_voltage(0) #set the minimum voltage available (min in 0)
    supply.set_max_voltage(20) #set the maximum voltage available (max is 20.05)
    #supply.set_min_current(0) #set the minimum current available (min in 0)
    supply.set_max_current(3.01) #set the maximum current available (max is 6.01a bellow 6v and 3.01a from that point)
    supply.set_current(3)

    supply.set_channel(2)
    supply.enable_channel()
    supply.set_max_voltage(0)
    supply.set_max_voltage(20)
    #supply.set_min_current(0)
    supply.set_max_current(3.01)
    supply.set_current(3)
    print("init supply OK")
    return supply


def Oscilloscope_test_code(osc):
    """
    Test code for the Oscilloscope.

    :param osc: Oscilloscope object
    """
    # --------- Oscilloscope test code ------------------
    time, voltage = osc.get_data()

    # Save data to a CSV file
    csv_file = 'data.csv'
    osc.save_data_to_csv(csv_file)

    # Print data to the console
    osc.print_data()

    # Plot data using matplotlib
    plt.plot(time, voltage)
    plt.xlabel('Time (s)')
    plt.ylabel('Voltage (V)')
    plt.title('Oscilloscope Data')
    plt.grid()
    plt.show()

def DUT_example_code(DUT):
    """
    Example code to demonstrate the capabilities of the DUT.

    :param DUT: DUT object
    """
    message = DUT.sendCommand("IDLE")
    print(message)

    message = DUT.sendCommand("BUCK", "LEG2", "ON")

    print(message)
    message = DUT.sendCommand("BUCK", "LEG1", "ON")
    print(message)

    message = DUT.sendCommand("LEG", "LEG1", "ON")
    print(message)
    message = DUT.sendCommand("LEG", "LEG2", "ON")
    print(message)

    message = DUT.sendCommand("DEAD_TIME_RISING", "LEG1", 300)
    print(message)
    message = DUT.sendCommand("DEAD_TIME_FALLING", "LEG1", 100)
    print(message)

    message = DUT.sendCommand("DEAD_TIME_RISING", "LEG2", 300)
    print(message)
    message = DUT.sendCommand("DEAD_TIME_FALLING", "LEG2", 100)
    print(message)

    message = DUT.sendCommand("POWER_ON")
    print(message)

    message = DUT.sendCommand("DUTY", "LEG1", 0.5)
    print(message)
    message = DUT.sendCommand("DUTY", "LEG2", 0.5)
    print(message)

    message = DUT.sendCommand("PHASE_SHIFT", "LEG2", 0)
    print(message)

if __name__ == "__main__":
    main_app()
