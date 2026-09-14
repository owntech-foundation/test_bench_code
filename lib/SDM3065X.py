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

#from TDKZ650_1_U import TDKZ650_1_U
#from tools import TOOL



class SDM3065X:
    """
    Class to manage DMM (Siglent SDM3065) resources for current and voltage measurements.
    
    This class handles opening, closing, and configuring two Siglent SDM3065 digital multimeters
    for DC current and DC voltage measurements with external triggering.
    
    Parameters
    ----------
    dmmtype : str, optional
        Type of DMM to initialize ("current", "voltage", or None for both).
    config_path : str, optional
        Path to JSON configuration file. If None, uses default parameters.
    dmm_current_addr : str, optional
        VISA address for current DMM. Default: from config or TCPIP0::169.254.126.119::inst0::INSTR
    dmm_voltage_addr : str, optional
        VISA address for voltage DMM. Default: from config or TCPIP0::169.254.126.120::inst0::INSTR
    """

    def __init__(self, dmmtype: str = None, config_path: str = None, dmm_current_addr: str = None, dmm_voltage_addr: str = None, ressource_manager: visa.ResourceManager = None):
        """
        Initialize the SDM3065X DMM controller.
        
        Parameters
        ----------
        config_path : str, optional
            Path to JSON config file containing DMM parameters
        dmm_current_addr : str, optional
            Override current DMM address
        dmm_voltage_addr : str, optional
            Override voltage DMM address
        """
        # Create PyVISA Resource Manager
        if ressource_manager is None:
            #self.rm = visa.ResourceManager()
            self.rm = None
        else:
            self.rm = ressource_manager
            print("RM sdm")

        # Initialize DMM resource attributes
        self.dmm_for_current = None
        self.dmm_for_voltage = None
        
        # Load configuration if provided
        if config_path and os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            print(f"Config file found at {config_path}. Loading parameters...")
            # Load DMM addresses
            if dmmtype == "current": 
                self.dmm_for_current_name = dmm_current_addr or config.get('DMMforCurrent', 'TCPIP0::169.254.126.119::inst0::INSTR')
            elif dmmtype == "voltage": 
                self.dmm_for_voltage_name = dmm_voltage_addr or config.get('DMMforVoltage', 'TCPIP0::169.254.126.120::inst0::INSTR')
            else:
                self.dmm_for_voltage_name = dmm_voltage_addr or config.get('DMMforVoltage', 'TCPIP0::169.254.126.120::inst0::INSTR')
                self.dmm_for_current_name = dmm_current_addr or config.get('DMMforCurrent', 'TCPIP0::169.254.126.119::inst0::INSTR')
            
            # Load DMM parameters
            self.dmm_init_delay = config.get('dmm_init_delay', 2)
            self.dmm_cmd_delay = config.get('dmm_cmd_delay', 0.1)
            self.dmm_current_nplc = config.get('dmm_current_nplc', 0.5)
            self.dmm_voltage_nplc = config.get('dmm_voltage_nplc', 0.5)
            self.dmm_current_sample_count = config.get('dmm_current_sample_count', 3)
            self.dmm_voltage_sample_count = config.get('dmm_voltage_sample_count', 3)
            self.nb_points_i = config.get('nbPointsI', 10)

            self.trig_source = config.get('trigSource', 'IMM')
            self.dmm_param_mode_lecture = config.get('dmm_param_mode_lecture', 'INITiate')
            # {INTernal|EXTernal|TIMer|BUS|IMM|MANual|ECLock}
        else:
            print(f"Config file not found at {config_path}. Using default parameters.")
            # Default parameters if no config file
            if dmmtype == "current":
                self.dmm_for_current_name = dmm_current_addr or 'TCPIP0::169.254.126.119::inst0::INSTR'
            if dmmtype == "voltage":
                self.dmm_for_voltage_name = dmm_voltage_addr or 'TCPIP0::169.254.126.120::inst0::INSTR'

            self.dmm_init_delay = 2
            self.dmm_cmd_delay = 0.1
            self.dmm_current_nplc = 0.5
            self.dmm_voltage_nplc = 0.5
            self.dmm_current_sample_count = 3
            self.dmm_voltage_sample_count = 3
            self.nb_points_i = 10

            self.trig_source = 'IMM'
            # {INTernal|EXTernal|TIMer|BUS|IMM|MANual|ECLock}

            self.dmm_param_mode_lecture = 'INITiate'
        
        print(f"SDM3065X controller initialized")
        #print(f"  Current DMM: {self.dmm_for_current_name}")
        #print(f"  Voltage DMM: {self.dmm_for_voltage_name}")

