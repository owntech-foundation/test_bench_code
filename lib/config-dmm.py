# Just DMM functions for development
import matplotlib.pyplot as plt
import pyvisa as visa
import time
from datetime import datetime
from typing import cast, Any

delay1 = 0.1 #delay in seconds (100 ms)

# ------------ Identification of instruments
def list_instruments():
    rm = visa.ResourceManager()
    instrument_list = rm.list_resources()

    for instrument in instrument_list:
        print("'{:s}': ".format(instrument), end=' ')
        try:
            device = rm.open_resource(instrument)
            print(type(device), end=' ')
            print(device.query("*IDN?"), end='\n')

        except visa.errors.VisaIOError:
            print('INSTRUMENT ERROR\n')
    # ## rev3 19/11/2024 Close rm !!
    rm.close() 

## rev3 19/11/2024 no longer hard-code DMM addr
def auto_detect_device(name: str) -> str:
    rm = visa.ResourceManager()
    instrument_list = rm.list_resources()
    dmm_addr = ''

    for instrument in instrument_list:
        if(name in instrument):
            dmm_addr = f"{instrument}"

    rm.close()  # Close rm
    return dmm_addr


def openSiglentDMM(name: str, **kwargs: Any) -> visa.resources.usb.USBInstrument:
    """Open a Siglent DMM resource.

     Parameters
     ----------
     name : str
            Multimeter name to identify in visa.ResourceManager() list
    kwargs : Any
            Keyword arguments to be used for visa.open_resource()

     Returns
     -------
     visa.resources.usb.USBInstrument
     """
    device_id = auto_detect_device(name)  # no longer hard-coded address
    print(f"Autodetected DMM: {device_id}")
    rm = visa.ResourceManager()
    dmm = cast(visa.resources.usb.USBInstrument, rm.open_resource(device_id, **kwargs))
    return dmm

# ------------ Functions for DMM
# ## rev3 19/11/2024 Send list of command instead of line by line
def SendCmd(dmm, cmd_list: list[str], delay: float = 0):
    """Send a list of commands to Siglent DMM.

     Parameters
     ----------
     dmm : VISA Resource corresponding to the multimeter
     cmd_list : list of string commands
     delay : delay in seconds between each command (default 0)
     """
    for cmd in cmd_list:
        dmm.write(cmd)
        time.sleep(delay)

def GetBuffer(dmm, wait_meas_complete: bool = True) -> list[str]:
    """Read data points in the measurement buffer and clear it.
    Parameters
    ----------
    dmm : VISA Resource corresponding to the multimeter
    wait_meas_complete : boolean, default True
            If true the function waits for the multimeter to return to idle and uses the READ? command
            If false the function uses the R? function that return only data that are in the buffer
    Returns
    -------
    List of data points
    """
    buffer_str = ''
    if wait_meas_complete:
        time.sleep(4)  # 4 second delay to be sure previous measurement is OK
        read_ok = False
        while not read_ok:
            try:
                buffer_str = dmm.query('READ?')  # FETCh? or READ? have to wait for the end of the measurement
                read_ok = True
            except visa.errors.VisaIOError:
                print("Wait for measurement to complete")
    else:
        buffer_str = dmm.query('R?')

    # the returned string starts with: #nxxx where n is the number of digits of the number xxx which
    # represent the total length of the string. We need to remove that
    digits = int(buffer_str[1])
    return buffer_str[digits + 2:].strip().split(',')


def AbortMeasure(dmm):
    dmm.write('ABORt')
    time.sleep(2)


def ConfigForDCVoltageMeasureAndStoreBuffer(dmm, **config):
    """Configures Siglent DMM for DC Voltage measurement.

     Parameters
     ----------
     dmm : VISA Resource corresponding to the multimeter
     config : Any Keywords for measurement configuration. Possible keys are :
        voltage_range, trig_count, trig_source, trig_delay, sample_count, nplc, auto_zero
     """
    cmd_buf = []
    cmd_buf.append(f'CONF:VOLT:DC {config.get("voltage_range", "AUTO")}')
    cmd_buf.append(f'TRIG:COUN {config.get("trig_count", "1")}')
    cmd_buf.append(f'TRIG:SOUR {config.get("trig_source", "IMM")}')
    cmd_buf.append(f'SAMP:COUN {config.get("sample_count", "1")}')
    cmd_buf.append(f'VOLT:DC:NPLC {config.get("nplc", "1")}')
    cmd_buf.append(f'VOLT:DC:AZ {config.get("auto_zero", "OFF")}')

    if 'trig_delay' in config:
        if config.get('trig_delay') is "AUTO":
            cmd_buf.append('TRIG:DEL:AUTO 1')   # auto delay between trigger and each measurement
        else:
            cmd_buf.append(f'TRIG:DEL {config.get("trig_delay")}')   # delay in seconds
    else:
        cmd_buf.append('TRIG:DEL:AUTO 1')

    SendCmd(dmm, cmd_buf, delay1)

