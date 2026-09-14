import json
import os
import time
import pylab as pl 
import struct 
import gc

import pyvisa as visa
from pyvisa import constants
from pyvisa.resources.serial import SerialInstrument
import sys
import math
from datetime import datetime
import matplotlib.pyplot as plt

#from TDKZ650_1_U import TDKZ650_1_U
#from tools import TOOL


class SDS2104X_plus:
    """
    Class to manage SDS2104X_plus resources.
    """

    def __init__(self, config_path: str = None, ressource_manager: visa.ResourceManager = None):
        """
        Initialize the SDS2104X_plus.
        
        Parameters
        ----------
        config_path : str, optional
            Path to JSON config file containing power supply parameters
        """

        # Create PyVISA Resource Manager
        if ressource_manager is None:
            #self.rm = visa.ResourceManager()
            self.rm = None
        else:
            self.rm = ressource_manager
            print("RM sds")
        
        self.oscilloscope = None
        self.oscilloscope_name = 'USB0::0xF4EC::0x1011::SDS2PDDX6R0968::INSTR'
        self.Sequence = 1
        self.delayOscillo = 0.1
        self.SaveEachFramePICTURE = False
        self.SaveEachFrameDATA = False
        self.result_output_path = ""
        self.scopeMeasure = []
        
        # Load configuration if provided
        if config_path and os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            self.oscilloscope_name = config.get('AddressOSCILLO', self.oscilloscope_name)
            self.Sequence = config.get('Sequence', self.Sequence)
            self.delayOscillo = config.get('delayOscillo', self.delayOscillo)
            self.SaveEachFramePICTURE = config.get('SaveEachFramePICTURE', self.SaveEachFramePICTURE)
            self.SaveEachFrameDATA = config.get('SaveEachFrameDATA', self.SaveEachFrameDATA)
            self.result_output_path = config.get('result_output_path', self.result_output_path)
            self.scopeMeasure = config.get('ScopeAutoMeasure', self.scopeMeasure)

        else:
            print(f"Config file not found at {config_path}. Using default parameters.")
            # Default parameters if no config file



    # ========================  ========================
    # Global variables 
    # (Modify the following global variables according to the model). 
    # --------------------------------------------------------- 
    #SDS_RSC = "USB0::0xF4EC::0x1011::SDS2PEEC6R0224::INSTR"
    #CHANNEL = "C1" 
    HORI_NUM = 10 
    tdiv_enum = [200e-12,500e-12, 1e-9, 2e-9, 5e-9, 10e-9, 20e-9, 50e-9, 100e-9, 200e-9, 500e-9, 1e-6, 2e-6, 5e-6, 10e-6, 20e-6, 50e-6, 100e-6, 200e-6, 500e-6,
                  1e-3, 2e-3, 5e-3, 10e-3, 20e-3, 50e-3, 100e-3, 200e-3, 500e-3, 1, 2, 5, 10, 20, 50, 100, 200, 500, 1000] 

    def oscilloscope_save_results(self):
        if self.oscilloscope is None:
            raise ValueError("Oscilloscope is not opened.")
        self.HistoryMode()
        meas_results = {}
        for frame in range(1, self.Sequence + 1, 1):
            self.SetFrame(frame)
            frame_name = f'Data{frame}'  #TODO: get a better name that includes measurement parameters

            # Save CSV data for each frame if needed
            if self.SaveEachFrameDATA:
                self.oscilloscope_save_data_all_channels(frame_name)

            # Save screenshot for each frame if needed
            if self.SaveEachFramePICTURE:
                #controloscillo.SavePicture(self.oscilloscope, frame_name, self.result_output_path.replace('/','\\')) # Non inverted
                #controloscillo.SavePicture(self.oscilloscope, frame_name, self.result_output_path.replace('/','\\'), True) # inverted
                self.SavePicture(frame_name, self.result_output_path) # Non inverted
                self.SavePicture(frame_name, self.result_output_path, True) # inverted


            frame_meas = {}

            # Put measurement results in a json file
            for i, measureParam in enumerate(self.scopeMeasure):
                frame_meas.update({f'{i+1}': {'type': measureParam.get('type'),
                                              'channel': measureParam.get('channel'),
                                              'value': self.GetMeasure(i + 1)}})
            print(frame_meas)
            meas_results.update({frame_name: frame_meas})

        # Write one json file with measurements for all frames
        with open(f'{self.result_output_path}/results.json', "w") as f:
            json.dump(meas_results, f, indent=4)

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

    def ExportResultToCSV(self, String, name, path):
        file_name= f"csv-{name}.csv"
        print(file_name)
        f = open(os.path.join(path, file_name), 'w')
        f.write(String) #Give your csv text here.
        ## Python will convert \n to os.linesep
        f.close()


    def PlotValues(self, data):
        x=data.split(",")
        dataFormatted=[float(i) for i in x]
        plt.plot(dataFormatted)
        plt.ylabel('current')
        #plt.show()


    def ConfigTrigger(self):
        self.oscilloscope.write('TRIG:TYPE  EDGE ') # Edge
        self.oscilloscope.write(':TRIGger:EDGE:SLOPe  RISing') # Rising Edge
        #self.oscilloscope.write(':TRIGger:EDGE:HOLDoff  TIME') #HOLDoff with TIME
        #self.oscilloscope.write(':TRIGger:EDGE:HLDTime  50E-03') # HOLDoff TIME 50ms
        #self.oscilloscope.write(':TRIGger:EDGE:SOURce  C1') #Trigger Source C1
        #self.oscilloscope.write(':TRIGger:EDGE:SOURce  EX') #Trigger Source External
        self.oscilloscope.write(':TRIGger:EDGE:SOURce  EX5') #Trigger Source External /5
        #self.oscilloscope.write(':TRIGger:EDGE:LEVel  0.00E-01') #Trigger Level 0V
        self.oscilloscope.write(':TRIGger:EDGE:LEVel  7.00E-01') #Trigger Level 700mV
        self.oscilloscope.write('TRIG:MODE  SINGle') # Single


    def ConfigSequence(self, nbFrames):
        self.oscilloscope.write(':ACQuire:SEQuence ON') #Segmented Memory ON
        #self.oscilloscope.write(':ACQuire:SEQuence:COUNt 200') # 200 Sequential Segments
        self.oscilloscope.write(f':ACQuire:SEQuence:COUNt {nbFrames}')  # 200 Sequential Segments


    def ConfigDisplay(self):
        #self.oscilloscope.write(':TIMebase:SCALe  5.00E-06') #Timebase 5us / div
        self.oscilloscope.write(':TIMebase:SCALe  2.00E-06') #Timebase 2us / div


    def ConfigMeasure(self):
        self.oscilloscope.write(':MEASure ON')
        self.oscilloscope.write(':MEASure:MODE ADVanced')
        self.oscilloscope.write(':MEASure:ADVanced:STYLe M1')


    def HistoryMode(self):
        self.oscilloscope.write(':HISTORy ON')
        self.oscilloscope.write(':HISTORy:INTERval 200.00E-03')  # 200 ms time interval for playing history
        self.oscilloscope.write(':HISTORy:PLAy FORWards')  # PLay automatically all frames


    def SetFrame(self, num: int):
        self.oscilloscope.write(f':HISTORy:FRAMe {num}')


    def NewMeasure(self, num: int, measure: dict):
        type = measure.get('type')
        source = measure.get('channel')
        self.oscilloscope.write(f':MEASure:ADVanced:P{num} ON')
        self.oscilloscope.write(f':MEASure:ADVanced:P{num}:SOURce1 C{source}')
        self.oscilloscope.write(f':MEASure:ADVanced:P{num}:TYPE {type}')
        print(f"Add Measure {num} on Ch{source} : {type}")


    def GetMeasure(self, num: int):
        if not 'ON' in self.oscilloscope.query(f':MEASure:ADVanced:P{num}?'):
            print(f'Measure {num} is not set')
            return 0
        val_str = self.oscilloscope.query(f':MEASure:ADVanced:P{num}:VALue?').strip()
        print(f'Get measure {num}: {val_str}')
        if '****' in val_str:
            return None
        return eval(val_str)


    def SavePicture(self, name: str, path: str = "", inverted: bool = False):
        # Make sure that the drive specified is available on your computer
        file_name = f"scope{'-Inverted-' if inverted else ''}{name}.bmp"
        self.oscilloscope.chunk_size = 20 * 1024 * 1024  #default value is 20*1024(20k bytes)
        #self.oscilloscope.write("SCDP")
        self.oscilloscope.write(f"PRIN? BMP{',INVerted' if inverted else ''}")  # BMP
        #self.oscilloscope.write("PRIN? PNG")
        result_str = self.oscilloscope.read_raw()
        f = open(os.path.join(path, file_name), 'wb')
        f.write(result_str)
        f.flush()
        del result_str
        # time.sleep(0.2)


    #smu > instrument
    #nbFrames > String, max number of frames
    #SaveBitmap > save each frame as bitmap 1 for YES
    #SaveDate > export all channels as CSV, 1 for YES
    #delay > waiting delay between each frame
    def ReadHistory(self, nbFrames, SaveBitmap, SaveData, delay):
        self.HistoryMode()
        #Must wait here !!!! otherwise useless
        for frame in range(1, nbFrames+1, 1):
            self.SetFrame(frame)
            time.sleep(delay)
            #self.oscilloscope.write(':SYSTem:MENU OFF')
            #time.sleep(delay) DOES NOT WORK
            frameName = f'Data{frame}'
            if SaveBitmap:
                self.SavePicture(frameName)
                self.SavePicture(frameName, inverted=True)
                # time.sleep(delay)
            if SaveData:
                self.SaveDataOscillo('C1', frameName)
                #pl.figure(1)
                self.SaveDataOscillo('C2', frameName)
                #pl.figure(2)
                self.SaveDataOscillo('C3', frameName)
                #pl.figure(3)
                self.SaveDataOscillo('C4', frameName)
                #pl.figure(4)
                #pl.show()
        



    # ========================================================= 
    # main_desc:Analyzing waveform parameters from data blocks 
    # ========================================================= 
    def main_desc(self, recv): 
        WAVE_ARRAY_1 = recv[0x3c:0x3f + 1]
        wave_array_count = recv[0x74:0x77 + 1] 
        first_point = recv[0x84:0x87 + 1] 
        sp = recv[0x88:0x8b + 1] 
        v_scale = recv[0x9c:0x9f + 1] 
        v_offset = recv[0xa0:0xa3 + 1] 
        interval = recv[0xb0:0xb3 + 1] 
        code_per_div = recv[0xa4:0Xa7 + 1] 
        adc_bit = recv[0xac:0Xad + 1] 
        delay = recv[0xb4:0xbb + 1] 
        tdiv = recv[0x144:0x145 + 1] 
        probe = recv[0x148:0x14b + 1] 
    
        data_bytes = struct.unpack('i', WAVE_ARRAY_1)[0] 
        point_num = struct.unpack('i', wave_array_count)[0] 
        fp = struct.unpack('i', first_point)[0] 
        sp = struct.unpack('i', sp)[0] 
        interval = struct.unpack('f', interval)[0] 
        delay = struct.unpack('d', delay)[0] 
        tdiv_index = struct.unpack('h', tdiv)[0] 
        probe = struct.unpack('f', probe)[0] 
        vdiv = struct.unpack('f', v_scale)[0] * probe 
        offset = struct.unpack('f', v_offset)[0] * probe 
        code = struct.unpack('f', code_per_div)[0] 
        adc_bit = struct.unpack('h', adc_bit)[0] 
        tdiv = self.tdiv_enum[tdiv_index] 
        return vdiv, offset, interval, delay, tdiv, code, adc_bit,data_bytes 
    
    # ========================================================= 
    # Main program: 
    # ========================================================= 
    def SaveDataOscillo(self, channel: str,  name: str, path: str = ""):
        #_rm = visa.ResourceManager() 
        #sds = _rm.open_resource(smu) 
        sds = self.oscilloscope
        sds.timeout = 6000  # default value is 2000(2s) 
        sds.chunk_size = 20 * 1024 * 1024  # default value is 20*1024(20k bytes) 
    
        # Get the channel waveform parameter data blocks and parse them 
        sds.write(":WAVeform:STARt 0")
        sds.write(":WAVeform:POINt 0")
        sds.write(f"WAV:SOUR {channel}")
        sds.write("WAV:PREamble?") 
        recv_all = sds.read_raw() 
        recv = recv_all[recv_all.find(b'#') + 11:]
        time_stamp = recv[346:] 
        print("Length received",len(recv)) 
        vdiv, ofst, interval, trdl, tdiv, vcode_per, adc_bit,data_bytes = self.main_desc(recv) 
        print(vdiv, ofst, interval, trdl, tdiv,vcode_per,adc_bit,data_bytes) 
    
        # Get the waveform points and confirm the number of waveform slice reads 
        points = float(sds.query(":ACQuire:POINts?").strip()) 
        one_piece_num = float(sds.query(":WAVeform:MAXPoint?").strip()) 
        read_times = math.ceil(points / one_piece_num) 
        #Set the number of read points per slice, if the waveform points is greater than the maximumnumber of slice reads 
        if points > one_piece_num: 
            sds.write(":WAVeform:POINt {}".format(one_piece_num)) 
        # Choose the format of the data returned 
        sds.write(":WAVeform:WIDTh BYTE") 
        if adc_bit > 8: 
            sds.write(":WAVeform:WIDTh WORD") 
    
        #Get the waveform data for each slice 
        recv_byte = b'' 
        for i in range(0, read_times): 
            start = i * one_piece_num 
            #Set the starting point of each slice 
            sds.write(":WAVeform:STARt {}".format(start)) 
            #Get the waveform data of each slice 
            sds.write("WAV:DATA?")
            recv_rtn = sds.read_raw().rstrip() 
            #Splice each waveform data based on data block information 
            block_start = recv_rtn.find(b'#') 
            data_digit = int(recv_rtn[block_start + 1:block_start + 2]) 
            data_start = block_start + 2 + data_digit 
            recv_byte += recv_rtn[data_start:]

        if data_bytes != len(recv_byte):
            print("data bytes",data_bytes,"len recv byte",len(recv_byte))
            print("Problem")
            print("Length recv_rtn",len(recv_rtn))
            Diff=data_bytes-len(recv_byte)
            print(Diff)
            points=points-Diff
            print(points)
            if adc_bit > 8:
                Mult=2
            else:
                Mult=1
            data_stop=data_start+Mult*points
            recv_byte=recv_rtn[data_start:int(data_stop)]
    ##        points=int(len(recv_byte)/2)+1
    ##        recv_byte[points]=+0
    ##        recv_byte += 0

    ##        Diff=data_bytes-len(recv_byte)
    ##        del recv_byte
    ##        recv_byte = b''
    ##        print(Diff)
    ##        recv_byte += recv_rtn[data_start-Diff:]
    ##        points=points-Diff
    ##        print(points)
    ##        data_stop = block_start + 2 + data_digit+points
    ##        recv_byte += recv_rtn[data_start:data_stop]
            
                
        
    ##    print("Length recv_rtn",len(recv_rtn))
        print("points",points)
    ##    print(one_piece_num)
    ##    print(read_times)
        print(len(recv_byte))
        # Unpack signed byte data. 
        if adc_bit > 8: 
            convert_data = struct.unpack("%dh"%points, recv_byte)
        else: 
            convert_data = struct.unpack("%db"%points, recv_byte) 
        del recv_byte 
        gc.collect() 
        #Calculate the voltage value and time value 
        time_value = [] 
        volt_value = [] 
        for idx in range(0, len(convert_data)): 
            volt_value.append(convert_data[idx] / vcode_per * float(vdiv) - float(ofst)) 
            time_data = - (float(tdiv) * self.HORI_NUM / 2) + idx * interval + float(trdl) 
            time_value.append(time_data) 
        print(len(volt_value)) 
        #Draw Waveform 
        #pl.figure(figsize=(7, 5)) 
        #pl.plot(time_value, volt_value, markersize=2, label=u"Y-T") 
        #pl.legend() 
        #pl.grid() 
        #pl.show()
        #
        # Save as CSV
        self.ExportResultToCSV(str(time_value), f'{channel}-{name}-timeX',path)
        self.ExportResultToCSV(str(volt_value), f'{channel}-{name}-valueY',path)
        print(f'Channel: {channel} - Frame / Name: {name}')
        del recv_all,time_value,volt_value,recv,convert_data,recv_rtn
    
    def oscilloscope_setup(self):
        """
        Initializes the oscilloscope (e.g., configures trigger settings).
        Uses an external library method (controloscillo.ConfigTrigger).
        """
        if self.oscilloscope is None:
            raise ValueError("Oscilloscope is not opened.")
        self.ConfigTrigger()
        self.ConfigMeasure()
        self.ConfigSequence(self.Sequence)
        for i, measureParam in enumerate(self.scopeMeasure):
            self.NewMeasure(i+1, measureParam)

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
        
        self.SavePicture(name, self.result_output_path.replace('/','\\'))

    def oscilloscope_read_history_only(self):
        """
        Reads the oscilloscope's history buffer without saving frames or data.
        """
        if self.oscilloscope is None:
            raise ValueError("Oscilloscope is not opened.")
        self.ReadHistory(self.Sequence, 0, 0, self.delayOscillo)

    def oscilloscope_read_history_and_choose_to_save(self):
        """
        Reads the oscilloscope's history buffer and conditionally saves frames or data
        depending on self.SaveEachFramePICTURE and self.SaveEachFrameDATA.
        """
        if self.oscilloscope is None:
            raise ValueError("Oscilloscope is not opened.")
        self.ReadHistory(
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
        self.SaveDataOscillo(channel, name, self.result_output_path)

    def oscilloscope_save_data_all_channels(self, name: str):
        """
        Saves oscilloscope data from all channels (C1, C2, C3, C4) using oscilloscope_save_data().
        """
        self.oscilloscope_save_data('C1', name)
        self.oscilloscope_save_data('C2', name)
        self.oscilloscope_save_data('C3', name)
        self.oscilloscope_save_data('C4', name)


# ======================== USAGE EXAMPLE ========================
if __name__ == "__main__":
    """
    Test program: voltage ramp with TDK Z650 + oscilloscope capture with SDS2104X+.
    - Configures the oscilloscope trigger (single mode, rising edge)
    - Ramps up voltage via TDK power supply
    - Oscilloscope triggers on the ramp start
    - Ramps down voltage and disables output
    - Saves a screenshot after acquisition

    """
    print("\n" + "="*60)
    print("  Ramp Capture Test - TDK Z650 + SDS2104X+")
    print("="*60 + "\n")
 
    # ── 1. Find config files ──────────────────────────────────────
    jsonlist = find_json_files("../PhaseShift")
    if not jsonlist:
        print("❌ No JSON config file found in ../PhaseShift")
        raise SystemExit(1)
    config_path = jsonlist[0]
    print(f"Using config: {config_path}\n")
 
    # ── 2. Instantiate instruments ────────────────────────────────
    scope = SDS2104X_plus(config_path=config_path)
    tdk   = TDKZ650_1_U(config_path=config_path)
 
    try:
        # ── 3. Open oscilloscope ──────────────────────────────────
        print("1. Opening oscilloscope...")
        scope.open_oscilloscope()
        print("   ✓ Oscilloscope opened\n")
 
        # ── 4. Configure oscilloscope ─────────────────────────────
        #    - Edge trigger, rising, source EX5, level 700 mV
        #    - Single acquisition mode  (waits for one trigger event)
        #    - Timebase 2 µs/div
        print("2. Configuring oscilloscope...")
        scope.oscilloscope_setup()
        print("   ✓ Oscilloscope configured\n")
 
        # ── 5. Ramp up and ramp down voltage with TDK power supply ───────────────
        print("3. Ramping up and down voltage on TDK power supply...")
        tdk.TDK_ramp_up_and_down_example()
        print("   ✓ Voltage ramp complete\n")
        
 
        # ── 6. Wait for oscilloscope to finish its acquisition ────
        acquisition_wait = 20.0   # seconds — We wait long enough for the acquisition
        print(f"8. Waiting {acquisition_wait} s for oscilloscope acquisition...")
        time.sleep(acquisition_wait)
        print("   ✓ Acquisition window elapsed\n")
 
        # ── 7. Save screenshot ───────────────────────────────────
        screenshot_name = f"ramp_capture_{time.strftime('%Y%m%d_%H%M%S')}"
        save_path = scope.result_output_path if scope.result_output_path else "./"
        print(f"9. Saving screenshot  →  {save_path}/scope{screenshot_name}.bmp ...")
        scope.SavePicture(name=screenshot_name, path=save_path, inverted=False)
        scope.SavePicture(name=screenshot_name, path=save_path, inverted=True)
        print("   ✓ Screenshots saved (normal + inverted)\n")
 
        # ── 8. Stabilisation hold ────────────────────────────────
        print("10. Holding at target voltage for 2 s...")
        time.sleep(2)
        print("    ✓ Hold complete\n")
 

        # ── 9. Close oscilloscope ─────────────
        print("14. Closing oscilloscope...")
        scope.close_oscilloscope()
        print("    ✓ Oscilloscope closed\n")
 
    except Exception as e:
        print(f"\n❌ Error: {e}\n")
        import traceback
        traceback.print_exc()
 
    finally:
        print("="*60)
        print("  Test SDS2104X+ completed")
        print("="*60 + "\n")
