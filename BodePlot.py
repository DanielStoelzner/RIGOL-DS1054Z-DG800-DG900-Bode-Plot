import cmath
import pyvisa as visa
import time
import numpy as np
import matplotlib.pyplot as plt
import math
from ds1054z import DS1054Z
import scipy
from scipy.interpolate import make_interp_spline
from scipy.interpolate import PchipInterpolator

config = open('config.txt')

freq_start = float(config.readline().split(',')[1])
freq_end = float(config.readline().split(',')[1])
if freq_start < 0 or freq_end < 0:
	print('ERROR. Frequency must be positive')
	print('Please press Enter to exit')
	input()
	exit(1)
if freq_start > freq_end:
	print('ERROR. Start Frequency must be less than End Frequency')
	print('Please press Enter to exit')
	input()
	exit(1)

freq_steps = int(config.readline().split(',')[1])
if freq_steps <= 0:
	print('ERROR. Frequency steps must be greater than zero')
	print('Please press Enter to exit')
	input()
	exit(1)
	
wave_v_max = float(config.readline().split(',')[1])
if wave_v_max <= 0:
	print('ERROR. Max Voltage must be greater than zero')
	print('Please press Enter to exit')
	input()
	exit(1)

sweep = config.readline().split(',')[1]
sweep = sweep[:-1]
if sweep != 'log' and sweep != 'linear':
	print("ERROR. Sweep type must be either 'log' or 'linear'")
	print('Please press Enter to exit')
	input()
	exit(1)

scale = config.readline().split(',')[1]
scale = scale[:-1]
if scale != 'db' and scale != 'v' and scale != 'both':
	print("ERROR. Scale must be either 'db', 'v' or 'both'")
	print('Please press Enter to exit')
	input()
	exit(1)

instrument = config.readline().split(',')[1]
instrument = instrument[:-1]

instrument2 = config.readline().split(',')[1]
instrument2 = instrument2[:-1]

print("-"*32)
print("Configuration:")
print("Start Frequency: " + str(freq_start))
print("End Frequency: " + str(freq_end))
print("Frequency Steps: " + str(freq_steps))
print("Max Voltage: " + str(wave_v_max))
print("Sweep Type: " + str(sweep))
print("Scale: " + scale)
print("Scope ID: " + instrument)
print("AWG ID: " + instrument2)
print("-"*32)
print(" ")

rm = visa.ResourceManager()

try:
	try:
		scope = DS1054Z(instrument)
	except:
		print("Scope: not found")
		raise Exception() 
		
	print ("Scope: " + scope.idn)

	scope.write(":MEASure:CLEar ALL")
	scope.write(":MEASure:STATistic:DISPlay 1")
	scope.write(":MEASure:ITEM VPP,CHANnel1")
	scope.write(":MEASure:ITEM VPP,CHANnel2")
	scope.write(":MEASure:ITEM VMID,CHANnel1")
	scope.write(":MEASure:ITEM VMID,CHANnel2")
	try:
		awg = rm.open_resource(instrument2)
	except:
		print("AWG:   not found")
		raise Exception()

	print ("AWG: " + awg.query("*IDN?"))
	
except:
	print('Please press Enter to exit')
	input()
	exit(1)
	
awg.write(':SOURce1:FUNC SINusoid')
awg.write(':SOURce1:FREQ '+str(freq_start))
awg.write(':SOUR1:VOLTage:HIGH '+str(wave_v_max/2))
awg.write(':SOUR1:VOLTage:LOW -'+str(wave_v_max/2))
awg.write(":OUTPut1:IMP INF")
awg.write(':OUTPut1 ON')

ch1_vpp      = np.zeros(freq_steps)
ch2_vpp      = np.zeros(freq_steps)
db           = np.zeros(freq_steps)
freq_values  = np.zeros(freq_steps)
phase_values = np.zeros(freq_steps)
freqs        = np.zeros(freq_steps)

if sweep == 'log':
	freqs = np.logspace(np.log10(freq_start), np.log10(freq_end), num=freq_steps)
else:
	freqs = np.linspace(freq_start, freq_end, num=freq_steps)

scope.write(":ACQuire:TYPE AVERages")
scope.write(":ACQuire:AVERages 16")
scope.write(":CHANnel1:VERNier 1")
scope.write(":CHANnel2:VERNier 1")
scope.write(":CHANnel1:BWLimit OFF")
scope.write(":CHANnel2:BWLimit OFF")
scope.write(":CHANnel2:COUPling AC")
scope.write(":CHANnel2:COUPling AC")
scope.write(":TRIGger:EDGe:SLOPe POSitive")
scope.write(":TRIGger:EDGe:LEVel 0")

def scope_reset():
	scope.write(":TIMebase:MAIN:SCAle " + str(1/(8*freq_start)))
	scope.write(":CHANnel1:SCALe 5")
	scope.write(":CHANnel2:SCALe 5")
	scope.write(":CHANnel1:OFFSet 0")
	scope.write(":CHANnel2:OFFSet 0")

scope_reset()

