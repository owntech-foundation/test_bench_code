import time
import pylab as pl 
import struct 
import gc
import os
import pyvisa as visa
from pyvisa import constants
from pyvisa.resources.serial import SerialInstrument
import sys
import time
import math
from datetime import datetime
import matplotlib.pyplot as plt



# Global variables 
# (Modify the following global variables according to the model). 
# --------------------------------------------------------- 
#SDS_RSC = "USB0::0xF4EC::0x1011::SDS2PEEC6R0224::INSTR"

#CHANNEL = "C1" 
HORI_NUM = 10 
tdiv_enum = [200e-12,500e-12, 1e-9, 2e-9, 5e-9, 10e-9, 20e-9, 50e-9, 100e-9, 200e-9, 500e-9, 1e-6, 2e-6, 5e-6, 10e-6, 20e-6, 50e-6, 100e-6, 200e-6, 500e-6,              1e-3, 2e-3, 5e-3, 10e-3, 20e-3, 50e-3, 100e-3, 200e-3, 500e-3, 1, 2, 5, 10, 20, 50, 100, 200, 500, 1000] 



def ExportResultToCSV(String, name, path):
    file_name= f"csv-{name}.csv"
    print(file_name)
    f = open(os.path.join(path, file_name), 'w')
    f.write(String) #Give your csv text here.
    ## Python will convert \n to os.linesep
    f.close()


def PlotValues(data):
    x=data.split(",")
    dataFormatted=[float(i) for i in x]
    plt.plot(dataFormatted)
    plt.ylabel('current')
    #plt.show()


def ConfigTrigger(scope):
    scope.write('TRIG:TYPE  EDGE ') # Edge
    scope.write(':TRIGger:EDGE:SLOPe  RISing') # Rising Edge
    #scope.write(':TRIGger:EDGE:HOLDoff  TIME') #HOLDoff with TIME
    #scope.write(':TRIGger:EDGE:HLDTime  50E-03') # HOLDoff TIME 50ms
    #scope.write(':TRIGger:EDGE:SOURce  C1') #Trigger Source C1
    #scope.write(':TRIGger:EDGE:SOURce  EX') #Trigger Source External
    scope.write(':TRIGger:EDGE:SOURce  EX5') #Trigger Source External /5
    #scope.write(':TRIGger:EDGE:LEVel  0.00E-01') #Trigger Level 0V
    scope.write(':TRIGger:EDGE:LEVel  7.00E-01') #Trigger Level 700mV
    scope.write('TRIG:MODE  SINGle') # Single


def ConfigSequence(scope, nbFrames):
    scope.write(':ACQuire:SEQuence ON') #Segmented Memory ON
    #scope.write(':ACQuire:SEQuence:COUNt 200') # 200 Sequential Segments
    scope.write(f':ACQuire:SEQuence:COUNt {nbFrames}')  # 200 Sequential Segments


def ConfigDisplay(scope):
    #scope.write(':TIMebase:SCALe  5.00E-06') #Timebase 5us / div
    scope.write(':TIMebase:SCALe  2.00E-06') #Timebase 2us / div


def ConfigMeasure(scope):
    scope.write(':MEASure ON')
    scope.write(':MEASure:MODE ADVanced')
    scope.write(':MEASure:ADVanced:STYLe M1')


def HistoryMode(scope):
    scope.write(':HISTORy ON')
    scope.write(':HISTORy:INTERval 200.00E-03')  # 200 ms time interval for playing history
    scope.write(':HISTORy:PLAy FORWards')  # PLay automatically all frames


def SetFrame(scope, num: int):
    scope.write(f':HISTORy:FRAMe {num}')


def NewMeasure(scope, num: int, measure: dict):
    type = measure.get('type')
    source = measure.get('channel')
    scope.write(f':MEASure:ADVanced:P{num} ON')
    scope.write(f':MEASure:ADVanced:P{num}:SOURce1 C{source}')
    scope.write(f':MEASure:ADVanced:P{num}:TYPE {type}')
    print(f"Add Measure {num} on Ch{source} : {type}")


def GetMeasure(scope, num: int):
    if not 'ON' in scope.query(f':MEASure:ADVanced:P{num}?'):
        print(f'Measure {num} is not set')
        return 0
    val_str = scope.query(f':MEASure:ADVanced:P{num}:VALue?').strip()
    print(f'Get measure {num}: {val_str}')
    if '****' in val_str:
        return None
    return eval(val_str)


def SavePicture(scope, name: str, path: str = "", inverted: bool = False):
    # Make sure that the drive specified is available on your computer
    file_name = f"scope{'-Inverted-' if inverted else ''}{name}.bmp"
    scope.chunk_size = 20 * 1024 * 1024  #default value is 20*1024(20k bytes)
    #scope.write("SCDP")
    scope.write(f"PRIN? BMP{',INVerted' if inverted else ''}")  # BMP
    #scope.write("PRIN? PNG")
    result_str = scope.read_raw()
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
def ReadHistory(scope, nbFrames, SaveBitmap, SaveData, delay):
    HistoryMode(scope)
    #Must wait here !!!! otherwise useless
    for frame in range(1, nbFrames+1, 1):
        SetFrame(scope, frame)
        time.sleep(delay)
        #scope.write(':SYSTem:MENU OFF')
        #time.sleep(delay) DOES NOT WORK
        frameName = f'Data{frame}'
        if SaveBitmap:
            SavePicture(scope, frameName)
            SavePicture(scope, frameName, inverted=True)
            # time.sleep(delay)
        if SaveData:
            SaveDataOscillo(scope, 'C1', frameName)
            #pl.figure(1)
            SaveDataOscillo(scope, 'C2', frameName)
            #pl.figure(2)
            SaveDataOscillo(scope, 'C3', frameName)
            #pl.figure(3)
            SaveDataOscillo(scope, 'C4', frameName)
            #pl.figure(4)
            #pl.show()
    



# ========================================================= 
# main_desc:Analyzing waveform parameters from data blocks 
# ========================================================= 
def main_desc(recv): 
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
    tdiv = tdiv_enum[tdiv_index] 
    return vdiv, offset, interval, delay, tdiv, code, adc_bit,data_bytes 
 
# ========================================================= 
# Main program: 
# ========================================================= 
def SaveDataOscillo(sds, channel: str,  name: str, path: str = ""):
    #_rm = visa.ResourceManager() 
    #sds = _rm.open_resource(smu) 
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
    vdiv, ofst, interval, trdl, tdiv, vcode_per, adc_bit,data_bytes = main_desc(recv) 
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
        time_data = - (float(tdiv) * HORI_NUM / 2) + idx * interval + float(trdl) 
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
    ExportResultToCSV(str(time_value), f'{channel}-{name}-timeX',path)
    ExportResultToCSV(str(volt_value), f'{channel}-{name}-valueY',path)
    print(f'Channel: {channel} - Frame / Name: {name}')
    del recv_all,time_value,volt_value,recv,convert_data,recv_rtn


if __name__ == '__main__':
    rm = visa.ResourceManager()
    print(rm.list_resources())
    scope = rm.open_resource('USB0::0xF4EC::0x1011::SDS2PDDX6R0968::INSTR', query_delay=0.5, timeout=6000)
    print(scope.query('*IDN?'))

    time.sleep(0.5)

    scope.close()