#A tester
    def open_all_dmm(self):
        """Opens both DMM resources (current and voltage)."""
        self.open_dmm_for_current()
        time.sleep(0.3)
        self.open_dmm_for_voltage()
        time.sleep(0.3)
#A tester
    def close_all_dmm(self):
        """Closes both DMM resources (current and voltage)."""
        self.close_dmm_for_current()
        time.sleep(0.3)
        self.close_dmm_for_voltage()
        time.sleep(0.3)

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


    def dmm_setup_current_testbench(self):
        """Test bench auto setup, Sets up the DMM for current measurements with the configured parameters.
        This method sends a series of SCPI commands to the current DMM to configure it for DC current measurements
        """
        self.dmm_send_cmd(self.dmm_for_current, [
            "*RST",
            "*CLS", #temporary clear status to avoid errors
            "CONF:CURR:DC 0.2",
            "CURR:DC:AZ OFF",
            "TRIG:SOUR EXT;SLOP POS",
            f"TRIG:COUN {self.nb_points_i}",
            f"SAMP:COUN {self.dmm_current_sample_count}",
            "TRIG:DEL 1E-6",# double check if TRIG:DEL:AUTO 0 is required or not!!!
            f"CURR:DC:NPLC {self.dmm_current_nplc}",
            "INITiate"
        ], delay=self.dmm_cmd_delay)
    
    def dmm_setup_voltage_testbench(self):
        self.dmm_send_cmd(self.dmm_for_voltage, [
            "*RST",
            "*CLS", #temporary clear status to avoid errors
            "CONF:VOLT:DC 200",
            "VOLT:DC:AZ OFF",
            "TRIG:SOUR EXT;SLOP POS",
            f"TRIG:COUN {self.nb_points_i}",
            f"SAMP:COUN {self.dmm_voltage_sample_count}",
            "TRIG:DEL 1E-6",
            f"VOLT:DC:NPLC {self.dmm_voltage_nplc}",
            "INITiate"
        ], delay=self.dmm_cmd_delay) 

    # def dmm_setup_current_(self):
    #     # Configure DMMs (already opened in sup.dmm_for_current, sup.dmm_for_voltage)
    #     # For example, we can send SCPI commands to set them up
    #     # self.dmm_send_cmd(self.dmm_for_current, [
    #     #     "*RST",
    #     #     "CONF:CURR:DC 0.2",
    #     #     "CURR:DC:AZ OFF",
    #     #     #"CONF:CURR:DC AUTO",
    #     #     #"TRIG:SOUR EXT;SLOP POS",

    #     #     f"TRIG:SOUR {self.trig_source};SLOP POS",

    #     #     #TRIG:SOURce {INTernal|EXTernal|TIMer|BUS|IMM|MANual|ECLock};SLOP {POSitive|NEGative}
    #     #     f"TRIG:COUN {self.nb_points_i}",
    #     #     f"SAMP:COUN {self.dmm_current_sample_count}",
    #     #     "TRIG:DEL 1E-6",# double check if TRIG:DEL:AUTO 0 is required or not!!!
    #     #     f"CURR:DC:NPLC {self.dmm_current_nplc}",
    #     #     "INITiate"
    #     # ], delay=self.dmm_cmd_delay)

    #     self.dmm_send_cmd(self.dmm_for_current, [
    #         "*RST",
    #         "CONF:CURR:DC 0.2",
    #         "CURR:DC:AZ OFF",
    #         #"CONF:CURR:DC AUTO",
    #         #"TRIG:SOUR EXT;SLOP POS",

    #         f"TRIG:SOUR {self.trig_source};SLOP POS",

    #         #TRIG:SOURce {INTernal|EXTernal|TIMer|BUS|IMM|MANual|ECLock};SLOP {POSitive|NEGative}
    #         f"TRIG:COUN {self.nb_points_i}",
    #         f"SAMP:COUN {self.dmm_current_sample_count}",
    #         "TRIG:DEL 1E-6",# double check if TRIG:DEL:AUTO 0 is required or not!!!
    #         f"CURR:DC:NPLC {self.dmm_current_nplc}",
    #         "INITiate"
    #     ], delay=self.dmm_cmd_delay)

    # def dmm_setup_voltage(self):
    #     # self.dmm_send_cmd(self.dmm_for_voltage, [
    #     #     "*RST",
    #     #     "CONF:VOLT:DC 200",
    #     #     "VOLT:DC:AZ OFF",
    #     #     #"CONF:VOLT:DC AUTO",


    #     #     f"TRIG:SOUR {self.trig_source};SLOP POS",


    #     #     #TRIG:SOURce {EXTernal|TIMer|BUS|IMM|MANual|ECLock};SLOP {POSitive|NEGative}
    #     #     f"TRIG:COUN {self.nb_points_i}",
    #     #     f"SAMP:COUN {self.dmm_voltage_sample_count}",
    #     #     "TRIG:DEL 1E-6",
    #     #     f"VOLT:DC:NPLC {self.dmm_voltage_nplc}",
    #     #     "INITiate"
    #     # ], delay=self.dmm_cmd_delay)  

    #     self.dmm_send_cmd(self.dmm_for_voltage, [
    #         "*RST",
    #         "CONF:VOLT:DC 200",
    #         "VOLT:DC:AZ OFF",
    #         #"CONF:VOLT:DC AUTO",


    #         f"TRIG:SOUR {self.trig_source};SLOP POS",


    #         #TRIG:SOURce {EXTernal|TIMer|BUS|IMM|MANual|ECLock};SLOP {POSitive|NEGative}
    #         f"TRIG:COUN {self.nb_points_i}",
    #         f"SAMP:COUN {self.dmm_voltage_sample_count}",
    #         "TRIG:DEL 1E-6",
    #         f"VOLT:DC:NPLC {self.dmm_voltage_nplc}",
    #         f"{self.dmm_param_mode_lecture}"
    #     ], delay=self.dmm_cmd_delay)           
    

    def dmm_setup_testbench(self, dmmtype: str = None):
        """
        Generalized setup function for a DMM resource, allowing configuration of trigger source and other parameters.
        This can be used to set up either the current or voltage DMM with custom settings.

        Parameters
        ----------
        dmm_type : str
            The type of DMM to set up ('current' or 'voltage').
        """

        if(dmmtype == "current"):
            self.dmm_setup_current_testbench()

        elif(dmmtype == "voltage"):
            self.dmm_setup_voltage_testbench()
        else:
            raise ValueError("Invalid dmmtype. Must be 'current' or 'voltage' in function dmm_setup.")


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
        print(f"dmm_get_buffer Debug buffer_str : {buffer_str}")
        
        digits = int(buffer_str[1])
        
        print(f"dmm_get_buffer Debug digits : {digits}")
        
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

    def cleanup(self):
        """
        Closes all open resources including both DMMs and the PyVISA resource manager.
        """
        self.close_all_dmm()
        if self.rm is not None:
            try:
                self.rm.close()
                print("PyVISA ResourceManager closed.")
            except Exception as e:
                print(f"Error closing ResourceManager: {e}")

    def __del__(self):
        """Destructor to ensure resources are cleaned up when object is deleted."""
        try:
            self.cleanup()
        except Exception as e:
            print(f"Error during cleanup: {e}")
    

