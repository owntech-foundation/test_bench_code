# N.Rouger // L.Leijnen
# version: Dec. 2024
# GPL3
import numpy as np
import matplotlib.pyplot as plt


def ReadXYfromcsv(Name):
    yvoltage = np.genfromtxt(Name+'valueY.csv', delimiter=',')
    xtime = np.genfromtxt(Name+'timeX.csv', delimiter=',')
    print(f"Loaded {len(xtime)}, {len(yvoltage)} points")
    return xtime,yvoltage

Frame='1'    
# Load data
time1,C1=ReadXYfromcsv('../ScreenShot/csv-C1-'+Frame+'Nico-')
plt.figure(1)
plt.plot(time1,C1)

time2,C2=ReadXYfromcsv('../ScreenShot/csv-C2-'+Frame+'Nico-')
plt.figure(2)
plt.plot(time2,C2,color='green')

##time3,C3=ReadXYfromcsv('../data/csv-C3-Data'+Frame+'-')
##plt.figure(3)
##plt.plot(time3,C3,color='red')
##
##time4,C4=ReadXYfromcsv('../data/csv-C4-Data'+Frame+'-')
##plt.figure(4)
##plt.plot(time4,C4)

plt.show()
