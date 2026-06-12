#! python3
#! python3

import json
import os
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
import lib.Oscillo_v1b as controloscillo


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

    def __init__(self, config_path: str = "parameters.json"):
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

        self.delay = self.config['delay']
        self.delay2 = self.config['delay2']
        self.delay3 = self.config['delay3']
        self.delay_com = self.config['delay_com']
        self.dmm_init_delay = self.config.get('dmm_init_delay', 2)
        self.dmm_cmd_delay = self.config.get('dmm_cmd_delay', 0.1)
        self.dmm_current_nplc = self.config.get('dmm_current_nplc', 0.5)
        self.dmm_voltage_nplc = self.config.get('dmm_voltage_nplc', 0.5)
        self.dmm_current_sample_count = self.config.get('dmm_current_sample_count', 3)
        self.dmm_voltage_sample_count = self.config.get('dmm_voltage_sample_count', 3)
        self.power_supply_output_delay = self.config.get('power_supply_output_delay', 0.3)
        self.power_supply_ramp_delay = self.config.get('power_supply_ramp_delay', 0.1)

        self.DutyPWM = self.config['DutyPWM']
        self.frequencyPWM = self.config['frequencyPWM']
        self.DeadTimePWM = self.config['DeadTimePWM']
        self.InitialPhaseShiftPWM = self.config['InitialPhaseShiftPWM']

        self.VoltageLimit = self.config['VoltageLimit']
        self.CurrentLimit = self.config['CurrentLimit']
        self.VoltageWrite = self.config['VoltageWrite']
        self.timestep = self.config['timestep']
        self.voltage_step = self.config['voltage_step']
        self.PhaseInit = self.config['PhaseInit']
        self.PhaseFinal = self.config['PhaseFinal']
        self.PhaseStep = self.config['PhaseStep']
        self.nb_points_i = self.config['nbPointsI']
        self.nb_points_v = self.config['nbPointsV']

        self.DutyInit = self.config['DutyInit']
        self.DutyFinal = self.config['DutyFinal']
        self.DutyStep = self.config['DutyStep']

        self.hv_power_supply_name = self.config['HVpowerSupply']
        self.dmm_for_current_name = self.config['DMMforCurrent']
        self.dmm_for_voltage_name = self.config['DMMforVoltage']
        self.oscilloscope_name = self.config['AddressOSCILLO']

        self.Sequence = self.config['Sequence']
        self.delayOscillo = self.config['delayOscillo']
        self.scopeMeasure = self.config['ScopeAutoMeasure']

        self.SaveEachFramePICTURE = self.config['SaveEachFramePICTURE']
        self.SaveEachFrameDATA = self.config['SaveEachFrameDATA']

        self.microcontroller_vid = self.config['shield_vid']
        self.microcontroller_pid = self.config['shield_pid']


        # 3. Create a single resource manager instance
        self.rm = visa.ResourceManager()

        # We store the microcontroller instance here (None if not opened yet)
        # Attributes to store open device resources
        self.hv_power_supply = None
        self.dmm_for_current = None
        self.dmm_for_voltage = None
        self.oscilloscope = None
        self.microcontroller = None

    # -------------------------------------------------
    # PART 1: Device Management (Open/Close)
    # -------------------------------------------------
    def open_all_devices(self):
        """
        Opens all known instruments (power supply, DMMs, oscilloscope) 
        and stores the resource objects in instance attributes.
        """
        
        self.open_dmm_for_current()
        time.sleep(0.5)
        self.open_dmm_for_voltage()
        time.sleep(0.5)
        self.open_hv_power_supply()
        time.sleep(0.5)
        self.open_microcontroller()
        time.sleep(0.5)
        self.open_oscilloscope()
        time.sleep(0.5)


    def close_all_devices(self):
        """
        Closes all opened instruments and sets their references to None.
        """
        self.close_hv_power_supply()
        self.close_dmm_for_current()
        self.close_dmm_for_voltage()
        self.close_oscilloscope()
        self.close_microcontroller()
        
    def close_rm_manager(self):
        self.rm.close()
        time.sleep(0.5)
        del self.rm

    def open_hv_power_supply(self):
        """
        Opens the HV power supply if not already open.
        """
        if self.hv_power_supply is not None:
            print("HV power supply is already opened.")
            return
        try:
            self.hv_power_supply = self.rm.open_resource(self.hv_power_supply_name, query_delay=0.5)
            # Ajout Nico - à tester
            self.hv_power_supply.baud_rate = 9600 # 300
