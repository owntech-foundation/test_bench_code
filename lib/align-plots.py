import numpy as np
import matplotlib.pyplot as plt


# DMM configuration
nplc = 1
tstep = (1/50)*nplc
nsamples = 1000
tmes = tstep*nsamples

# Power supply configuration
voltage_setpoint = 50
voltage_threshold, voltage_hyst = 46, 1

# Load data
#yvoltage = np.genfromtxt('data/csv-15_31_32-19_11_2024Voltage.csv', delimiter=',')
#ycurrent = np.genfromtxt('data/csv-15_31_31-19_11_2024Current.csv', delimiter=',')
yvoltage = np.genfromtxt('data/csv-11_53_15-10_12_2024Voltage.csv', delimiter=',')
ycurrent = np.genfromtxt('data/csv-11_53_14-10_12_2024Current.csv', delimiter=',')
print(f"Loaded {len(ycurrent)}, {len(ycurrent)} points")

def plot_dualy(data1, data2):
    fig, ax1 = plt.subplots(figsize=(5, 3))

    ax2 = ax1.twinx()
    ax1.plot(data1, color='g')
    ax2.plot(data2, color='b')

    ax1.set_xlabel('X data')
    ax1.set_ylabel('Voltage [V]', color='g')
    ax2.set_ylabel('Current [A]', color='b')
    ax1.set_xlim(0, len(data1))

# First let's take alook at the waveforms as is 
plot_dualy(yvoltage, ycurrent)
plt.figure(1)

# Detect rising edge from threshold
def rising_edge(data, thresh: float):
    sign = data >= thresh
    pos = np.where(np.convolve(sign, [1, -1]) == 1)
    return pos[0][0]

def alignData(data1, data2):
    # First, only process on the part with stable voltage
    # -> Identify lower and higher index
    lbound, hbound = 0, 0
    for n in range(len(data1)):
        if (lbound == 0):
            if (data1[n] > (voltage_threshold+voltage_hyst)):
                lbound = n+125 # make sure the pulsed region is excluded
                n += 10
        elif (hbound == 0):
            if (data1[n] < (voltage_threshold-voltage_hyst)):
                hbound = n-50
        n += 1

    dvoltage = np.gradient(data1[lbound:hbound], tstep)
    dcurrent = np.gradient(data2[lbound:hbound], tstep)
    n_dvmax = rising_edge(-dvoltage, max(-dvoltage)*0.8)
    n_dimax = rising_edge(dcurrent, max(dcurrent)*0.8)
    offset = n_dvmax - n_dimax

    return lbound, hbound, offset

lbound, hbound, offset = alignData(yvoltage, ycurrent)
print(f"Offset: {offset}")

plot_dualy(yvoltage[lbound+offset:hbound+offset], ycurrent[lbound:hbound])
plt.figure(2)
#plt.show()


ypower = yvoltage[lbound+offset:hbound+offset]*ycurrent[lbound:hbound]

#plt.figure(figsize=(5, 3))
plt.figure(3)
plt.plot(ypower)
plt.ylabel('Power [W]')
plt.xlabel('Sample')
plt.minorticks_on()
plt.grid()
plt.grid(which='minor', alpha=0.3)
plt.show()
