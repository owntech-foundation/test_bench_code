#! python3

import json
import os
from pyexpat import errors
import sys
import time
import math
from datetime import datetime
from typing import cast, Any

import serial.serialutil
import pyvisa as visa
import numpy as np
import matplotlib.pyplot as plt

from comm_protocol.src import find_devices
from comm_protocol.src.Shield_Class import Shield_Device

import lib.tools as tools


# Expand module path if needed
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../"))
sys.path.insert(0, parent_dir)

class Supervisor:
    """
    A Supervisor class that loads configuration parameters from a JSON file
    and provides methods for test bench operations:
      1) Connect with devices (DMM, microcontroller, power supply, oscilloscope).
      2) Run test algorithms (phase shift or duty sweep, etc.).
      3) Handle data (plotting, CSV export, etc.).
    """

    def __init__(self, config_path: str = "parameters.json", sdm_voltage=None, sdm_current=None, sds_oscilloscope=None, tdk_power_supply=None, ressource_manager: visa.ResourceManager = None): 
        """
        Constructor to initialize the Supervisor class.
        
        1) Reads a JSON configuration file that contains all parameters needed for the tests.
        2) Stores these parameters as instance attributes.
        3) Creates a single PyVISA Resource Manager to manage instrument communication.

        Parameters
        ----------
        config_path : str, optional
            Path to the JSON file containing configuration parameters. 
            Defaults to "parameters.json".
        """
        # 1. Load JSON configuration
        with open(config_path, 'r') as f:
            self.config = json.load(f)

        self.result_output_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            self.config["dataOutputFolder"])
        if not os.path.exists(self.result_output_path):
            os.makedirs(self.result_output_path)
        print(self.result_output_path)
        
        # 2. Store parameters in instance attributes (delays, PWM settings, limits, etc.)
        # Replace these lines in the constructor:

        self.multimeter_current = sdm_current
        self.multimeter_voltage = sdm_voltage
        self.base_oscilloscope = sds_oscilloscope
        self.power_supply = tdk_power_supply
        self.microcontroller = None  

        self.base_oscilloscope.result_output_path = self.result_output_path

        self.delay = self.config['delay']
        self.delay2 = self.config['delay2']
        self.delay3 = self.config['delay3']
        self.delay_com = self.config['delay_com']

        # self.dmm_init_delay = self.config.get('dmm_init_delay', 2)
        # self.dmm_cmd_delay = self.config.get('dmm_cmd_delay', 0.1)
        # self.dmm_current_nplc = self.config.get('dmm_current_nplc', 0.5)
        # self.dmm_voltage_nplc = self.config.get('dmm_voltage_nplc', 0.5)
        # self.dmm_current_sample_count = self.config.get('dmm_current_sample_count', 3)
        # self.dmm_voltage_sample_count = self.config.get('dmm_voltage_sample_count', 3)
        # self.power_supply_output_delay = self.config.get('power_supply_output_delay', 0.3)
        # self.power_supply_ramp_delay = self.config.get('power_supply_ramp_delay', 0.1)

        self.DutyPWM = self.config['DutyPWM']
        self.frequencyPWM = self.config['frequencyPWM']
        self.DeadTimePWM = self.config['DeadTimePWM']
        self.InitialPhaseShiftPWM = self.config['InitialPhaseShiftPWM']

        # self.VoltageLimit = self.config['VoltageLimit']
        # self.CurrentLimit = self.config['CurrentLimit']
        # self.VoltageWrite = self.config['VoltageWrite']
        # self.timestep = self.config['timestep']
        # self.voltage_step = self.config['voltage_step']
        self.PhaseInit = self.config['PhaseInit']
        self.PhaseFinal = self.config['PhaseFinal']
        self.PhaseStep = self.config['PhaseStep']
        # self.nb_points_i = self.config['nbPointsI']
        # self.nb_points_v = self.config['nbPointsV']

        self.DutyInit = self.config['DutyInit']
        self.DutyFinal = self.config['DutyFinal']
        self.DutyStep = self.config['DutyStep']

        # self.hv_power_supply_name = self.config['HVpowerSupply']
        # self.dmm_for_current_name = self.config['DMMforCurrent']
        # self.dmm_for_voltage_name = self.config['DMMforVoltage']
        # self.oscilloscope_name = self.config['AddressOSCILLO']

        # self.Sequence = self.config['Sequence']
        # self.delayOscillo = self.config['delayOscillo']
        # self.scopeMeasure = self.config['ScopeAutoMeasure']

        # self.SaveEachFramePICTURE = self.config['SaveEachFramePICTURE']
        # self.SaveEachFrameDATA = self.config['SaveEachFrameDATA']

        self.microcontroller_vid = self.config['shield_vid']
        self.microcontroller_pid = self.config['shield_pid']


        # 3. Create a single resource manager instance

        # Create PyVISA Resource Manager
        if ressource_manager is None:
            #self.rm = visa.ResourceManager()
            self.rm = None
        else:
            self.rm = ressource_manager
            print("RM supervisor")


        # We store the microcontroller instance here (None if not opened yet)
        # Attributes to store open device resources
        # self.hv_power_supply = None
        # self.dmm_for_current = None
        # self.dmm_for_voltage = None
        # self.oscilloscope = None
        # self.microcontroller = None




    # -------------------------------------------------
    # PART 1: Device Management (Open/Close)
    # -------------------------------------------------
    def open_all_devices(self):
        """
        Opens all known instruments (power supply, DMMs, oscilloscope) 
        and stores the resource objects in instance attributes.
        """
        
        self.multimeter_current.open_dmm_for_current()
        time.sleep(0.5)
        self.multimeter_voltage.open_dmm_for_voltage()
        time.sleep(0.5)
        self.power_supply.open_hv_power_supply()
        time.sleep(2)
        self.open_microcontroller()
        time.sleep(0.5)

        self.base_oscilloscope.open_oscilloscope()
        time.sleep(0.5)

    def setup_all_devices(self):
        """
        Setups all devices (DMMs, oscilloscope, microcontroller & power supply).
        """
        self.microcontroller_setup() #Setup µC before oscilloscope to restart owntech board and avoid errors 
        time.sleep(0.5)

        self.base_oscilloscope.oscilloscope_setup()
        time.sleep(0.5)


        self.multimeter_current.dmm_setup_current_testbench()
        time.sleep(0.5)
        self.multimeter_voltage.dmm_setup_voltage_testbench()
        time.sleep(self.multimeter_current.dmm_init_delay) # Wait DMM initialized
        

        
        self.power_supply.setup_hv_power_supply()
        time.sleep(0.5)
        

    def close_all_devices(self):
        """
        Closes all opened instruments and sets their references to None.
        """
        errors = []
        try:
            self.power_supply.close_hv_power_supply()
        except Exception as e:
            errors.append(f"Failed to close HV power supply: {e}")
        try:
            self.multimeter_current.close_dmm_for_current()
        except Exception as e:
            errors.append(f"Failed to close DMM for current: {e}")
        try:
            self.multimeter_voltage.close_dmm_for_voltage()
        except Exception as e:
            errors.append(f"Failed to close DMM for voltage: {e}")
        try:
            self.base_oscilloscope.close_oscilloscope()
        except Exception as e:
            errors.append(f"Failed to close oscilloscope: {e}")
        try:
            self.close_microcontroller()
        except Exception as e:
            errors.append(f"Failed to close microcontroller: {e}")

        if errors:
            raise RuntimeError(
                "One or more devices failed to close:\n" + "\n".join(errors)
            )
        else:
            print("All devices closed successfully. Test complete!")
            

    def close_rm_manager(self):
        self.rm.close()
        time.sleep(0.5)
        del self.rm


    def open_microcontroller(self):
        """
        Finds and opens the microcontroller based on VID/PID from the JSON config.
        Stores the instance in self.microcontroller.
        """
        if self.microcontroller is not None:
            print("Microcontroller is already opened.")
            return

        # Find the microcontroller ports
        ports = find_devices.find_shield_device_ports(self.microcontroller_vid, self.microcontroller_pid)
        if not ports:
            raise RuntimeError(f"No microcontroller found for VID=0x{self.microcontroller_vid:04X}, "
                               f"PID=0x{self.microcontroller_pid:04X}.")

        self.microcontroller = Shield_Device(shield_port=ports[0], shield_type='TWIST')
        print(f"Opened microcontroller on port {ports[0]}")

    def close_microcontroller(self):
        """
        Closes the microcontroller if it is open.
        """
        if self.microcontroller is not None:
            try:
                print("Closing microcontroller.")
                # No explicit close() method in Shield_Device, so just set to None
            except Exception as e:
                print(f"Error closing microcontroller: {e}")
            finally:
                self.microcontroller = None
        else:
            print("Microcontroller is not opened.")


    # -------------------------------------------------
    # PART 3: Instrument Identification
    # -------------------------------------------------
    def list_instruments(self):
        """
        Lists and queries all instruments found by the PyVISA Resource Manager.
        """
        resources = self.rm.list_resources()
        print(resources)

        for instrument in resources:
            print(f"'{instrument}': ", end=' ')
            try:
                dev = self.rm.open_resource(instrument)
                print(type(dev), end=' ')
                print(dev.query("*IDN?"), end='\n')
                dev.close()
            except visa.errors.VisaIOError:
                print('INSTRUMENT ERROR\n')
            except serial.serialutil.SerialException:
                print('Dummy Serial')


    # -------------------------------------------------
    # PART 5: Microcontroller Phase / Duty Functions
    # -------------------------------------------------
    def microcontroller_setup(self):
        self.microcontroller_send_command("LEG", "LEG1", "ON")
        self.microcontroller_send_command("LEG", "LEG2", "ON")
        self.microcontroller_send_command("POWER_ON")

        # We assume the JSON config defines sup.DutyPWM, sup.frequencyPWM, sup.DeadTimePWM, etc.
        self.microcontroller_send_command("DUTY", "LEG1", self.DutyPWM)
        self.microcontroller_send_command("DUTY", "LEG2", self.DutyPWM)

        self.microcontroller_send_command("FREQUENCY", "LEG1", self.frequencyPWM)
        self.microcontroller_send_command("DEAD_TIME_RISING", "LEG2", self.DeadTimePWM)
        self.microcontroller_send_command("DEAD_TIME_RISING", "LEG1", self.DeadTimePWM)
        self.microcontroller_send_command("DEAD_TIME_FALLING", "LEG2", self.DeadTimePWM)
        self.microcontroller_send_command("DEAD_TIME_FALLING", "LEG1", self.DeadTimePWM)

        self.microcontroller_send_command("PHASE_SHIFT", "LEG2", self.InitialPhaseShiftPWM)


    def microcontroller_send_command(self, action: str, *args, delay=0.2):
        """
        Sends a command to the microcontroller using its sendCommand() method.

        Parameters
        ----------
        action : str
            The action to perform (e.g. "PHASE_SHIFT", "DUTY", "POWER_ON").
        *args : tuple
            Additional arguments for that action (e.g., leg identifier, numeric values).
        delay : float
            Time to wait after sending the command. Defaults to 0.2 seconds.
        """
        if self.microcontroller is None:
            raise ValueError("Microcontroller is not opened. Call open_microcontroller() first.")

        msg = self.microcontroller.sendCommand(action, *args, delay=delay)
        print(f"Microcontroller command => {action}, args={args}, msg={msg}")
        return msg

    def microcontroller_sweep_phase_shift(self, phase_init, phase_final, step):
        """
        Sweeps the phase shift on the microcontroller from 'phase_init' to 'phase_final'
        in increments of 'step'.
        """
        if self.microcontroller is None:
            raise ValueError("Microcontroller is not opened.")

        for phase_val in range(phase_init, phase_final, step):
            msg = self.microcontroller.sendCommand("PHASE_SHIFT", "LEG2", phase_val, delay=self.delay_com)
            print(f"Set phase shift={phase_val}, msg={msg}")

    def microcontroller_repeat_get_line(self, num_times):
        """
        Calls microcontroller.getLine() multiple times and prints the result each time.
        """
        if self.microcontroller is None:
            raise ValueError("Microcontroller is not opened.")

        for _ in range(num_times):
            msg = self.microcontroller.getLine()
            print(msg)

    def microcontroller_sweep_duty_shift(self, duty_init, duty_final, duty_step):
        """
        Sweeps the duty cycle on the microcontroller from 'duty_init' to 'duty_final'
        and then back down, in increments of 'duty_step'.
        """
        if self.microcontroller is None:
            raise ValueError("Microcontroller is not opened.")

        print("Duty Sweep mode ON")
        # Ramp up
        for duty_val in range(duty_init, duty_final, duty_step):
            msg = self.microcontroller.sendCommand("DUTY", "LEG2", duty_val / 1000, delay=self.delay_com)
            print(f"Set duty={duty_val/1000}, msg={msg}")

        # Ramp down
        for duty_val_down in range(duty_final, duty_init - duty_step, -duty_step):
            msg = self.microcontroller.sendCommand("DUTY", "LEG2", duty_val_down / 1000, delay=self.delay_com)
            print(f"Set duty={duty_val_down/1000}, msg={msg}")