##            self.hv_power_supply.write_termination = ''
##            self.hv_power_supply.read_termination = '\r\n'
##            self.hv_power_supply.set_visa_attribute(constants.VI_ATTR_ASRL_FLOW_CNTRL, constants.VI_ASRL_FLOW_XON_XOFF)
##            self.hv_power_supply.stop_bits = constants.StopBits.one
##            self.hv_power_supply.parity = constants.Parity.none
##            self.hv_power_supply.data_bits = 8
            self.hv_power_supply.write('INSTrument:NSELect  1')
            print(f"Opened HV power supply => {self.hv_power_supply_name}")
##            # Clear and flush buffer
##            self.hv_power_supply.flush()
##            time.sleep(0.5)
##            self.hv_power_supply.clear()
##            time.sleep(0.5)
##            print('Flushed HV power supply')
        except Exception as e:
            print(f"Failed to open HV power supply => {self.hv_power_supply_name}: {e}")

    def close_hv_power_supply(self):
        """
        Closes the HV power supply if it is open.
        """
        if self.hv_power_supply is not None:
            try:
                self.hv_power_supply.close()
                print("Closed HV power supply.")
                time.sleep(0.5)
                del self.hv_power_supply
                print("Deleted HV power supply.")
            except Exception as e:
                print(f"Error closing HV power supply: {e}")
            finally:
                self.hv_power_supply = None

    def open_dmm_for_current(self):
        """
        Opens the DMM used for current measurements if not already open.
        """
        if self.dmm_for_current is not None:
            print("DMM for current is already opened.")
            return
        try:
            self.dmm_for_current = self.rm.open_resource(self.dmm_for_current_name, query_delay=0.5)
            print(f"Opened DMM for current => {self.dmm_for_current_name}")
##            # Clear and flush buffer
##            self.dmm_for_current.flush()
##            time.sleep(0.5)
##            self.dmm_for_current.clear()
##            time.sleep(0.5)
##            print('Flushed DMM for current')
        except Exception as e:
            print(f"Failed to open DMM for current => {self.dmm_for_current_name}: {e}")

    def close_dmm_for_current(self):
        """
        Closes the DMM for current measurements if open.
        """
        if self.dmm_for_current is not None:
            try:
                self.dmm_for_current.close()
                print("Closed DMM for current.")
                time.sleep(0.5)
                del self.dmm_for_current
                print("Deleted DMM for current.")
            except Exception as e:
                print(f"Error closing DMM for current: {e}")
            finally:
                self.dmm_for_current = None

    def open_dmm_for_voltage(self):
        """
        Opens the DMM used for voltage measurements if not already open.
        """
        if self.dmm_for_voltage is not None:
            print("DMM for voltage is already opened.")
            return
        try:
            self.dmm_for_voltage = self.rm.open_resource(self.dmm_for_voltage_name, query_delay=0.5)
            print(f"Opened DMM for voltage => {self.dmm_for_voltage_name}")
##            # Clear and flush buffer
##            self.dmm_for_voltage.flush()
##            time.sleep(0.5)
##            self.dmm_for_voltage.clear()
##            time.sleep(0.5)
##            print('Flushed DMM for voltage')
            
        except Exception as e:
            print(f"Failed to open DMM for voltage => {self.dmm_for_voltage_name}: {e}")

    def close_dmm_for_voltage(self):
        """
        Closes the DMM for voltage measurements if open.
        """
        if self.dmm_for_voltage is not None:
            try:
                self.dmm_for_voltage.close()
                print("Closed DMM for voltage.")
                time.sleep(0.5)
                del self.dmm_for_voltage
                print("Deleted DMM for voltage.")
            except Exception as e:
                print(f"Error closing DMM for voltage: {e}")
            finally:
                self.dmm_for_voltage = None

    def open_oscilloscope(self):
        """
        Opens the oscilloscope if not already open.
        """
        if self.oscilloscope is not None:
            print("Oscilloscope is already opened.")
            return
        try:
            self.oscilloscope = self.rm.open_resource(self.oscilloscope_name, query_delay=0.5, timeout=6000)
            print(f"Opened oscilloscope => {self.oscilloscope_name}")