def ConfigForDCCurrentMeasureAndStoreBuffer(dmm, **config):
    """Configures Siglent DMM for DC Current measurement.

     Parameters
     ----------
     dmm : VISA Resource corresponding to the multimeter
     config : Any keywords for measurement configuration. Possible keys are :
        voltage_range, trig_count, trig_source, trig_delay, sample_count, nplc, auto_zero
     """
    cmd_buf = []
    cmd_buf.append(f'CONF:CURR:DC {config.get("voltage_range", "AUTO")}')   # Current range
    cmd_buf.append(f'TRIG:COUN {config.get("trig_count", "1")}')            # Max trigger before returning to idle
    cmd_buf.append(f'TRIG:SOUR {config.get("trig_source", "IMM")}')         # immediate trigger (after INIT is sent)
    cmd_buf.append(f'SAMP:COUN {config.get("sample_count", "1")}')          # Number of measurement per trigger
    cmd_buf.append(f'CURR:DC:NPLC {config.get("nplc", "1")}')               # Default NPLC 1
    cmd_buf.append(f'CURR:DC:AZ {config.get("auto_zero", "OFF")}')          # Default auto-zero OFF

    if 'trig_delay' in config:
        if config.get('trig_delay') is "AUTO":
            cmd_buf.append('TRIG:DEL:AUTO 1')   # auto delay between trigger and each measurement
        else:
            cmd_buf.append(f'TRIG:DEL {config.get("trig_delay")}')   # delay in seconds
    else:
        cmd_buf.append('TRIG:DEL:AUTO 1')

    SendCmd(dmm, cmd_buf, delay1)


# ## rev3 19/11/2024 common for current & voltage
def StartMeasureAndStoreBufferDC(dmm):
    # Initiate measurement if Trigger immediate is set before
    SendCmd(dmm, ['INITiate'])


def StartLoggingDCvoltage(dmm, **config):
    # Configure DMM for DC voltage
    ConfigForDCVoltageMeasureAndStoreBuffer(dmm, **config)
    StartMeasureAndStoreBufferDC(dmm)  # Measure and Store in buffer


def StartLoggingDCcurrent(dmm, **config):
    # Configure DMM for DC current
    ConfigForDCCurrentMeasureAndStoreBuffer(dmm, **config)
    StartMeasureAndStoreBufferDC(dmm)  # Measure and Store in buffer


def main():
    #list_instruments()

    dmm = openSiglentDMM('SDM35HBQ7R1226', query_delay=0.01)
    # dmm.write('SYSTem:PRESet')    # Be careful this takes a lot of time to complete !
    # time.sleep(4)

    # configure current DMM with external trigger
    # maximum 100 measured points, 50ms delay before measurement
    # and NPLC = 1 (20ms)
    ConfigForDCCurrentMeasureAndStoreBuffer(dmm, trig_source='EXT', trig_count=100, trig_delay=0.05, nplc=1)

    dmm.write('INITiate')

    ### Test loop
    start = time.time()
    while(time.time() - start) <= 5:   # loop for 5 seconds
        print(dmm.query('DATA:POINts?'))    # This shows the number of measurement points
        time.sleep(0.5)

    dmm.write('ABORt')      # return to idle state #TODO: This doesn't seems to work ! :(

    print("Measurement finished")
    print(dmm.query('DATA:POINts?'))
    values = GetBuffer(dmm, wait_meas_complete=False)   # get the measure points we have at this moment

    print(f"Loaded {len(values)} points")
    print(values)

    dmm.close()     # Close DMM resource session (ResourceManager is still alive !)


if __name__ == "__main__":
    main()