def find_json_files(folder):
    """
    Recursively finds all JSON files in the specified folder and its subfolders.
    Useful only for testing purposes to easily load configuration files without hardcoding paths.
    """
    json_files = []
    for root, dirs, files in os.walk(folder):
        for file in files:
            if file.endswith('.json'):
                json_files.append(os.path.relpath(os.path.join(root, file), "./"))
    return json_files

def TimeStamp():
    # Generate a time-based string here
    now = datetime.now()

    # Create a timestamp like "HH_MM_SS-DD_MM_YYYY"
    day = now.strftime("%d_%m_%Y")
    current_time = now.strftime("%H_%M_%S")
    Timestamp = f"{current_time}-{day}"
    return Timestamp

# ======================== USAGE EXAMPLE ========================
if __name__ == "__main__":
    """
    Example usage of the SDM3065X class for DMM control.
    """
    print("\n" + "="*60)
    print("  SDM3065X DMM Controller - Example Usage")
    print("="*60 + "\n")
    
  
    jsonlist = find_json_files("../PhaseShift")

    # Initialize with configuration file
    
    sdm_current = SDM3065X(dmmtype="current", config_path=jsonlist[0])
    sdm_voltage = SDM3065X(dmmtype="voltage", config_path=jsonlist[0])

    tdk = TDKZ650_1_U(config_path=jsonlist[0])