##            # Clear and flush buffer
##            self.oscilloscope.flush()
##            time.sleep(0.5)
##            self.oscilloscope.clear()
##            time.sleep(0.5)
##            print('Flushed Oscilloscope')
        except Exception as e:
            print(f"Failed to open oscilloscope => {self.oscilloscope_name}: {e}")

    def close_oscilloscope(self):
        """
        Closes the oscilloscope if open.
        """
        if self.oscilloscope is not None:
            try:
                self.oscilloscope.close()
                print("Closed oscilloscope.")
                time.sleep(0.5)
                del self.oscilloscope
                print("Deleted Oscilloscope.")
            except Exception as e:
                print(f"Error closing oscilloscope: {e}")
            finally:
                self.oscilloscope = None

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
    # PART 2: Utility Methods (export, plot)
    # -------------------------------------------------
    def TimeStamp(self):
        # Generate a time-based string here
        now = datetime.now()

        # Create a timestamp like "HH_MM_SS-DD_MM_YYYY"
        day = now.strftime("%d_%m_%Y")
        current_time = now.strftime("%H_%M_%S")
        Timestamp = f"{current_time}-{day}"
        return Timestamp
    
    def export_result_to_csv(self, data_string: str, extra_name: str = None):
        """
        Exports the provided data string to a CSV file named with a timestamp
        and optionally an extra string in the filename.

        Filename formats:
        - Without extra_name: "csv-{timestamp}.csv"
        - With extra_name:    "csv-{timestamp}-{extra_name}.csv"

        Parameters
        ----------
        data_string : str
            The data (e.g., comma-separated values) to write to the CSV file.
        extra_name : str, optional
            Additional string appended to the filename, e.g., "_Current".
            If None, no extra string is appended.
        """
        # Generate a time-based string here
        stamp = self.TimeStamp()

        # Construct filename depending on whether extra_name is provided
        if extra_name:
            filename = f"csv-{stamp}-{extra_name}.csv"
        else:
            filename = f"csv-{stamp}.csv"

        # Write the data to the file
        with open(os.path.join(self.result_output_path,filename), 'w') as f:
            f.write(data_string)

        print(f"CSV exported to {filename}")


    def plot_values(self, data_string: str):
        """
        Plots a comma-separated string of numeric data.
        """
        data_formatted = [float(i) for i in data_string.split(",")]
        plt.plot(data_formatted)
        plt.ylabel('current')
        plt.show()

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
    # PART 4: DMM Functions
    # -------------------------------------------------
    def dmm_setup(self):
        # Configure DMMs (already opened in sup.dmm_for_current, sup.dmm_for_voltage)
        # For example, we can send SCPI commands to set them up
        self.dmm_send_cmd(self.dmm_for_current, [
            "*RST",
            "CONF:CURR:DC 0.2",
            "CURR:DC:AZ OFF",
            #"CONF:CURR:DC AUTO",
            "TRIG:SOUR EXT;SLOP POS",
            f"TRIG:COUN {self.nb_points_i}",
            f"SAMP:COUN {self.dmm_current_sample_count}",
            "TRIG:DEL 1E-6",# double check if TRIG:DEL:AUTO 0 is required or not!!!
            f"CURR:DC:NPLC {self.dmm_current_nplc}",
            "INITiate"
        ], delay=self.dmm_cmd_delay)
        self.dmm_send_cmd(self.dmm_for_voltage, [
            "*RST",
            "CONF:VOLT:DC 200",
            "VOLT:DC:AZ OFF",
            #"CONF:VOLT:DC AUTO",
            "TRIG:SOUR EXT;SLOP POS",
            f"TRIG:COUN {self.nb_points_i}",
            f"SAMP:COUN {self.dmm_voltage_sample_count}",
            "TRIG:DEL 1E-6",
            f"VOLT:DC:NPLC {self.dmm_voltage_nplc}",
            "INITiate"
        ], delay=self.dmm_cmd_delay)            
    
    def dmm_send_cmd(self, dmm, cmd_list: list[str], delay = 0.1):
        """
        Sends a list of SCPI commands to a given DMM resource, printing them for visibility.
        Optionally waits 'delay' seconds between commands.

        Parameters
        ----------
        dmm : resource
            The DMM resource object from self.dmm_for_current or self.dmm_for_voltage
        cmd_list : list of str
            The list of SCPI command strings to send.
        delay : float, optional
            Seconds to wait between each command. Default is 0.
        """
        if dmm is None:
            raise ValueError("DMM is not opened.")
        print(f"{dmm.resource_name} sending commands:")
        for cmd in cmd_list:
            dmm.write(cmd)
            print(f"\t - {cmd}")
            time.sleep(delay)

    def dmm_get_buffer(self, dmm, wait_meas_complete: bool = True) -> list[float]:
        """
        Reads data points in the measurement buffer of a given DMM resource and clears it afterward.

        Parameters
        ----------
        dmm : resource
            The DMM resource object from self.dmm_for_current or self.dmm_for_voltage
        wait_meas_complete : bool, optional
            If True, attempts to query 'READ?' which waits for measurement completion.
            If False, queries 'R?' to fetch any data already in the buffer.

        Returns
        -------
        list of float
            The measured values as floats.
        """
        if dmm is None:
            raise ValueError("DMM is not opened.")

        buffer_str = ''
        if wait_meas_complete:
            time.sleep(4)
            read_ok = False
            while not read_ok:
                try:
                    buffer_str = dmm.query('READ?')
                    read_ok = True
                except visa.errors.VisaIOError:
                    print("Wait for measurement to complete")
        else:
            buffer_str = dmm.query('R?')
            time.sleep(2)

        # handle the #nxxx prefix
        digits = int(buffer_str[1])
        return [float(e) for e in buffer_str[digits + 2:].strip().split(',')]

    def dmm_abort_measure(self, dmm, delay = 0.2):
        """
        Aborts any ongoing measurement in the given DMM resource.

        Parameters
        ----------
        dmm : resource
            The DMM resource object to abort measurement on.
        """
        if dmm is None:
            raise ValueError("DMM is not opened.")
        dmm.write('ABORt')
        time.sleep(delay)

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

    # -------------------------------------------------
    # PART 6: HV Power Supply Functions
    # -------------------------------------------------
    def power_supply_output_change(self, state: str, delay = 0.3):
        """
        Changes the output state of the HV power supply (e.g., 'ON' or 'OFF').

        Parameters
        ----------
        state : str
            The desired output state, typically 'ON' or 'OFF'.
        """
        if self.hv_power_supply is None:
            raise ValueError("HV power supply is not opened.")

        cmd = f'OUTPut:STATe {state}'
        self.hv_power_supply.write(cmd)
        time.sleep(delay)

    def power_supply_check_voltage(self, delay = 0.3) -> float:
        """
        Queries the HV power supply for the measured voltage.

        Returns
        -------
        float
            The measured voltage as a float.
        """
        if self.hv_power_supply is None:
            raise ValueError("HV power supply is not opened.")

        cmd = 'MEASure:VOLTage?'
        result = self.hv_power_supply.query(cmd)
        time.sleep(delay)
        return float(result)

    def power_supply_check_current(self, delay = 0.3) -> float:
        """
        Queries the HV power supply for the measured current.

        Returns
        -------
        float
            The measured current as a float.
        """
        if self.hv_power_supply is None:
            raise ValueError("HV power supply is not opened.")

        cmd = 'MEASure:CURRent?'
        result = self.hv_power_supply.query(cmd)
        time.sleep(delay)
        return float(result)

    def power_supply_voltage_ramp_up(self, voltage: float, step_value: float, start_value=0, delay = 0.1):
        """
        Ramps up the voltage of the HV power supply from start_value to 'voltage', 
        in steps of step_value, waiting self.timestep between steps.

        Parameters
        ----------
        voltage : float
            Target voltage to reach.
        step_value : float
            The increment in voltage for each step.
        start_value : float, optional
            The initial voltage. Defaults to 0.
        """
        if self.hv_power_supply is None:
            raise ValueError("HV power supply is not opened.")

        self.hv_power_supply.write('VOLTage:MODE FIX')
        steps = np.arange(start_value, voltage + step_value, step_value)
        for x in steps:
            x2=round(x)
            cmd2 = f'VOLT:LEV {x2}'
            self.hv_power_supply.write(cmd2)
            time.sleep(delay)
        time.sleep(delay)

    def power_supply_voltage_ramp_down(self, start_voltage: float, end_value: float, step_value: float, delay = 0.1):
        """
        Ramps down the voltage of the HV power supply from 'start_voltage' to 'end_value', 
        in negative increments (step_value < 0), waiting self.timestep between steps.

        Parameters
        ----------
        start_voltage : float
            The starting voltage.
        end_value : float
            The final voltage to reach.
        step_value : float
            The negative increment for each step, e.g., -1.
        """
        if self.hv_power_supply is None:
            raise ValueError("HV power supply is not opened.")

        self.hv_power_supply.write('VOLTage:MODE FIX')
        steps = np.arange(start_voltage, end_value, step_value)
        for x in steps:
            x2=round(x)
            cmd2 = f'VOLT:LEV {x2}'
            self.hv_power_supply.write(cmd2)
            time.sleep(delay)
        time.sleep(delay)

    # -------------------------------------------------
    # PART 7: Oscilloscope Functions
    # -------------------------------------------------
    def oscilloscope_setup(self):
        """
        Initializes the oscilloscope (e.g., configures trigger settings).
        Uses an external library method (controloscillo.ConfigTrigger).
        """
        if self.oscilloscope is None:
            raise ValueError("Oscilloscope is not opened.")
        controloscillo.ConfigTrigger(self.oscilloscope)
        controloscillo.ConfigMeasure(self.oscilloscope)
        controloscillo.ConfigSequence(self.oscilloscope, self.Sequence)
        for i, measureParam in enumerate(self.scopeMeasure):
            controloscillo.NewMeasure(self.oscilloscope, i+1, measureParam)

    def oscilloscope_save_picture(self, name: str):
        """
        Saves a screenshot or image from the oscilloscope to local storage.
        
        Parameters
        ----------
        name : str
            Filename or identifier for the saved picture.
        """
        if self.oscilloscope is None:
            raise ValueError("Oscilloscope is not opened.")
        
        controloscillo.SavePicture(self.oscilloscope, name, self.result_output_path.replace('/','\\'))

    def oscilloscope_read_history_only(self):
        """
        Reads the oscilloscope's history buffer without saving frames or data.
        """
        if self.oscilloscope is None:
            raise ValueError("Oscilloscope is not opened.")
        controloscillo.ReadHistory(self.oscilloscope, self.Sequence, 0, 0, self.delayOscillo)

    def oscilloscope_read_history_and_choose_to_save(self):
        """
        Reads the oscilloscope's history buffer and conditionally saves frames or data
        depending on self.SaveEachFramePICTURE and self.SaveEachFrameDATA.
        """
        if self.oscilloscope is None:
            raise ValueError("Oscilloscope is not opened.")
        controloscillo.ReadHistory(
            self.oscilloscope,
            self.Sequence,
            self.SaveEachFramePICTURE,
            self.SaveEachFrameDATA,
            self.delayOscillo
        )

    def oscilloscope_save_data(self, channel: str, name: str):
        """
        Saves oscilloscope data from a specified channel to a file.

        Parameters
        ----------
        channel : str
            The oscilloscope channel identifier (e.g., 'C1', 'C2').
        name : str
            Filename or identifier for the saved data.
        """
        if self.oscilloscope is None:
            raise ValueError("Oscilloscope is not opened.")