for x in range(2):
	scope.write(":DISPlay:CLEar")
	scope.write(":MEASure:STATistic:RESet")
	time.sleep(1)
	scope.write(":CHANnel1:OFFSet "+str(float(scope.query("MEASure:STATistic:ITEM? AVERages,VMID,CHANnel1"))*-1))
	time.sleep(.3)
	scope.write(":CHANnel2:OFFSet "+str(float(scope.query("MEASure:STATistic:ITEM? AVERages,VMID,CHANnel2"))*-1))
	time.sleep(.3)
	scope.write(":CHANnel1:SCALe "+str(float(scope.query("MEASure:STATistic:ITEM? AVERages,VPP,CHANnel1")) / 7))
	time.sleep(.3)
	scope.write(":CHANnel2:SCALe "+str(float(scope.query("MEASure:STATistic:ITEM? AVERages,VPP,CHANnel2")) / 7))

time.sleep(.3)
scope.write(":MEASure:SETup:PSA CHANnel1")
scope.write(":MEASure:STATistic:ITEM RPHase")
scope.write(":MEASure:STATistic:RESet")

for i in range(freq_steps):
	scope.write("TIMebase:MAIN:SCAle "+ str(1/(8*freqs[i])))
	awg.write(':SOUR1:FREQ '+str(freqs[i]))
	scope.write(":DISPlay:CLEar")	
	scope.write(":MEASure:STATistic:RESet")
	time.sleep(1.5)
	ch1_vpp[i] = scope.query("MEASure:STATistic:ITEM? AVERages,VPP,CHANnel1")
	ch2_vpp[i] = scope.query("MEASure:STATistic:ITEM? AVERages,VPP,CHANnel2")
	phase_values[i] = scope.query("MEASure:STATistic:ITEM? AVERages,RPHase")
	db[i] = 20*np.log10(ch2_vpp[i]/ch1_vpp[i])
	print (str(i+1) + '/' + str(freq_steps) + ' ' + f'{round(freqs[i],2):,}' + 'Hz ' + str(round(phase_values[i],2)) + '° ' + str(round(db[i],2)) + 'dB')
	scope.set_channel_scale(2, ch2_vpp[i] / 7)

print("-"*32)

def find_nearest(array, value):
	array = np.asarray(array)
	idx = (np.abs(array - value)).argmin()
	return idx

if scale == 'db' or scale == 'both':
	fig_db = plt.figure('dB Bode Plot')
	plt.plot(freqs,db,alpha=0.75)

	yhat = scipy.signal.savgol_filter(db, 5, 3)

	interp_obj = PchipInterpolator(freqs, yhat)
	new_x_vals = np.linspace(np.log10(freqs.min()), np.log10(freqs.max()), 50)
	new_x_vals = np.power(10, new_x_vals)
	new_y_vals = interp_obj(new_x_vals)
	plt.plot(new_x_vals, new_y_vals, "--", color="red", label="Smoothed data")

	freq_cutoff = new_x_vals[find_nearest(new_y_vals, value=-3.01)]

	plt.axhline(-3.0, color = 'orchid', linestyle = ':', label = '-3dB')
	plt.axvline(freq_cutoff, color = 'orange', linestyle = ':', label = 'Cutoff Frequency (~ ' + str(round(freq_cutoff, 2)) + "Hz)")
	plt.xlabel('f')
	plt.ylabel('dB')
	plt.title('dB Bode Plot')
	plt.grid()
	plt.xscale(sweep)
	plt.legend()
	plt.tight_layout()

if scale == 'v' or scale == 'both':
	fig_db = plt.figure('V Bode Plot')
	plt.plot(freqs,ch2_vpp,alpha=0.75)

	yhat = scipy.signal.savgol_filter(ch2_vpp, 5, 3)

	interp_obj = PchipInterpolator(freqs, ch2_vpp)
	new_x_vals = np.linspace(np.log10(freqs.min()), np.log10(freqs.max()), 50)
	new_x_vals = np.power(10, new_x_vals)
	new_y_vals = interp_obj(new_x_vals)
	plt.plot(new_x_vals, new_y_vals, "--", color="red", label="Smoothed data")
	
	ch1_vpp_3db = np.average(ch1_vpp) * 0.707
	freq_cutoff = new_x_vals[find_nearest(new_y_vals, value=ch1_vpp_3db)]
	
	plt.axhline(ch1_vpp_3db, color = 'orchid', linestyle = ':', label = '70.7%')
	plt.axvline(freq_cutoff, color = 'orange', linestyle = ':', label = 'Cutoff Frequency (~ ' + str(round(freq_cutoff, 2)) + "Hz)")

	plt.xlabel('f')
	plt.ylabel('Vout')
	plt.title('V Bode Plot')
	plt.grid()
	plt.xscale(sweep)
	plt.legend()
	plt.tight_layout()

fig_phase = plt.figure('Phase Bode Plot')
plt.plot(freqs, phase_values,alpha=0.75)

yhat = scipy.signal.savgol_filter(phase_values, 5, 3)

interp_obj = PchipInterpolator(freqs, yhat)
new_x_vals = np.linspace(np.log10(freqs.min()), np.log10(freqs.max()), 50)
new_x_vals = np.power(10, new_x_vals)
new_y_vals = interp_obj(new_x_vals)
plt.plot(new_x_vals, new_y_vals, "--", color="red", label="Smoothed data")

if scale == 'db' or scale == 'both':
	plt.axvline(freq_cutoff, color = 'orange', linestyle = ':', label = 'Cutoff Frequency (~ ' + f'{round(freq_cutoff,2):,}' + "Hz)")
plt.xlabel('f')
plt.ylabel('°')
plt.title('Phase Bode Plot')
plt.grid()
plt.xscale(sweep)
plt.legend()
plt.tight_layout()

awg.write(':OUTPut1 OFF')
scope_reset()
scope.close()
awg.close()

plt.show()