# Override some parameters for testing purposes
    sdm_voltage.nb_points_i = 250
    sdm_voltage.dmm_voltage_sample_count = 2 
    sdm_voltage.dmm_param_mode_lecture = 'READ?' # 'INITiate' or 'SINGle' or READ? (lecture mode for voltage DMM, to be tested)
    sdm_voltage.dmm_voltage_nplc = 0.5

    try:
        # Open both DMMs
        print("\n1. Opening DMMs...")
        sdm_current.open_dmm_for_current()
        sdm_voltage.open_dmm_for_voltage()
        print("   ✓ DMMs opened successfully\n")
        
        # Configure for measurements
        print("2. Configuring DMMs for DC measurements...")
        sdm_current.dmm_setup_current_testbench()
        sdm_voltage.dmm_setup_voltage_testbench()
        print("   ✓ DMM setup complete!\n")
        
        # Wait for initialization
        print(f"3. Waiting for initialization ({sdm_current.dmm_init_delay}s)...")
        time.sleep(sdm_current.dmm_init_delay)
        print("   ✓ Ready for measurements\n")
        
        print("4. Measurements would be triggered by external signal (oscilloscope)...")
        print("   Status: Waiting for trigger...\n")

        tdk.TDK_ramp_up_and_down_example()

        # sdm_voltage.dmm_abort_measure(sdm_voltage.dmm_for_voltage)
        # sdm_voltage.dmm_abort_measure(sdm_voltage.dmm_for_voltage)
        
        # Get data from buffers (when data is available) 
        voltage_data = sdm_voltage.dmm_get_buffer(sdm_voltage.dmm_for_voltage)
        # current_data = sdm_current.dmm_get_buffer(sdm_current.dmm_for_current)
        print(f"   Voltage measurements: {voltage_data}")
        # print(f"   Current measurements: {current_data}\n")

        plt.figure()
        plt.title("Voltage Data Points")
        plt.plot(voltage_data, marker='o', linestyle='none')
        plt.savefig('01-Voltage-' + TimeStamp() + '.svg', format='svg', dpi=300)
        
    except Exception as e:
        print(f"❌ Error: {e}\n")
        import traceback
        traceback.print_exc()
    finally:
        # Always cleanup
        print("5. Cleanup...")
        
        sdm_current.close_dmm_for_current()
        time.sleep(0.3)
        sdm_voltage.close_dmm_for_voltage()
        time.sleep(0.3)
        print("   ✓ Resources released.\n")
        print("="*60)
        print("  Example SDM3065X completed")
        print("="*60 + "\n")