##        controloscillo.SaveDataOscillo(self.oscilloscope, channel, os.path.join(self.result_output_path, name))
        controloscillo.SaveDataOscillo(self.oscilloscope, channel, name, self.result_output_path)

    def oscilloscope_save_data_all_channels(self, name: str):
        """
        Saves oscilloscope data from all channels (C1, C2, C3, C4) using oscilloscope_save_data().
        """
        self.oscilloscope_save_data('C1', name)
        self.oscilloscope_save_data('C2', name)
        self.oscilloscope_save_data('C3', name)
        self.oscilloscope_save_data('C4', name)

    def oscilloscope_save_results(self):
        if self.oscilloscope is None:
            raise ValueError("Oscilloscope is not opened.")
        controloscillo.HistoryMode(self.oscilloscope)
        meas_results = {}
        for frame in range(1, self.Sequence + 1, 1):
            controloscillo.SetFrame(self.oscilloscope, frame)
            frame_name = f'Data{frame}'  #TODO: get a better name that includes measurement parameters

            # Save CSV data for each frame if needed
            if self.SaveEachFrameDATA:
                self.oscilloscope_save_data_all_channels(frame_name)

            # Save screenshot for each frame if needed
            if self.SaveEachFramePICTURE:
                #controloscillo.SavePicture(self.oscilloscope, frame_name, self.result_output_path.replace('/','\\')) # Non inverted
                #controloscillo.SavePicture(self.oscilloscope, frame_name, self.result_output_path.replace('/','\\'), True) # inverted
                controloscillo.SavePicture(self.oscilloscope, frame_name, self.result_output_path) # Non inverted
                controloscillo.SavePicture(self.oscilloscope, frame_name, self.result_output_path, True) # inverted


            frame_meas = {}

            # Put measurement results in a json file
            for i, measureParam in enumerate(self.scopeMeasure):
                frame_meas.update({f'{i+1}': {'type': measureParam.get('type'),
                                              'channel': measureParam.get('channel'),
                                              'value': controloscillo.GetMeasure(self.oscilloscope, i + 1)}})
            print(frame_meas)
            meas_results.update({frame_name: frame_meas})

        # Write one json file with measurements for all frames
        with open(f'{self.result_output_path}/results.json', "w") as f:
            json.dump(meas_results, f, indent=4)
